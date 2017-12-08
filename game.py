# -*- coding: utf-8 -*-
import pymysql
import configparser
import random
import re
import os
import urllib.parse
import urllib.request

class Game:
	def __init__(self, platform, userid):
		self.platform = platform
		self.userid = userid
		config = configparser.ConfigParser()
		configpath = os.path.dirname(os.path.realpath(__file__))+'/config.ini'
		config.read(configpath)
		self.guesslenlimit = int(config.get('global', 'guesslenlimit'))
		self.db = pymysql.connect(host=config.get('database', 'host'),
								  user=config.get('database', 'user'),
								  passwd=config.get('database', 'passwd'),
								  db=config.get('database', 'db'),
								  charset=config.get('database', 'charset'))
		self.cur = self.db.cursor()
		self.cur.execute("""SELECT `guess`, `word`, `meaning` FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
			(self.platform, self.userid) )
		rows = self.cur.fetchall()
		if len(rows) == 0:
			self.isstart = False
		else :
			from zhconversion import ZhConversion
			self.oldguess = rows[0][0]
			self.word = rows[0][1]
			self.wordhans = ZhConversion(self.word).text()
			self.meaning = rows[0][2]
			self.isstart = True

	def start(self, length = 0):
		if self.isstart:
			return "遊戲已經開始了\n「"+self.oldguess+"」的意思是：\n"+self.meaning
		try:
			length = int(length)
			if length < 2:
				length = random.randint(2, 10)
			if length > 10:
				length = 10
		except Exception as e:
			length = random.randint(2, 10)
		if length == 10:
			self.cur.execute("""SELECT COUNT(*) FROM `dictionary` WHERE `length` >= 10""")
			count = self.cur.fetchall()[0][0]
			wordoffset = random.randint(0, count-1)
			self.cur.execute("""SELECT `word`, `meaning` FROM `dictionary` WHERE `length` >= 10 LIMIT %s,1""", (wordoffset))
		else :
			self.cur.execute("""SELECT COUNT(*) FROM `dictionary` WHERE `length` = %s""", (length))
			count = self.cur.fetchall()[0][0]
			wordoffset = random.randint(0, count-1)
			self.cur.execute("""SELECT `word`, `meaning` FROM `dictionary` WHERE `length` = %s LIMIT %s,1""", (length, wordoffset))
		row = self.cur.fetchall()[0]
		word = row[0]
		newguess = ""
		for i in range(len(word)):
			if word[i] in "，；":
				newguess += word[i]
			else :
				newguess += "？"
		meaning = row[1]
		meaning = meaning.replace(word, newguess)
		self.cur.execute("""INSERT INTO `guess` (`platform`, `userid`, `guess`, `word`, `meaning`) VALUES (%s, %s, %s, %s, %s)""",
			(self.platform, self.userid, newguess, word, meaning) )
		self.db.commit()
		self.log("Q:"+word)
		self.word = word
		self.meaning = meaning
		self.oldguess = newguess
		self.isstart = True
		return newguess+" 的意思是：\n"+meaning

	def guess(self, guess):
		guess = guess.replace("\n", "").strip()
		if len(guess) > self.guesslenlimit:
			return "偵測到作弊行為，請勿破壞遊戲體驗，此次猜測無效"
		newguess = ""
		for i in range(len(self.word)):
			if self.oldguess[i] != "？":
				newguess += self.oldguess[i]
			elif self.word[i] in guess or self.wordhans[i] in guess:
				newguess += self.word[i]
			else :
				newguess += "？"
		if newguess == self.word:
			response = "恭喜猜中了，答案是「"+self.word+"」"
			self.cur.execute("""DELETE FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
				(self.platform, self.userid) )
			self.db.commit()
			self.isstart = False
		else :
			self.meaning = self.meaning.replace(self.oldguess, newguess)
			if self.oldguess != newguess:
				response = "快要猜中囉，「"+newguess+"」的意思是：\n"+self.meaning
				self.cur.execute("""UPDATE `guess` SET `guess` = %s, `meaning` = %s WHERE `platform` = %s AND `userid` = %s""",
					(newguess, self.meaning, self.platform, self.userid) )
				self.db.commit()
			else :
				response = "猜錯囉，「"+newguess+"」的意思是：\n"+self.meaning
		return response

	def tip(self):
		unknown = []
		for i in range(len(self.oldguess)):
			if self.oldguess[i] == "？":
				unknown.append(i)
		if len(unknown) < 2:
			return "沒有更多提示了，「"+self.oldguess+"」的意思是：\n"+self.meaning
		else :
			index = unknown[random.randint(0, len(unknown)-1)]
			newguess = self.oldguess[:index]+self.word[index]+self.oldguess[index+1:]
			self.guess(newguess)
			return "使用提示，「"+newguess+"」的意思是：\n"+self.meaning

	def giveup(self):
		self.cur.execute("""SELECT `guess`, `word`, `meaning` FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
			(self.platform, self.userid) )
		rows = self.cur.fetchall()
		self.cur.execute("""DELETE FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
			(self.platform, self.userid) )
		self.db.commit()
		self.isstart = False
		return "答案是「"+self.word+"」"

	def log(self, message):
		self.cur.execute("""INSERT INTO `log` (`platform`, `userid`, `message`) VALUES (%s, %s, %s)""",
			(self.platform, self.userid, str(message)) )
		self.db.commit()

	def __exit__(self):
		self.db.close()

class TelegramGame(Game):
	def __init__(self, userid):
		super(TelegramGame, self).__init__("tg", userid)
		config = configparser.ConfigParser()
		configpath = os.path.dirname(os.path.realpath(__file__))+'/config.ini'
		config.read(configpath)
		self.token = config.get('telegram', 'token')
		self.botid = int(config.get('telegram', 'botid'))
		if int(userid) > 0:
			self.cmdpostfix = ""
		else :
			self.cmdpostfix = "@"+config.get('telegram', 'botname')
	
	def response(self, message):
		message += " "

		m = re.match(r"/start"+self.cmdpostfix+" (.+)?", message)
		if m != None:
			length = m.group(1)
			response = super(TelegramGame, self).start(length)+"\n"
			if self.userid < 0:
				response += "回答需Reply，"
			response += "提示請輸入 /tip ，放棄請輸入 /giveup"
			return response

		if self.isstart:
			m = re.match(r"/tip"+self.cmdpostfix+" ", message)
			if m != None:
				return super(TelegramGame, self).tip()

			m = re.match(r"/giveup"+self.cmdpostfix+" ", message)
			if m != None:
				return super(TelegramGame, self).giveup()+"\n開始新遊戲請輸入 /start"+self.cmdpostfix+"\n或 /start"+self.cmdpostfix+" n 限定答案n個字"

		m = re.match(r"/[^ ]+ ", message)
		if m != None:
			return ""

		if self.isstart:
			response = super(TelegramGame, self).guess(message)
			if not self.isstart:
				response += "\n開始新遊戲請輸入 /start"+self.cmdpostfix+"\n或 /start"+self.cmdpostfix+" n 限定答案n個字"
			return response

		return ""

	def sendmessage(self, message, reply_to_message_id):
		self.log("send:"+message)
		try:
			url = "https://api.telegram.org/bot"+self.token+"/sendMessage?chat_id="+str(self.userid)+"&reply_to_message_id="+str(reply_to_message_id)+"&text="+urllib.parse.quote_plus(message.encode())
			urllib.request.urlopen(url)
		except urllib.error.HTTPError as e:
			self.log("error:"+str(e.code)+" "+str(e.hdrs))

class LineGame(Game):
	def __init__(self, userid, replytoken):
		from linebot import LineBotApi
		super(LineGame, self).__init__("line", userid)
		config = configparser.ConfigParser()
		configpath = os.path.dirname(os.path.realpath(__file__))+'/config.ini'
		config.read(configpath)
		self.secret = config.get('line', 'secret')
		self.token = config.get('line', 'token')
		self.replytoken = replytoken
		self.line_bot_api = LineBotApi(self.token)

	def response(self, message):
		if self.isstart:
			response = super(LineGame, self).guess(message)
			if self.isstart and message.strip() == "放棄":
				response = super(LineGame, self).giveup()+"\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
			elif self.isstart and message.strip() == "提示":
				response = super(LineGame, self).tip()
			elif not self.isstart:
				response += "\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
		else :
			response = super(LineGame, self).start(message)+"\n\n可輸入「提示」獲取提示，放棄遊戲請輸入「放棄」"
		return response

	def sendmessage(self, message):
		from linebot.models import TextSendMessage
		self.log(message)
		self.line_bot_api.reply_message(
			self.replytoken,
			TextSendMessage(text=message))

class FacebookGame(Game):
	def __init__(self, userid):
		super(FacebookGame, self).__init__("fb", userid)
		config = configparser.ConfigParser()
		configpath = os.path.dirname(os.path.realpath(__file__))+'/config.ini'
		config.read(configpath)
		self.token = config.get('facebook', 'token')

	def response(self, message):
		self.log(message)
		if self.isstart:
			response = super(FacebookGame, self).guess(message)
			if self.isstart and message.strip() == "放棄":
				response = super(FacebookGame, self).giveup()+"\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
			elif self.isstart and message.strip() == "提示":
				response = super(FacebookGame, self).tip()
			elif not self.isstart:
				response += "\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
		else :
			response = super(FacebookGame, self).start(message)+"\n\n可輸入「提示」獲取提示，放棄遊戲請輸入「放棄」"
		return response

	def sendmessage(self, message):
		self.log(message)
		url = "https://graph.facebook.com/v2.7/me/messages"
		print(url)
		data = {'access_token': self.token,
				'recipient': {"id": self.userid},
				'message': {"text": message}
				}
		print(data)
		req = urllib.request.Request(url, urllib.parse.urlencode(data).encode())
		print(req)
		try:
			res = urllib.request.urlopen(req)
		except urllib.error.HTTPError as e:
			raise Exception(str(e.hdrs))

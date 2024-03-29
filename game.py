# -*- coding: utf-8 -*-
import pymysql
import configparser
import random
import re
import os
import json
import subprocess
import urllib.parse
import urllib.request


class Game:
    def __init__(self, platform, userid):
        self.platform = platform
        self.userid = userid
        config = configparser.ConfigParser()
        configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
        config.read(configpath)
        self.db = pymysql.connect(host=config.get('database', 'host'),
                                  user=config.get('database', 'user'),
                                  passwd=config.get('database', 'passwd'),
                                  db=config.get('database', 'db'),
                                  charset=config.get('database', 'charset'))
        self.cur = self.db.cursor()
        self.cur.execute("""SELECT `guess`, `word`, `meaning` FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
                         (self.platform, self.userid))
        rows = self.cur.fetchall()
        if len(rows) == 0:
            self.isstart = False
        else:
            from zhconversion import ZhConversion
            self.oldguess = rows[0][0]
            self.word = rows[0][1]
            self.wordhans = ZhConversion(self.word).text()
            wordlen = len(self.word)
            if wordlen <= 3:
                self.guesslenlimit = 10
            elif wordlen <= 5:
                self.guesslenlimit = 15
            elif wordlen <= 10:
                self.guesslenlimit = 20
            elif wordlen <= 16:
                self.guesslenlimit = 25
            else:
                self.guesslenlimit = int(wordlen * 1.5)
            self.meaning = rows[0][2]
            self.isstart = True

    def start(self, length=0):
        if self.isstart:
            return "遊戲已經開始了\n「" + self.oldguess + "」的意思是：\n" + self.meaning
        try:
            length = int(length)
            if length < 2:
                length = random.randint(2, 10)
            if length > 10 and length != 64:
                length = 10
        except Exception as e:
            length = random.randint(2, 10)
        if length == 10:
            self.cur.execute("""SELECT COUNT(*) FROM `dictionary` WHERE `length` >= 10""")
            count = self.cur.fetchall()[0][0]
            wordoffset = random.randint(0, count - 1)
            self.cur.execute(
                """SELECT `word`, `meaning` FROM `dictionary` WHERE `length` >= 10 LIMIT %s,1""", (wordoffset))
        else:
            self.cur.execute("""SELECT COUNT(*) FROM `dictionary` WHERE `length` = %s""", (length))
            count = self.cur.fetchall()[0][0]
            wordoffset = random.randint(0, count - 1)
            self.cur.execute(
                """SELECT `word`, `meaning` FROM `dictionary` WHERE `length` = %s LIMIT %s,1""", (length, wordoffset))
        row = self.cur.fetchall()[0]
        word = row[0]
        newguess = ""
        for i in range(len(word)):
            if word[i] in "，。、；「」～〜★˙ ":
                newguess += word[i]
            else:
                newguess += "？"
        meaning = row[1]
        meaning = meaning.replace(word, newguess)
        meaning = re.sub(r"&(.+?\.gif);", r"�( http://dict.revised.moe.edu.tw/cbdic/cfont/\1 )", meaning)
        self.cur.execute("""INSERT INTO `guess` (`platform`, `userid`, `guess`, `word`, `meaning`) VALUES (%s, %s, %s, %s, %s)""",
                         (self.platform, self.userid, newguess, word, meaning))
        self.db.commit()
        self.log("Q:" + word)
        self.word = word
        self.meaning = meaning
        self.oldguess = newguess
        self.isstart = True
        return "「" + newguess + "」的意思是：\n" + meaning

    def guess(self, guess):
        guess = guess.replace("\n", "").strip()
        self.correct = 0
        if len(guess) > self.guesslenlimit:
            return "偵測到作弊行為，請勿破壞遊戲體驗，此次猜測無效"
        newguess = ""
        for i in range(len(self.word)):
            if self.oldguess[i] != "？":
                newguess += self.oldguess[i]
            elif self.word[i] in guess or self.wordhans[i] in guess:
                newguess += self.word[i]
                self.correct += 1
            else:
                newguess += "？"
        self.meaning = self.meaning.replace(self.oldguess, newguess)
        if newguess == self.word:
            response = "恭喜猜中了，答案是「" + self.word + "」"
            self.cur.execute("""DELETE FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
                             (self.platform, self.userid))
            self.db.commit()
            self.isstart = False
        else:
            if self.oldguess != newguess:
                response = "快要猜中囉，「" + newguess + "」的意思是：\n" + self.meaning
                self.cur.execute("""UPDATE `guess` SET `guess` = %s, `meaning` = %s WHERE `platform` = %s AND `userid` = %s""",
                                 (newguess, self.meaning, self.platform, self.userid))
                self.db.commit()
            else:
                response = "猜錯囉，「" + newguess + "」的意思是：\n" + self.meaning
        self.oldguess = newguess
        return response

    def hint(self):
        unknown = []
        unknownchar = []
        for i in range(len(self.oldguess)):
            if self.oldguess[i] == "？" and self.word[i] not in unknownchar:
                unknown.append(i)
                unknownchar.append(self.word[i])
        if len(unknown) < 2:
            return "沒有更多提示了，「" + self.oldguess + "」的意思是：\n" + self.meaning
        else:
            index = unknown[random.randint(0, len(unknown) - 1)]
            newguess = self.oldguess[:index] + self.word[index] + self.oldguess[index + 1:]
            self.guess(newguess)
            return "使用提示，「" + self.oldguess + "」的意思是：\n" + self.meaning

    def giveup(self):
        self.cur.execute("""SELECT `guess`, `word`, `meaning` FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
                         (self.platform, self.userid))
        rows = self.cur.fetchall()
        self.cur.execute("""DELETE FROM `guess` WHERE `platform` = %s AND `userid` = %s""",
                         (self.platform, self.userid))
        self.db.commit()
        self.isstart = False
        return "答案是「" + self.word + "」"

    def log(self, message):
        self.cur.execute("""INSERT INTO `log` (`platform`, `userid`, `message`) VALUES (%s, %s, %s)""",
                         (self.platform, self.userid, str(message)))
        self.db.commit()

    def __del__(self):
        self.db.close()


class TelegramGame(Game):
    def __init__(self, userid, fromid, date):
        super(TelegramGame, self).__init__("tg", userid)
        self.fromid = fromid
        self.date = date
        config = configparser.ConfigParser()
        configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
        config.read(configpath)
        self.token = config.get('telegram', 'token')
        self.botid = config.getint('telegram', 'botid')
        self.guesstimes = config.getint('telegram', 'guesstimes')
        self.hinttimes = config.getint('telegram', 'hinttimes')
        self.hintduration = config.getint('telegram', 'hintduration')
        self.giveuptimes = config.getint('telegram', 'giveuptimes')
        self.giveupduration = config.getint('telegram', 'giveupduration')
        self.isdelusermsg = config.getboolean('telegram', 'isdelusermsg')
        self.isdelbotmsg = config.getboolean('telegram', 'isdelbotmsg')
        self.isdelanswer = config.getboolean('telegram', 'isdelanswer')
        if int(userid) > 0:
            self.cmdpostfix = ""
        else:
            self.cmdpostfix = "@" + config.get('telegram', 'botname')
        if userid != fromid:
            configpath = os.path.dirname(os.path.realpath(__file__)) + '/config/' + str(userid) + '.ini'
            if os.path.isfile(configpath):
                config = configparser.ConfigParser()
                config.read(configpath)
                self.guesstimes = config.getint('limit', 'guesstimes', fallback=self.guesstimes)
                self.hinttimes = config.getint('limit', 'hinttimes', fallback=self.hinttimes)
                self.hintduration = config.getint('limit', 'hintduration', fallback=self.hintduration)
                self.giveuptimes = config.getint('limit', 'giveuptimes', fallback=self.giveuptimes)
                self.giveupduration = config.getint('limit', 'giveupduration', fallback=self.giveupduration)
                self.isdelusermsg = config.getboolean('limit', 'isdelusermsg', fallback=self.isdelusermsg)
                self.isdelbotmsg = config.getboolean('limit', 'isdelbotmsg', fallback=self.isdelbotmsg)
                self.isdelanswer = config.getboolean('limit', 'isdelanswer', fallback=self.isdelanswer)
            else:
                config = configparser.ConfigParser()
                config.read(configpath)
                config.add_section('limit')
                config.set('limit', 'guesstimes', str(self.guesstimes))
                config.set('limit', 'hinttimes', str(self.hinttimes))
                config.set('limit', 'hintduration', str(self.hintduration))
                config.set('limit', 'giveuptimes', str(self.giveuptimes))
                config.set('limit', 'giveupduration', str(self.giveupduration))
                config.set('limit', 'isdelusermsg', str(self.isdelusermsg))
                config.set('limit', 'isdelbotmsg', str(self.isdelbotmsg))
                config.set('limit', 'isdelanswer', str(self.isdelanswer))
                config.write(open(configpath, 'w'))
            self.isgroup = True
            self.botmsgaction = ""
            self.botmsgid = ""
        else:
            self.isgroup = False

    def isadmin(self):
        res = urllib.request.urlopen('https://api.telegram.org/bot' + self.token + '/getChatMember?chat_id='
                                     + str(self.userid) + '&user_id=' + str(self.fromid)).read().decode("utf8")
        res = json.loads(res)
        return res["result"]["status"] in ["creator", "administrator"]

    def isbotisadmin(self):
        res = urllib.request.urlopen('https://api.telegram.org/bot' + self.token + '/getChatMember?chat_id='
                                     + str(self.userid) + '&user_id=' + str(self.botid)).read().decode("utf8")
        res = json.loads(res)
        return (res["result"]["status"] == "administrator" and res["result"]["can_delete_messages"])

    def checklimit(self, type, date):
        self.cur.execute("""SELECT COUNT(*) FROM `tggrouplimit` WHERE `userid` = %s AND `fromid` = %s AND `type` = %s AND `date` > %s""",
                         (self.userid, self.fromid, type, date))
        return self.cur.fetchall()[0][0]

    def checkhint(self):
        hintduration = self.date - self.hintduration
        count = self.checklimit("hint", hintduration)
        return count < self.hinttimes

    def checkgiveup(self):
        giveupduration = self.date - self.giveupduration
        count = self.checklimit("giveup", giveupduration)
        return count < self.giveuptimes

    def addlimit(self, type):
        self.cur.execute("""INSERT INTO `tggrouplimit` (`userid`, `fromid`, `type`, `date`) VALUES (%s, %s, %s, %s)""",
                         (self.userid, self.fromid, type, self.date))

    def delfailguess(self):
        self.cur.execute("""DELETE FROM `tggrouplimit` WHERE `type` = 'failguess' AND `userid` = %s""",
                         (self.userid))

    def setconfig(self, type, value):
        configpath = os.path.dirname(os.path.realpath(__file__)) + '/config/' + str(self.userid) + '.ini'
        config = configparser.ConfigParser()
        config.read(configpath)
        config.set("limit", type, str(value))
        config.write(open(configpath, 'w'))

    def response(self, message):
        message += " "

        m = re.match(r"/start" + self.cmdpostfix + " (.+)?", message)
        if m != None:
            self.botmsgaction = "add"
            length = m.group(1)
            response = super(TelegramGame, self).start(length) + "\n"
            response = self.badchar(response)
            if self.userid < 0:
                response += "回答需Reply，"
            response += "提示請輸入 /hint ，放棄請輸入 /giveup"
            return response

        if self.isstart:
            m = re.match(r"/hint" + self.cmdpostfix + " ", message)
            if m != None:
                self.botmsgaction = "add"
                if not self.isgroup or self.checkhint():
                    if self.isgroup:
                        self.addlimit("hint")
                    return self.badchar(super(TelegramGame, self).hint())
                else:
                    return "你的提示使用次數已達上限，「" + self.oldguess + "」的意思是：\n" + self.badchar(self.meaning)

            m = re.match(r"/giveup" + self.cmdpostfix + " ", message)
            if m != None:
                if not self.isgroup or self.checkgiveup():
                    if self.isgroup:
                        self.addlimit("giveup")
                        self.botmsgaction = "del"
                    self.delfailguess()
                    response = super(TelegramGame, self).giveup()
                    response += "，意思是：\n" + self.badchar(self.meaning)
                    response += "\n開始新遊戲請輸入 /start" + self.cmdpostfix + "\n或 /start" + self.cmdpostfix + " n 限定答案n個字"
                    return response
                else:
                    self.botmsgaction = "add"
                    return "你的放棄使用次數已達上限，「" + self.oldguess + "」的意思是：\n" + self.meaning

        if self.isgroup:
            m = re.match(r"/guesslimit" + self.cmdpostfix + " ", message)
            if m != None:
                self.botmsgaction = "add"
                if not self.isadmin():
                    return "只有群組管理員可以更改此設定"
                m = re.match(r"/guesslimit" + self.cmdpostfix + " (\d+) ", message)
                if m != None:
                    if int(m.group(1)) < 1:
                        return "參數錯誤，至少要為 1"
                    if int(m.group(1)) > 10000:
                        return "參數太大囉"
                    self.setconfig("guesstimes", m.group(1))
                    return "已限制每人每局可以猜錯" + m.group(1) + "次"
                else:
                    return "命令使用方法： " + "/guesslimit" + self.cmdpostfix + " c 限制每人每局可以猜錯c次"

            m = re.match(r"/hintlimit" + self.cmdpostfix + " ", message)
            if m != None:
                self.botmsgaction = "add"
                if not self.isadmin():
                    return "只有群組管理員可以更改此設定"
                m = re.match(r"/hintlimit" + self.cmdpostfix + " (\d+) (\d+) ", message)
                if m != None:
                    if int(m.group(1)) < 0:
                        return "第一個參數錯誤，至少要為 0"
                    if int(m.group(1)) > 10000:
                        return "第一個參數太大囉"
                    if int(m.group(2)) < 1:
                        return "第二個參數錯誤，至少要為 1"
                    if int(m.group(2)) > 100000000:
                        return "第二個參數太大囉"
                    self.setconfig("hinttimes", m.group(1))
                    self.setconfig("hintduration", m.group(2))
                    return "已限制每人" + m.group(2) + "秒內最多可以使用提示" + m.group(1) + "次"
                else:
                    return "命令使用方法： " + "/hintlimit" + self.cmdpostfix + " c t 限制t秒內最多可以使用提示c次"

            m = re.match(r"/giveuplimit" + self.cmdpostfix + " ", message)
            if m != None:
                self.botmsgaction = "add"
                if not self.isadmin():
                    return "只有群組管理員可以更改此設定"
                m = re.match(r"/giveuplimit" + self.cmdpostfix + " (\d+) (\d+) ", message)
                if m != None:
                    if int(m.group(1)) < 0:
                        return "第一個參數錯誤，至少要為 0"
                    if int(m.group(1)) > 10000:
                        return "第一個參數太大囉"
                    if int(m.group(2)) < 1:
                        return "第二個參數錯誤，至少要為 1"
                    if int(m.group(2)) > 100000000:
                        return "第二個參數太大囉"
                    self.setconfig("giveuptimes", m.group(1))
                    self.setconfig("giveupduration", m.group(2))
                    return "已限制每人" + m.group(2) + "秒內最多可以使用放棄" + m.group(1) + "次"
                else:
                    return "命令使用方法： " + "/giveuplimit" + self.cmdpostfix + " c t 限制t秒內最多可以使用放棄c次"

            m = re.match(r"/delmsg" + self.cmdpostfix + " ", message)
            if m != None:
                self.botmsgaction = "add"
                if not self.isadmin():
                    return "只有群組管理員可以更改此設定"
                m = re.match(r"/delmsg" + self.cmdpostfix + " (\d) (\d) (\d)", message)
                if m != None:
                    response = ""
                    isdelusermsg = bool(int(m.group(1)))
                    if isdelusermsg and not self.isbotisadmin():
                        isdelusermsg = False
                        response += "機器人非管理員，無法刪除使用者訊息，請先給予刪除訊息權限\n"
                    isdelusermsg = str(isdelusermsg)
                    isdelbotmsg = str(bool(int(m.group(2))))
                    isdelanswer = str(bool(int(m.group(3))))
                    self.setconfig("isdelusermsg", isdelusermsg)
                    self.setconfig("isdelbotmsg", isdelbotmsg)
                    self.setconfig("isdelanswer", isdelanswer)
                    response += "已設定刪除使用者訊息：" + isdelusermsg + "；刪除機器人訊息：" + isdelbotmsg + "；刪除答案：" + isdelanswer
                    return response
                else:
                    return "命令使用方法： " + "/delmsg" + self.cmdpostfix + " u b a 設定是否刪除使用者、機器人、答案的訊息，是為1，否為0"

        m = re.match(r"/help" + self.cmdpostfix + " ", message)
        if m != None:
            response = "/start 開始遊戲\n" +\
                "/hint 提示\n" +\
                "/giveup 放棄遊戲\n"
            if self.isgroup:
                self.botmsgaction = "add"
                response += "/settings 查看規則\n" +\
                    "/guesslimit 設定猜測錯誤次數限制 (僅群管可用)\n" +\
                    "/hintlimit 設定提示次數限制 (僅群管可用)\n" +\
                    "/giveuplimit 設定放棄次數限制 (僅群管可用)\n" +\
                    "/delmsg 設定是否刪除使用者及機器人訊息 (僅群管可用)\n"
            return response

        m = re.match(r"/settings" + self.cmdpostfix + " ", message)
        if m != None:
            if self.isgroup:
                self.botmsgaction = "add"
                return "設定：\n" +\
                    "每人每局可以猜錯" + str(self.guesstimes) + "次\n" +\
                    ("每人" + str(self.hintduration) + "秒內可使用提示" + str(self.hinttimes) + "次\n" if self.hinttimes > 0 else "禁止使用提示\n") +\
                    ("每人" + str(self.giveupduration) + "秒內可使用放棄" + str(self.giveuptimes) + "次\n" if self.giveuptimes > 0 else "禁止使用放棄\n") +\
                    "刪除使用者訊息：" + str(self.isdelusermsg) + "；刪除機器人訊息：" + str(self.isdelbotmsg) + "；刪除答案訊息：" + str(self.isdelanswer) + "\n" +\
                    "使用 /help" + self.cmdpostfix + " 查看更改設定用指令"
            else:
                return "私訊模式中沒有可用設定"

        m = re.match(r"/search" + self.cmdpostfix + " ", message)
        if m != None:
            self.botmsgaction = "add"
            m = re.match(r"/search" + self.cmdpostfix + " (.+) ", message)
            if m != None:
                word = m.group(1)
                self.cur.execute("""SELECT `meaning` FROM `dictionary` WHERE `word` = %s""",
                                 (word))
                rows = self.cur.fetchall()
                if len(rows) == 0:
                    return "找不到「" + word + "」"
                else:
                    return "「" + word + "」的意思是：\n" + re.sub(r"&(.+?\.gif);", r"[�](http://dict.revised.moe.edu.tw/cbdic/cfont/\1)", rows[0][0])
            else:
                return "命令使用方法： " + "/search" + self.cmdpostfix + " word 搜尋word的意思"

        if message.startswith("/"):
            return ""

        if self.isstart:
            failguess = self.checklimit("failguess", 0)
            if self.isgroup and failguess >= self.guesstimes:
                return ""
            response = super(TelegramGame, self).guess(message)
            if not self.isstart:
                self.delfailguess()
                if self.isgroup:
                    self.botmsgaction = "del"
                response += "，意思是：\n" + self.meaning
                response += "\n開始新遊戲請輸入 /start" + self.cmdpostfix + "\n或 /start" + self.cmdpostfix + " n 限定答案n個字"
            else:
                self.botmsgaction = "add"
                if self.correct == 0:
                    self.addlimit("failguess")
                    if self.isgroup and failguess + 1 >= self.guesstimes:
                        response = response.replace("猜錯囉", "你猜錯太多次了，已失去本局遊戲資格")
                    else:
                        response = response.replace("猜錯囉", "猜錯" + str(failguess + 1) + "次囉")
            response = self.badchar(response)
            return response

        return ""

    def badchar(self, text):
        return re.sub(r"�\( (.+?) \)", r"[�](\1)", text)

    def sendmessage(self, message, reply_to_message_id):
        self.log("send " + str(self.userid) + " " + message)
        try:
            url = "https://api.telegram.org/bot" + self.token + "/sendMessage?chat_id=" + str(self.userid) + "&reply_to_message_id=" + str(
                reply_to_message_id) + "&parse_mode=Markdown&disable_web_page_preview=1&text=" + urllib.parse.quote_plus(message.encode())
            res = urllib.request.urlopen(url).read().decode("utf8")
            res = json.loads(res)
            if res["ok"]:
                self.botmsgid = res["result"]["message_id"]
        except urllib.error.HTTPError as e:
            self.log("send msg error:" + str(e.code) + " " + str(e.read().decode("utf-8")))

    def managemessage(self):
        if self.botmsgaction == "add":
            if self.isdelbotmsg:
                self.addmessage(self.botmsgid)
        elif self.botmsgaction == "del":
            self.deletemessage()

    def addmessage(self, messageid):
        if self.isgroup:
            self.cur.execute("""INSERT INTO `tggroupbotmsg` (`userid`, `messageid`) VALUES (%s, %s)""",
                             (self.userid, messageid))
            self.db.commit()

    def deletemessage(self):
        self.cur.execute("""SELECT `messageid` FROM `tggroupbotmsg` WHERE `userid` = %s""",
                         (self.userid))
        rows = self.cur.fetchall()
        self.cur.execute("""DELETE FROM `tggroupbotmsg` WHERE `userid` = %s""",
                         (self.userid))
        self.db.commit()
        for row in rows:
            try:
                url = "https://api.telegram.org/bot" + self.token + \
                    "/deleteMessage?chat_id=" + str(self.userid) + "&message_id=" + row[0]
                subprocess.Popen(['curl', '-s', url])
            except Exception:
                self.log("del msg error:")


class LineGame(Game):
    def __init__(self, userid, replytoken):
        from linebot import LineBotApi
        super(LineGame, self).__init__("line", userid)
        config = configparser.ConfigParser()
        configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
        config.read(configpath)
        self.secret = config.get('line', 'secret')
        self.token = config.get('line', 'token')
        self.replytoken = replytoken
        self.line_bot_api = LineBotApi(self.token)

    def response(self, message):
        if self.isstart:
            response = super(LineGame, self).guess(message)
            if self.isstart and message.strip() == "放棄":
                response = super(LineGame, self).giveup() + "\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
            elif self.isstart and message.strip() == "提示":
                response = super(LineGame, self).hint()
            elif not self.isstart:
                response += "\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
        else:
            response = super(LineGame, self).start(message) + "\n\n可輸入「提示」獲取提示，放棄遊戲請輸入「放棄」"
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
        configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
        config.read(configpath)
        self.token = config.get('facebook', 'token')

    def response(self, message):
        self.log(message)
        if self.isstart:
            response = super(FacebookGame, self).guess(message)
            if self.isstart and message.strip() == "放棄":
                response = super(FacebookGame, self).giveup() + "\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
            elif self.isstart and message.strip() == "提示":
                response = super(FacebookGame, self).hint()
            elif not self.isstart:
                response += "\n\n繼續遊戲請輸入任意文字\n或輸入數字限定答案字數"
        else:
            response = super(FacebookGame, self).start(message) + "\n\n可輸入「提示」獲取提示，放棄遊戲請輸入「放棄」"
        return response

    def sendmessage(self, message):
        self.log(message)
        url = "https://graph.facebook.com/v2.7/me/messages"
        data = {'access_token': self.token,
                'recipient': {"id": self.userid},
                'message': {"text": message}
                }
        req = urllib.request.Request(url, urllib.parse.urlencode(data).encode())
        try:
            res = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            self.log("error:" + str(e.code) + " " + str(e.read().decode("utf-8")))

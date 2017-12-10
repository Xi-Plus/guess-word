# -*- coding: utf-8 -*-
import json
from flask import Flask, request, abort
import configparser
from game import *
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage

config = configparser.ConfigParser()
configpath = os.path.dirname(os.path.realpath(__file__))+'/config.ini'
config.read(configpath)
handler = WebhookHandler(config.get('line', 'secret'))
facebooK_hub_verify_token = config.get('facebook', 'hub_verify_token')

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World!"

@app.route("/facebook", methods=['GET'])
def facebookget():
	if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == facebooK_hub_verify_token:
		return request.args.get('hub.challenge')
	return "OK"

@app.route("/facebook", methods=['POST'])
def facebookpost():
	data = json.loads(request.data.decode("utf8"))
	if "messaging" in data["entry"][0]:		
		if "message" in data["entry"][0]["messaging"][0]:
			if "text" in data["entry"][0]["messaging"][0]["message"]:
				userid = data["entry"][0]["messaging"][0]["sender"]["id"]
				game = FacebookGame(userid)
				message = data["entry"][0]["messaging"][0]["message"]["text"]
				if message == "開始":
					game.sendmessage("？？ 的意思是：\n法律上判決文的第一段，記載判決結果與適用的法律。\n\n放棄遊戲請輸入 放棄")
				elif message == "判決":
					game.sendmessage("錯誤")
				elif message == "主文":
					game.sendmessage("正確")
				else :
					response = game.response(message)
					game.sendmessage(response)
	return "OK"

@app.route("/telegram", methods=['POST'])
def telegram():
	data = json.loads(request.data.decode("utf8"))
	if "message" in data:
		if "text" in data["message"]:
			userid = data["message"]["chat"]["id"]
			fromid = data["message"]["from"]["id"]
			date = data["message"]["date"]
			text = data["message"]["text"]
			game = TelegramGame(userid, fromid, date)
			if "reply_to_message" in data["message"] and data["message"]["reply_to_message"]["from"]["id"] != game.botid:
				return "OK"
			if "reply_to_message" not in data["message"] and not text.startswith("/"):
				return "OK"
			response = game.response(text)
			if game.isdelusermsg:
				game.addmessage(data["message"]["message_id"])
			if response != "":
				game.sendmessage(response, data["message"]["message_id"])
				game.managemessage()
			return "OK"
	return "OK"

@app.route("/line", methods=['POST'])
def line():
	signature = request.headers['X-Line-Signature']

	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)

	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def line_message_handler(event):
	userid = event.source.user_id
	message = event.message.text
	reply_token = event.reply_token

	game = LineGame(userid, reply_token)
	response = game.response(message)
	game.sendmessage(response)

if __name__ == "__main__":
	app.run()

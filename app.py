# -*- coding: utf-8 -*-
import json
import time
import traceback
from flask import Flask, request, abort
import configparser
from game import *
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage

config = configparser.ConfigParser()
configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
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
                response = game.response(message)
                game.sendmessage(response)
    return "OK"


@app.route("/guess")
def log1():
    game = Game("unknown", "unknown")
    game.cur.execute("""SELECT * FROM `guess`""")
    rows = game.cur.fetchall()
    text = ""
    for row in rows:
        text += row[0] + " " + row[1] + " " + row[2] + " " + row[3] + " " + row[4] + "\n<hr>\n"
    return text


@app.route("/log")
def log2():
    game = Game("unknown", "unknown")
    game.cur.execute("""SELECT `message` FROM `log` ORDER BY `time` DESC LIMIT 20""")
    rows = game.cur.fetchall()
    text = ""
    for row in rows:
        text += row[0] + "\n<hr>\n"
    return text


@app.route("/telegram", methods=['POST'])
def telegram():
    data = json.loads(request.data.decode("utf8"))
    if "message" in data:
        if "text" in data["message"]:
            date = data["message"]["date"]
            if date < time.time() - 600:
                return "OK"
            userid = data["message"]["chat"]["id"]
            fromid = data["message"]["from"]["id"]
            text = data["message"]["text"]
            game = TelegramGame(userid, fromid, date)
            if "reply_to_message" in data["message"] and data["message"]["reply_to_message"]["from"]["id"] != game.botid:
                return "OK"
            if "reply_to_message" not in data["message"] and not text.startswith("/") and game.isgroup:
                return "OK"
            first_name = data["message"]["from"]["first_name"]
            chat_name = first_name
            if "title" in data["message"]["chat"]:
                chat_name = data["message"]["chat"]["title"]
                if "username" in data["message"]["chat"]:
                    chat_name += " @" + data["message"]["chat"]["username"]
            response = game.response(text)
            if response != "":
                if game.isdelusermsg:
                    game.addmessage(data["message"]["message_id"])
                game.sendmessage(response, data["message"]["message_id"])
                if game.isgroup:
                    game.managemessage()
                    if game.isdelanswer:
                        game.addmessage(game.botmsgid)
                game.log("get " + str(userid) + " " + str(chat_name) + " " + str(fromid) + " " + first_name + " " + text)
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
    game.log('get ' + str(userid) + ' ' + str(message))
    response = game.response(message)
    game.sendmessage(response)


if __name__ == "__main__":
    app.run()

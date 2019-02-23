# -*- coding: utf-8 -*-
import argparse
import configparser
import os

import requests


config = configparser.ConfigParser()
configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
config.read(configpath)

token = config.get('telegram', 'token')

parser = argparse.ArgumentParser()
parser.add_argument('action', default='set')
parser.add_argument('--url', default=config.get('global', 'url') + 'telegram')
parser.add_argument('--max_connections', default=config.get('telegram', 'max_connections'))
args = parser.parse_args()
print(args)

if args.action == 'set':
    url = "https://api.telegram.org/bot{0}/setWebhook?url={1}&max_connections={2}".format(
        token, args.url, args.max_connections)
elif args.action == 'delete':
    url = "https://api.telegram.org/bot{0}/deleteWebhook".format(token)
elif args.action == 'get':
    url = "https://api.telegram.org/bot{0}/getWebhookInfo".format(token)
else:
    exit('unknown action.')

response = requests.get(url)
print(response.text)

#!/usr/bin/python3
import datetime
import time
import configparser
import pymysql
import os

timestamp = datetime.datetime.fromtimestamp(int(time.time() - 86400 * 30)).strftime('%Y-%m-%d %H:%M:%S')
print(timestamp)

config = configparser.ConfigParser()
configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
config.read(configpath)

db = pymysql.connect(
    host=config.get('database', 'host'),
    user=config.get('database', 'user'),
    passwd=config.get('database', 'passwd'),
    db=config.get('database', 'db'),
    charset=config.get('database', 'charset')
)
cur = db.cursor()

cur.execute("""DELETE FROM `log` WHERE `time` < %s""", (timestamp))
db.commit()

db.close()

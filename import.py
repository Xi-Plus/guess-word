#!/usr/bin/python3
import configparser
import pymysql
import csv
import os
import sys
import re

config = configparser.ConfigParser()
configpath = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'
config.read(configpath)

if len(sys.argv) > 1:
    infile = sys.argv[1]
else:
    exit("Usage: python import.py your_dictionary.csv")

print(infile)

f = open(infile, "r", encoding='utf8')
r = csv.reader(f, delimiter=',')
next(r)

db = pymysql.connect(host=config.get('database', 'host'),
                     user=config.get('database', 'user'),
                     passwd=config.get('database', 'passwd'),
                     db=config.get('database', 'db'),
                     charset=config.get('database', 'charset'))
cur = db.cursor()

for row in r:
    if row[0] == "2":
        wid = row[1]
        word = row[2]
        meaning = row[10]

        if "(" in word or "（" in word:
            word = re.sub(r"[(（].+[)）]", "", word)

        if re.search(r"\d", word) != None:
            continue

        print(len(word), word, meaning)
        cur.execute("""INSERT INTO `dictionary` (`id`, `word`, `meaning`) VALUES (%s, %s, %s)""",
                    (wid, word, meaning))
        db.commit()

db.close()

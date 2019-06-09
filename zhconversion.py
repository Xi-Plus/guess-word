# -*- coding: utf-8 -*-
import codecs
import configparser
import os


class ZhConversion():
    def __init__(self, text):
        config = configparser.ConfigParser()
        configpath = os.path.dirname(os.path.realpath(__file__)) + '/zhconversion.ini'
        config.readfp(codecs.open(configpath, "r", "utf8"))
        hant = config.get('global', 'hant')
        hans = config.get('global', 'hans')
        self.newtext = ""
        for i in range(len(text)):
            index = hant.find(text[i])
            if index != -1:
                self.newtext += hans[index]
            else:
                self.newtext += text[i]

    def text(self):
        return self.newtext

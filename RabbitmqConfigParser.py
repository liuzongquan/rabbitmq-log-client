# encoding:utf-8

import ConfigParser


class RabbitmqConfigParser:
    def __init__(self, config_file='rabbitmq.conf'):
        self.config_file = config_file

    def parse(self):
        cf = ConfigParser.ConfigParser()
        cf.read(self.config_file)
        return cf

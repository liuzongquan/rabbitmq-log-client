#-*- coding:utf-8

import threading
import json
import time
import datetime
import logging

from CurlRequest import CurlRequest
from RabbitmqConfigParser import RabbitmqConfigParser
from ConsumingThread import ConsumingThread


class SchedulingThread(threading.Thread):

    def __init__(self):
        super(SchedulingThread, self).__init__()
        self.available_exchange_set = set()
        self.current_consuming_exchange_set = set()
        self.alive_consuming_thread_dict = dict()

    def get_available_exchanges(self):
        rabbitmq_parser = RabbitmqConfigParser()
        auto_scan = rabbitmq_parser.parse().get("consumer", "auto_scan")
	print "auto_scan=%s" % auto_scan
        if auto_scan == 'true':
            # 调用rabbitMQ的http api接口获取可用的exchange列表
            http_api_url = rabbitmq_parser.parse().get("global", "http_api_url")
            user = rabbitmq_parser.parse().get("global", "user")
            password = rabbitmq_parser.parse().get("global", "password")
            vhost = rabbitmq_parser.parse().get("global", "vhost")
            # curl -i -u guest:guest http://localhost:15672/api/exchanges/vhost
            curl = CurlRequest("%s/exchanges/%s" % (http_api_url, vhost))
            curl.set_userpwd("%s:%s" % (user, password))
            curl.set_header(0)
            curl.perform()
            parsed_json = json.loads(curl.get_body())
            for item in parsed_json :
                if item['name'] and len(str(item['name']).strip()) > 0:
                    if item['type'] == rabbitmq_parser.parse().get("global", "queue_default_type"):
                        self.available_exchange_set.add(item['name'])

        else:
            # 读取配置文件中指定的exchange列表
            syn_exchanges = rabbitmq_parser.parse().get("consumer", "syn_exchanges")
            split_list = syn_exchanges.strip().split(",")
            for exchange in split_list:
                if len(exchange) > 0:
                    self.available_exchange_set.add(exchange)

    def start_subprocess(self):
        new_available_exchange_set = self.available_exchange_set.difference(self.current_consuming_exchange_set)
        if len(new_available_exchange_set) > 0:
            for exchange in new_available_exchange_set:
                new_consuming_thread = ConsumingThread(exchange)
                new_consuming_thread.start()
                self.alive_consuming_thread_dict[exchange] = new_consuming_thread
                self.current_consuming_exchange_set.add(exchange)

    def update_meta(self):
        for exchange in self.alive_consuming_thread_dict.keys():
            consuming_thread = self.alive_consuming_thread_dict.get(exchange)
            if not consuming_thread.is_alive :
                self.alive_consuming_thread_dict.pop(exchange)
                self.current_consuming_exchange_set.remove(exchange)

    def run(self):
	logging.basicConfig(filename='logger.log', level=logging.INFO)
        while True:
            try:
		logging.info("[%s]开始一轮新的扫描......" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                self.get_available_exchanges()
                self.start_subprocess()
                self.update_meta()
            except Exception, ex:
                print "[%s][Exception]程序异常: %s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ex)
                logging.info("[%s][Exception]程序异常: %s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ex))
            except RuntimeError, err:
                print "[%s][Error]程序异常" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), err)
                logging.info("[%s][Error]程序异常" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), err))

            time.sleep(int(RabbitmqConfigParser().parse().get("consumer", "detect_period")))

if __name__ == '__main__':
    sche = SchedulingThread()
    sche.start()

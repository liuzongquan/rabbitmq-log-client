#--*-- coding:utf-8

import threading

from Consumer import Consumer


class ConsumingThread(threading.Thread):

    def __init__(self, exchange):
        super(ConsumingThread, self).__init__()
        self.exchange = exchange

    def run(self):
        consumer = Consumer(self.exchange)
        consumer.start_consuming()

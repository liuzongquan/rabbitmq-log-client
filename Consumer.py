# encoding:utf-8

from RabbitmqConfigParser import RabbitmqConfigParser
from Utils import get_mac_address
import pika
import uuid
import re
import datetime


class Consumer:

    def __init__(self, exchange):
        rabbit_parser = RabbitmqConfigParser()
        self.host = rabbit_parser.parse().get("global", "host")
        self.port = rabbit_parser.parse().get("global", "port")
        self.user = rabbit_parser.parse().get("global", "user")
        self.password = rabbit_parser.parse().get("global", "password")
        self.vhost = rabbit_parser.parse().get("global", "vhost")
        self.queue_default_type = rabbit_parser.parse().get("global", "queue_default_type")
        self.log_postfix = rabbit_parser.parse().get("consumer", "log_postfix")
        self.out_dir = rabbit_parser.parse().get("consumer", "out_dir")

        self.exchange = exchange
        self.consumerID = self.exchange+ "-" + get_mac_address()
        self.queue = self.consumerID
        self.pattern = re.compile("^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\[.*?\]")

    def connect(self):

        credentials = pika.PlainCredentials(self.user, self.password)
        conn_params = pika.ConnectionParameters(host=self.host, port=int(self.port), virtual_host=self.vhost,
                                                credentials=credentials)
        # conn_params = pika.ConnectionParameters("localhost", credentials=credentials)
        conn_broker = pika.BlockingConnection(conn_params)
        channel = conn_broker.channel()
        channel.exchange_declare(exchange=self.exchange, type=self.queue_default_type, passive=False, durable=True,
                                 auto_delete=False)
        channel.queue_declare(queue=self.queue)
        channel.queue_bind(queue=self.queue, exchange=self.exchange, routing_key=self.exchange)

        return channel

    def msg_consumer(self, channel, method, header, body):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        if body == "quit":
            channel.basic_cancel(consumer_tag=self.consumerID)
            channel.stop_consuming()
        else:
            match = self.pattern.match(body)
            if match:
                time_str = match.group(1)
                log_postfix = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").strftime(self.log_postfix)
                log_file = self.out_dir + "/" + self.exchange + log_postfix
                f=open(log_file, "a")
                f.write(body+"\n")
                f.close()


        return

    def start_consuming(self):
        try:
            channel = self.connect()
            channel.basic_consume(self.msg_consumer, queue=self.queue, consumer_tag=self.consumerID)
            channel.start_consuming()
        except Exception, ex:
            print "%s connect error: %s" % (self.exchange, ex)


if __name__ == '__main__':
    consumer = Consumer("hello-exchange3")
    consumer.start_consuming()

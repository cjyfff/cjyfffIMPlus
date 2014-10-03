#! /usr/bin/env python
#coding=utf-8

import pika
import json

EXCHANGE_NAME = 'CJYFFFIM'

#连接rabbitmq服务器
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

#定义队列
channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
channel.queue_declare(queue='server_q')
channel.queue_bind(exchange=EXCHANGE_NAME, queue='server_q', routing_key='server')
print ' [*] Waiting for client'


def request(ch, method, properties, body):
    online_msg = json.loads(body)

    response_msg = '''{
        'type': 'online_resp',
    }'''
    print "server24", properties.reply_to
    #将计算结果发送回控制中心
    ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
    ch.basic_publish(exchange=EXCHANGE_NAME,
                     routing_key=online_msg['user_id'],
                     body=response_msg)
    ch.basic_ack(delivery_tag = method.delivery_tag)
    print "server26"

channel.basic_qos(prefetch_count=1)
channel.basic_consume(request, queue='server_q')

channel.start_consuming()

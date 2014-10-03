#! /usr/bin/env python
#coding=utf-8

import pika

#连接rabbitmq服务器
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

#定义队列
channel.exchange_declare(exchange='test', type='direct')
channel.queue_declare(queue='server_q')
channel.queue_bind(exchange='test', queue='server_q', routing_key='server')
print ' [*] Waiting for client'

#定义接收到消息的处理方法
def request(ch, method, properties, body):
    response_msg = '''{
        'type': 'online_resp',
    }'''
    print "server24", properties.reply_to
    #将计算结果发送回控制中心
    ch.exchange_declare(exchange='test',  
                         type='direct')
    ch.basic_publish(exchange='test',
                     routing_key='jackson',
                     body=response_msg)
    ch.basic_ack(delivery_tag = method.delivery_tag)
    print "server26"

channel.basic_qos(prefetch_count=1)
channel.basic_consume(request, queue='server_q')

channel.start_consuming()

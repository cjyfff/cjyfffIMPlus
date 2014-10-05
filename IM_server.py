#! /usr/bin/env python
#coding=utf-8

import pika
import json
import time

EXCHANGE_NAME = 'CJYFFFIM'


def handle_online_msg(msg, ch, method):
    client_list = []
    user_id_list = []
    for i in client_list:
        user_id_list.append(i['user_id'])

    if msg['user_id'] not in user_id_list:
        client_list.append({
            'id': len(client_list) + 1,
            'user_name': msg['from'],
            'user_id': msg['user_id'],
        })

    response_msg = {
        'type': 'online_resp',
        'created_at': int(time.time()),
        'message': client_list,
    }
    #将计算结果发送回控制中心
    ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
    ch.basic_publish(exchange=EXCHANGE_NAME,
                     routing_key=msg['user_id'],
                     body=json.dumps(response_msg))
    ch.basic_ack(delivery_tag = method.delivery_tag)
    print "server35"


def handle_offline_msg(msg):
    print "server39", msg


def handle_normal_msg(msg, ch, method):
    print "server48", msg

    client_list = [{
        'id': 1,
        'user_name': 'kate',
        'user_id': msg['user_id'],
    }]

    d_client = {}
    for client in client_list:
        print "server59", client
        if int(client['id']) == int(msg['destination_id']):
            d_client = client
            break

    # destination user's id
    d_user_id = d_client['user_id']
    response_msg = {
        'type': 'normal',
        'from': msg['from'],
        'from_id': 1,
        'destination': msg['destination'],
        'destination_id': msg['destination_id'],
        'created_at': int(time.time()),
        'message': msg['message'],
    }

    ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
    ch.basic_publish(exchange=EXCHANGE_NAME,
                     routing_key=d_user_id,
                     body=json.dumps(response_msg))
    ch.basic_ack(delivery_tag = method.delivery_tag)


def request(ch, method, properties, body):
    msg = json.loads(body)

    if msg['type'] == 'online':
        handle_online_msg(msg, ch, method)

    elif msg['type'] == 'offline_notice':
        handle_offline_msg(msg)

    elif msg['type'] == 'normal':
        handle_normal_msg(msg, ch, method)


#连接rabbitmq服务器
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

#定义队列
channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
channel.queue_declare(queue='server_q')
channel.queue_bind(exchange=EXCHANGE_NAME, queue='server_q', routing_key='server')
print ' [*] Waiting for client'


channel.basic_qos(prefetch_count=1)
channel.basic_consume(request, queue='server_q')

channel.start_consuming()

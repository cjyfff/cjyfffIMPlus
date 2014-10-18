#! /usr/bin/env python
#coding=utf-8

import pika
import json
import time
import settings

EXCHANGE_NAME = settings.exchange_name
client_list = []


def handle_online_msg(msg, ch, method):
    global client_list
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
        'type': 'client_list',
        'created_at': int(time.time()),
        'message': [{'id': client['id'], 'user_name': client['user_name']} for client in client_list],
    }
    ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
    ch.basic_publish(exchange=EXCHANGE_NAME,
                     routing_key=msg['user_id'],
                     body=json.dumps(response_msg))
    ch.basic_ack(delivery_tag = method.delivery_tag)
    print "server35 end handle_online_msg"


def handle_offline_msg(msg, ch, method):
    global client_list
    for i in client_list:
        if i['user_id'] == msg['user_id']:
            client_list.remove(i)
    print "server44", client_list
    ch.basic_ack(delivery_tag = method.delivery_tag)

    if not client_list:
        return 0

    response_msg = {
        'type': 'client_list',
        'created_at': int(time.time()),
        'message': [{'id': client['id'], 'user_name': client['user_name']} for client in client_list],
        }
    ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
    for client in client_list:
        ch.basic_publish(exchange=EXCHANGE_NAME,
                         routing_key=client['user_id'],
                         body=json.dumps(response_msg))
    print "server60 end handle_offline_msg"


def handle_normal_msg(msg, ch, method):
    print "server48", msg
    global client_list

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
        'from_id': '',
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
        print "server81 recv online msg"
        handle_online_msg(msg, ch, method)

    elif msg['type'] == 'offline':
        handle_offline_msg(msg, ch, method)

    elif msg['type'] == 'normal':
        handle_normal_msg(msg, ch, method)


def main():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        channel.queue_declare(queue='server_q')
        channel.queue_bind(exchange=EXCHANGE_NAME, queue='server_q', routing_key='server')
        print " [*] Waiting for client"

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(request, queue='server_q')
        channel.start_consuming()
    except (KeyboardInterrupt, SystemError):
        connection.close()
        print " [*] Server exit..."

if __name__ == '__main__':
    main()

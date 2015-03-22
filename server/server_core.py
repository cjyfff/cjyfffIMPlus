#! /usr/bin/env python
#coding=utf-8

import pika
import json
import time
import settings
import logging
import sys
import os
import redis

EXCHANGE_NAME = settings.exchange_name

redis_pool = redis.ConnectionPool(host=settings.REDIS_HOST,
                                  port=settings.REDIS_PORT,
                                  db=settings.REDIS_DB)
rc = redis.Redis(connection_pool=redis_pool)
rc_key = settings.REDIS_KEY


class RedisJSONHandler(object):

    @classmethod
    def get(self, redis_conn, key):
        res = redis_conn.get(key)
        if not res:
            return []
        return json.loads(res)

    @classmethod
    def set(self, redis_conn, key, value):
        return redis_conn.setex(key, json.dumps(value), settings.REDIS_EXPIRE)


class BaseHandler(object):

    def __init__(self, msg, ch, method):
        self.msg = msg
        self.ch = ch
        self.method = method


class HandleOnlineMsg(BaseHandler):

    def run(self):
        client_list = RedisJSONHandler.get(rc, rc_key)
        user_id_list = []
        for client in client_list:
            user_id_list.append(client['user_id'])

        if self.msg['user_id'] not in user_id_list:
            client_list.append({
                    'id': len(client_list) + 1,
                    'user_name': self.msg['from'],
                    'user_id': self.msg['user_id'],
                    'prublic_key': self.msg['message']['prublic_key'],
            })
            RedisJSONHandler.set(rc, rc_key, client_list)

        response_msg = {
                'type': 'client_list',
                'created_at': int(time.time()),
                'message': [{'id': client['id'],
                             'user_name': client['user_name'],
                             'prublic_key': client['prublic_key']} for client in client_list],
            }
        self.ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        for client in client_list:
            self.ch.basic_publish(exchange=EXCHANGE_NAME,
                                  routing_key=client['user_id'],
                                  body=json.dumps(response_msg),
                                  properties=pika.BasicProperties(delivery_mode=2))
        self.ch.basic_ack(delivery_tag=self.method.delivery_tag)


class HandleOfflineMsg(BaseHandler):

    def run(self):
        client_list = RedisJSONHandler.get(rc, rc_key)
        for client in client_list:
            if client['user_id'] == self.msg['user_id']:
                client_list.remove(client)
                RedisJSONHandler.set(rc, rc_key, client_list)
        self.ch.basic_ack(delivery_tag = self.method.delivery_tag)

        if not client_list:
            return

        response_msg = {
            'type': 'client_list',
            'created_at': int(time.time()),
            'message': [{'id': client['id'],
                        'user_name': client['user_name'],
                        'prublic_key': client['prublic_key']} for client in client_list],
        }
        self.ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        for client in client_list:
            self.ch.basic_publish(exchange=EXCHANGE_NAME,
                                  routing_key=client['user_id'],
                                  body=json.dumps(response_msg),
                                  properties=pika.BasicProperties(delivery_mode=2))


class HandleNormalMsg(BaseHandler):

    def run(self):
        client_list = RedisJSONHandler.get(rc, rc_key)

        d_client = {}
        for client in client_list:
            if int(client['id']) == int(self.msg['destination_id']):
                d_client = client
                break

        # destination user's id
        d_user_id = d_client['user_id']
        response_msg = {
            'type': 'normal',
            'from': self.msg['from'],
            'from_id': '',
            'destination': self.msg['destination'],
            'destination_id': self.msg['destination_id'],
            'created_at': int(time.time()),
            'message': self.msg['message'],
        }

        self.ch.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.ch.basic_publish(exchange=EXCHANGE_NAME,
                              routing_key=d_user_id,
                              body=json.dumps(response_msg),
                              properties=pika.BasicProperties(delivery_mode=2))
        self.ch.basic_ack(delivery_tag=self.method.delivery_tag)


def request(ch, method, properties, body):
    msg = json.loads(body)

    if msg['type'] == 'online':
        handle_online_msg = HandleOnlineMsg(msg, ch, method)
        handle_online_msg.run()

    elif msg['type'] == 'offline':
        handle_offline_msg = HandleOfflineMsg(msg, ch, method)
        handle_offline_msg.run()

    elif msg['type'] == 'normal':
        handle_normal_msg = HandleNormalMsg(msg, ch, method)
        handle_normal_msg.run()


def main():
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'cjyfffIM.log'),
                        level=logging.WARN, filemode = 'a+',
                        format='%(asctime)s - %(levelname)s: %(message)s')
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        channel.queue_declare(queue='server_q', durable=True)
        channel.queue_bind(exchange=EXCHANGE_NAME, queue='server_q', routing_key='server')
        print " [*] Server running..."

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(request, queue='server_q')
        channel.start_consuming()
    except KeyboardInterrupt:
        connection.close()
        print " [*] Server exit..."
    except Exception, e:
        logging.error(e)
        print "\033[0;31;1m%s\033[0m" % (
                  "An error had happened and the server is down: " + str(e))
        sys.exit(1)

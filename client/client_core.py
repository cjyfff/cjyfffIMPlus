#! /usr/bin/env python
# coding=utf-8

import pika
import os
import time
import json
import threading
import copy
import rsa
import settings
from uuid import uuid4
from client_interface import ClientInterface


EXCHANGE_NAME = settings.EXCHANGE_NAME
MQServer = settings.MQServer

client_list = []


class SendOnlineMsg(object):

    def __init__(self, connection, msg, pubkey):
        self.connection = connection
        self.msg = copy.deepcopy(msg)
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()
        self.pubkey = pubkey

    def run(self):
        online_msg = self.msg
        online_msg.update({'created_at': int(time.time()),
                           'message': {'public_key': self.pubkey}})
        online_msg = json.dumps(online_msg)
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key='server',
                                   body=online_msg,
                                   properties=pika.BasicProperties(delivery_mode=2))


class SendNormalMsg(object):

    def __init__(self, msg, quit_msg):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=MQServer))
        self.msg = copy.deepcopy(msg)
        self.quit_msg = copy.deepcopy(quit_msg)
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()
        self.show_ci = ClientInterface()
        self.in_ci = ClientInterface()
        self.did = 0

    def send_quit_msg(self):
        # send quit msg to server
        self.quit_msg.update({'created_at': int(time.time())})
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key='server',
                                   body=json.dumps(self.quit_msg),
                                   properties=pika.BasicProperties(delivery_mode=2))

        # send quit msg to client itself
        self.quit_msg.update({'type': 'self_offline'})
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                   routing_key=self.user_id,
                                   body=json.dumps(self.quit_msg),
                                   properties=pika.BasicProperties(delivery_mode=2))
        self.connection.close()

    def show_client_list(self):
        global client_list
        # TODO: exclude client itself
        for client in client_list:
            self.show_ci.show_client_list(client['id'], client['user_name'])

    def check_did(self, did):
        global client_list
        if not did:
            self.show_ci.did_is_none()
            return False
        if did not in [i['id'] for i in client_list]:
            self.show_ci.did_is_invalid()
            return False
        return True

    @staticmethod
    def encrypt_msg(did, content):
        global client_list
        destination_pubkey = ''
        for client in client_list:
            if client['id'] == did:
                destination_pubkey = client['public_key']
                break
        if not destination_pubkey:
            return
        encrypt_content = rsa.encrypt(content, rsa.PublicKey.load_pkcs1(destination_pubkey))
        return encrypt_content

    def run(self):
        while 1:
            msg = self.in_ci.input_char()
            if not msg:
                continue
            if msg in ['quit', 'exit']:
                self.send_quit_msg()
                time.sleep(1)
                break
            if msg in ['client_list', 'cl']:
                self.show_client_list()
                continue

            try:
                did = int(msg.split(' ')[0])
                msg_content = msg[2:]
                self.did = did
            except (ValueError, IndexError):
                did = self.did
                msg_content = msg

            if not self.check_did(did):
                continue

            msg_content = self.encrypt_msg(did, msg_content)
            normal_msg = self.msg
            normal_msg.update({
                'destination_id': did,
                'created_at': int(time.time()),
                'message': msg_content.decode('latin-1'),
            })
            normal_msg = json.dumps(normal_msg, ensure_ascii=False)
            self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
            self.channel.basic_publish(exchange=EXCHANGE_NAME,
                                       routing_key='server',
                                       body=normal_msg,
                                       properties=pika.BasicProperties(delivery_mode=2))


class ReceiveMsg(object):

    def __init__(self, msg, connection, online_msg, pubkey, privkey):
        self.client_list = None
        self.connection = connection
        self.msg = msg
        self.user_id = self.msg['user_id']
        self.channel = self.connection.channel()
        self.privkey = privkey
        self.channel.exchange_declare(exchange=EXCHANGE_NAME, type='direct')
        queue_name = 'user_q' + self.user_id
        self.channel.queue_declare(queue=queue_name, durable=True)
        self.channel.queue_bind(exchange=EXCHANGE_NAME,
                                queue=queue_name,
                                routing_key=self.user_id)
        self.ci = ClientInterface()

        # In order to handling online response from server while
        # sending online msg, the function of sending online msg must be run
        # as the same time as running receiving msg function.
        send_online_msg = SendOnlineMsg(connection, online_msg, pubkey)
        send_online_msg.run()

    def notify_client_list_has_changed(self, body):
        if self.client_list is not None and body['message'] != self.client_list:
            self.ci.client_list_changed_warning()
        self.client_list = body['message']

    def save_client_list(self, body):
        global client_list
        self.notify_client_list_has_changed(body)
        # TODO: exclude client itself
        client_list = body['message']

    def decrypt_msg(self, content):
        try:
            return rsa.decrypt(content, self.privkey)
        except rsa.DecryptionError:
            self.ci.decryption_error()
            return False

    def on_response(self, body):
        if body['type'] == 'client_list':
            self.save_client_list(body)
        elif body['type'] == 'self_offline':
            pass
        else:
            msg = self.decrypt_msg(body['message'].encode('latin-1'))
            if msg:
                self.ci.show_msg(body['from'], msg)
            else:
                pass

    def run(self):
        queue_name = 'user_q' + self.user_id
        self.channel.basic_qos(prefetch_count=1)
        for method_frame, properties, body in self.channel.consume(queue_name):
            body = json.loads(body)
            self.on_response(body)
            self.channel.basic_ack(method_frame.delivery_tag)
            if body['type'] == 'self_offline':
                break
        self.connection.close()


class MyThread(threading.Thread):
    """Factory of new threads"""

    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def run(self):
        apply(self.func, self.args)


def main():
    username = os.environ['USER']
    user_id = uuid4().hex

    online_msg = {
        'type': 'online',
        'from': username,
        'user_id': user_id,
        'created_at': 0,
        'message': '',
    }

    normal_msg = {
        'type': 'normal',
        'from': username,
        'user_id': user_id,
        'destination': 'retain',
        'destination_id': 1,
        'created_at': '',
        'message': '',
    }

    quit_msg = {
        'type': 'offline',
        'from': username,
        'user_id': user_id,
        'created_at': '',
        'message': '',
    }

    (pubkey, privkey) = rsa.newkeys(1024)
    pubkey = pubkey.save_pkcs1()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=MQServer))
    send_normal_msg = SendNormalMsg(normal_msg, quit_msg)
    recive_msg = ReceiveMsg(normal_msg, connection, online_msg, pubkey, privkey)

    threads = []
    t1 = MyThread(send_normal_msg.run, (), )
    threads.append(t1)
    t2 = MyThread(recive_msg.run, (), )
    threads.append(t2)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

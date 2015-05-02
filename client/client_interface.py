#! /usr/bin/env python
# coding=utf-8
import settings

interface_type = settings.INTERFACE_TYPE


usage = '''
[cjyfffIMPlus client v0.84]
输入'client_list'或者'cl'查看当前在线的用户
输入用户对应的id + 空格 + 想要发送的消息，即可向该id对应的用户发送消息
例如输入'1 hello'，将会向id为1的用户发送消息"hello"
假如没有指定用户id的话，消息将发送到上一次所指定的用户
输入'quit'或者'exit'退出程序
'''


class NormalInterface(object):
    """
    普通CLI交互接口
    """
    @staticmethod
    def n_show_usage():
        print usage

    @staticmethod
    def n_sys_exit():
        print "Bye!"

    @staticmethod
    def n_show_client_list(id, name):
        print "id: {id}    name: {name}".format(id=id, name=name)

    @staticmethod
    def n_input_char():
        char = raw_input("> ")
        return char

    @staticmethod
    def n_client_list_changed_warning():
        print "Warning! client list has changed, enter 'cl' or 'client_list' to confirm."

    @staticmethod
    def n_show_msg(msg_from, msg):
        print "from {msg_from}: {msg}".format(msg_from=msg_from, msg=msg)

    @staticmethod
    def n_did_is_none():
        print "Please enter the id of the user you want to talk!"

    @staticmethod
    def n_did_is_invalid():
        print "This user id is not valid, please enter an valid one!"

    @staticmethod
    def decryption_error():
        print "Decryption error, please connect again."


class UnixSocketInterface(object):
    """
    unix socket 交互接口
    """
    pass


class ClientInterface(NormalInterface, UnixSocketInterface):
    """
    ClientInterface这个类会根据settings中的INTERFACE_TYPE值会选择不同的
    不同的交互接口，当INTERFACE_TYPE的值为`normal`时，将会选择使用默认的命令行交互；
    当INTERFACE_TYPE的值为其他值时（例如`unix_socket`），将会使用其他的交互方式。
    """
    def __getattribute__(self, item):
        if interface_type == 'normal':
            fun_name = 'n_' + item
        elif interface_type == 'unix_socket':
            fun_name = 'u_' + item
        else:
            raise TypeError('Unknown interface type: {0}'.format(interface_type))
        return super(ClientInterface, self).__getattribute__(fun_name)

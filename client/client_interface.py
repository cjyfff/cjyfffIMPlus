#! /usr/bin/env python
#coding=utf-8
from client_core import main

usage = '''
[cjyfffIMPlus client v0.81]
输入'client_list'或者'cl'查看当前在线的用户
输入用户对应的id + 空格 + 想要发送的消息，即可向该id对应的用户发送消息
例如输入'1 hello'，将会向id为1的用户发送消息"hello"
假如没有指定用户id的话，消息将发送到上一次所指定的用户
输入'quit'或者'exit'退出程序
'''

if __name__ == '__main__':
    print usage
    main()
    print "Bye!"

#! /usr/bin/env python
# coding=utf-8
import logging
from client_core import main
from client_interface import ClientInterface


class NullHandler(logging.Handler):

    def emit(self, record):
        pass


if __name__ == '__main__':
    h = NullHandler()
    ci = ClientInterface()
    logging.getLogger('pika').addHandler(h)
    ci.show_usage()
    main()
    ci.sys_exit()

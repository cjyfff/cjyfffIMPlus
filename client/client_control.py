#! /usr/bin/env python
#coding=utf-8


USAGE = '''
        Please Choose an Option:
        1 Show The User List
        2 Connect to an User, and Begin to Talk
        3 Exit
'''


def option():
    '''Menu of options'''
    while 1:
        print USAGE
        action = raw_input("> ")
        if action is '1':
            pass
        elif action is '2':
            pass
        elif action is '3':
            pass
        else:
            pass


def main():
    '''Main function'''

    try:
        option()
    except (KeyboardInterrupt, SystemError):
        pass


if __name__ == '__main__':
    main()

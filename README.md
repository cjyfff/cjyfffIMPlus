##cjyfffIMPlus: 一个基于RabbitMQ的多人即时通讯程序   
   
###1 描述：   
cjyfffIMPlus是一个基于RabbitMQ的多人即时通讯程序，采用C\S模式，能够检测用户的上线和下线，对用户信息进行加密并实现持久化，并且实现多人同时双向通信。   
   
###2 版本历史：    
   
0.8.0   
发布日期： 2014.10.19   
更新内容：实现程序基本功能。   
   
###3 依赖：   
   
客户端：   
python 2.7   
pika 0.9.13   
RabbitMQ 3.2.4   
   
服务器端：   
python 2.7   
pika 0.9.13   
RabbitMQ 3.2.4   
   
###4 使用方法：   
   
服务器端：   
运行server_core.py   
   
客户端：   
运行client_interface.py   
输入'client_list'或者'cl'查看当前在线的用户   
输入用户对应的id + 空格 + 想要发送的消息，即可向该id对应的用户发送消息   
例如输入'1 hello'，将会向id为1的用户发送消息"hello"   
假如没有指定用户id的话，消息将发送到上一次所指定的用户   
输入'quit'或者'exit'退出程序   
   
###5 消息协议（example）：   
    客户端发送一般信息给服务器的格式，routing_key: 'server'：   
    {   
        'type': 'normal',    
        'from': 'jackson',   
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6', #采用uuid4生成   
        'destination': 'kate',   
        'destination_id': 1,   
        'created_at': '1412318244',   
        'message': 'balabalabala',   
    }   
    
    服务器转发一般信息给客户端的格式（[user_id]代表目标用户的user_id），routing_key: [user_id]:   
    {   
        'type': 'normal',    
        'from': 'kate',   
        'from_id': 2,   
        'user_id': '',   
        'destination': 'jackson',   
        'destination_id': 1,   
        'created_at': '1412318254',   
        'message': 'balabalabala',   
    }   
       
    上线信息, routing_key: 'system'：   
    {   
        'type': 'online',    
        'from': 'jackson',   
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6',   
        'created_at': '1412318244',   
        'message': {'prublic_key': '-----BEGIN RSA PUBLIC KEY...'},  #RSA加密的公钥   
    }   
       
    下线信息（发给服务器）, routing_key: 'system'：   
    {   
        'type': 'offline',    
        'from': 'jackson',   
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6',   
        'created_at': '1412318244',   
        'message': '',   
    }   
       
    下线信息（发给自身），routing_key：[uuid]   
    {   
        'type': 'self_offline',    
        'from': 'jackson',   
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6',   
        'created_at': '1412318244',   
        'message': '',   
    }   
       
    服务器反馈客户端列表给客户端。当某客户上线时，反馈给所有客户；
    当某客户下线时，反馈给除了该客户以外的所有客户。routing_key: [user_id]：   
    {   
        'type': 'client_list',   
        'created_at': '1412318244',   
        'message': [   
            {'id': 1,   
              'user_name': 'kate',   
            },   
            {'id': 2,   
              'user_name': 'mike',   
            },   
        ]   
    }   

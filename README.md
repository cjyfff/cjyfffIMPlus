##cjyfffIMPlus: 一个基于RabbitMQ的多人即时通讯程序   
   
###1、描述   
cjyfffIMPlus是一个基于RabbitMQ的多人即时通讯程序，采用C\S模式，能够检测用户的上线和下线，对用户信息进行加密并实现持久化，并且实现多人同时双向通信。   
   
###2、版本历史   
0.8.3   
发布日期：2015.3.22   
更新内容： 服务器端使用redis缓存客户列表   
0.8.2    
发布日期：2015.1.11   
更新内容：修复下线时服务器发送client list没有包含prublic key的问题，服务器程序添加日志记录功能   
0.8.1    
发布日期：2014.12.2    
更新内容：对信息实现RSA加密   
0.8.0   
发布日期： 2014.10.19   
更新内容：实现程序基本功能。   
   
###3、依赖   
客户端和服务器端均需要安装rabbitmq-server 3.2.4，另外服务器端需要安装redis-server 2:2.8.4-2，python版本均为2.7。    
python依赖库已经使用virtualenv打包（基于ubuntu14.04），进入/client/IM_client_env/ （服务器是/server/IM_server_env），执行soure ./bin/activate即可进入运行环境。   
   
客户端：   
1. pika==0.9.13   
2. rsa==3.1.4   
   
服务器端：   
1. pika==0.9.13    
2. redis==2.10.3   
   
###4、部分工作原理    
* 关于消息投递   
消息队列中的routing_key是采用在客户端生成的一个user_id。   
在服务器端程序定义了一个交换机，然后通过这个routing_key投递消息。客户端程序连接到服务器端后，会根据自己的user_id得出routing_key，然后把这个交换机、routing_key绑定到一个queue上进行消息的消费。   
   
* 关于解密与加密   
客户端一开始运行时，都会生成一对密钥。在发送上线信息给服务器端时，会把prublic_key 包含到上线信息当中。服务器端会在广播信息中把该用户的prublic_key发给所有用户，当A用户要和B用户通信时，A用户会把要发送的信息用B用户的prublic_key加密，然后通过服务器把信息转发给B，B用户收到信息后，就用自己的private_key解密信息。   
   
###5、使用方法：   
   
服务器端：   
运行server_core.py   
   
客户端：   
运行client_interface.py   
输入'client_list'或者'cl'查看当前在线的用户   
输入用户对应的id + 空格 + 想要发送的消息，即可向该id对应的用户发送消息   
例如输入'1 hello'，将会向id为1的用户发送消息"hello"   
假如没有指定用户id的话，消息将发送到上一次所指定的用户   
输入'quit'或者'exit'退出程序   
   
###6、消息协议（example）：   
    一般通信信息，由客户端发送给服务器，routing_key: 'server'：
    {
        'type': 'normal', 
        'from': 'jackson',
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6', #采用uuid4生成
        'destination': 'kate',
        'destination_id': 1,
        'created_at': '1412318244',
        'message': 'balabalabala',
    }
    
    服务器转发信息，由服务器发给客户端，routing_key: [user_id]:
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
    
    上线信息，由客户端发给服务器，routing_key: 'system'：
    {
        'type': 'online', 
        'from': 'jackson',
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6',
        'created_at': '1412318244',
        'message': {'prublic_key': '-----BEGIN RSA PUBLIC KEY...'},  #RSA加密的公钥
    }
    
    下线信息，由客户端发给服务器，routing_key: 'system'：
    {
        'type': 'offline', 
        'from': 'jackson',
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6',
        'created_at': '1412318244',
        'message': '',
    }
    
    下线信息，由客户端发给自己，以便退出程序，routing_key：[uuid]
    {
        'type': 'self_offline', 
        'from': 'jackson',
        'user_id': '4b3f76fb2c96495cbc365cd005c147d6',
        'created_at': '1412318244',
        'message': '',
    }
    
    反馈客户端列表信息。由服务器发给客户端。当某客户上线时，反馈给所有客户；
    当某客户下线时，反馈给除了下线客户以外的所有客户。routing_key: [user_id]：
    {
        'type': 'client_list',
        'created_at': '1412318244',
        'message': [
            {'id': 1,
              'user_name': 'kate',
              'prublic_key': '----BEGIN RSA PUBLIC KEY...',
            },
            {'id': 2,
              'user_name': 'mike',
              'prublic_key': '----BEGIN RSA PUBLIC KEY...',
            },
        ]
    }

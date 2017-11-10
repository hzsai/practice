#!/usr/bin/env python3
# filename: client_tcp.py

import socket

#初始化
buffer_size = 1024
ip_port = ('192.168.43.120', 8080)
# 生成socket对象，指定为SOCK_STREAM，即tcp连接
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 客户端连接目标ip和端口号
client.connect_ex(ip_port)

while True:
    msg = input(">>: ").strip()
    if len(msg) == 0:
        continue
    # 客户端发送信息
    client.send(msg.encode('utf-8'))
    # 阻塞的等待信息
    feedback = client.recv(buffer_size)
    if feedback.decode('utf-8') == 'exit':
        break
    print(feedback.decode('utf-8'))

# 关闭当前连接
client.close()
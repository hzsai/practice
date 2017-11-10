#!/usr/bin/env python3
# filename: client_udp.py

import socket

# 初始化信息
ip_port = ('192.168.43.120', 1047)
buffer_size = 1024

# 创建socket, 指定为socket.SOCK_DGRAM，即UDP socket
client_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    """
        UDP不用连接，直接发送信息给目的端口
    """
    msg = input(">>: ")
    if not msg:
        continue
    if msg == 'exit':
        break
    # 发送信息
    client_udp.sendto(msg.upper().encode('utf-8'), ip_port)
    # 接受server的返回信息
    feedback = client_udp.recvfrom(buffer_size)

    print(feedback[0].decode('utf-8'))

# 结束当前udp，准备释放资源
client_udp.close()


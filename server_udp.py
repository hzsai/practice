#!/usr/bin env python3
# filename: server_udp.py

import socket

# 初始化信息
ip_port = ('192.168.43.120', 1047)
buffer_size = 1024

# 创建socket对象，指定为sock.SOCK_DGRAM,即UDP socket
udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 绑定端口
udp_server.bind(ip_port)

while True:
    """
        不断等待客户端的连接
    """
    print("寂寞的等待中的udp server。。。")
    # 阻塞的等待连接
    msg, address = udp_server.recvfrom(buffer_size)
    print("Msg: {0}, Addr: {1} ".format(msg.decode('utf-8'), address))
    # udp server回复信息给address
    udp_server.sendto("-----> 你好，这里是服务端{0}( •̀ ω •́ )y\n-----> 收到你的消息：{1}"
                      .format(ip_port, msg.upper().decode('utf-8')).encode('utf-8'), address)


    # 当然还可以用server端回复client端，，，
    # back_msg = input("回信 >>: ")
    # udp_server.sendto(back_msg.encode('utf-8'), addr)


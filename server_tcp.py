#!/usr/bin/env python3
# filename: server_tcp.py

# 导入socket模块
import socket
import time

# 初始ip、端口号、缓冲区大小
ip_port = ('192.168.43.120', 8080)
buffer_size = 1024

# 创建sock对象
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 服务端绑定端口
server.bind(ip_port)

# 最大尝试链接数
server.listen(5)

print('服务器正在为您服务( •̀ ω •́ )y')

while True:
    """
       不断的等待连接,接受连接
    """

    # 连接等待，阻塞, socket.accept()返回一个pair（conn, address）
    print("Waiting...")
    connection, address = server.accept()

    # 阻塞结束，
    print('来自%s的连接' % address[0])
    while True:
        # 消息等待阻塞
        client_msg = connection.recv(buffer_size)
        if len(client_msg) == 0:
            continue
        if client_msg.decode('ascii') == 'exit':
            connection.send('exit'.encode('ascii'))
            break
        print('%s' % address[0] + ' 说 ' + '%s' % client_msg.decode('ascii'))
        # 响应信息
        connection.send("hello, {0}".format(address[0]).encode('ascii'))

    # 等待一段时间，等待client端完成传输
    time.sleep(1)
    # 连接结束
    connection.close()

# 标记socket为closed状态（在完成传输任务后，socket关闭）
server.close()
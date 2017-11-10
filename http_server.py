#!/usr/bin env python3
# filename: http_server.py

import socket
import time
import os


class SimpleHttpServer:

    # 常量以及连接数、后用
    connections = 0
    MAX_LENGTH = 1024

    def __init__(self, ip="127.0.0.1", port=8080, buffer_size=1024):
        """
        初始化服务器
        :param ip: ip
        :param port: 端口号
        :param buffer_size: 缓冲区大小 
        """
        self.ip = ip
        self.port = port
        self.buffer_size = buffer_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.listen(5)
        self.content = ""
        self.header = {}

    def __repr__(self):
        """
        打印当前正在运行的信息
        :return: 
        """
        return "<Running on {0}:{1}>".format(self.ip, self.port)

    @staticmethod
    def response(url, status):
        content = ""
        if status == 404:
            with open('PageNotFound.html', 'rt', encoding='utf-8') as file:
                content = file.read()
        else:
            with open(url, 'rt', encoding='utf-8') as file:
                content = file.read()
        return content

    @staticmethod
    def build_http_header(status, location, last_modified=time.time(),encoding='utf-8', server='python_server',
                    language='zh-CN', content_type="text/html"):
        """
        构造响应头，返回响应头
        """
        header = dict()
        header['Server'] = server
        header['Location'] = location
        header['Content-Length'] = 528
        header['Content-Encoding'] = encoding
        header['Content-Language'] = language
        header['Content-Type'] = content_type
        header['Last-Modified'] = last_modified

        """
            ！！！响应头格式要注意，注意，注意，注意（多余空格也不要）。留坑,,,
        """
        head = ""
        if status == 200:
            head += "HTTP/1.1 200 OK\r\n"
        else:
            head += "HTTP/1.1 404\r\n"
        for key, value in header.items():
            head += str(key) + ":" + str(value) + '\r\n'
        # 响应头的结束
        head += '\r\n'
        return head

    @staticmethod
    def prepare_content(request):

        content = ""
        # 请求的信息，当然，这里很多都没有解析啦
        method = request[0]
        url = request[1][1::]
        # f_type要根据url来解析，不写了，，，
        f_type = 'text/html'
        # 处理访问文件的情况
        if url == '/' or url == '':
            url = 'index.html'
        if os.path.exists(url):
            status = 200
        else:
            status = 404
        header = SimpleHttpServer.build_http_header(status=status, location=url, content_type=f_type)
        content += header
        body = SimpleHttpServer.response(url, status)
        content += body

        return content

    def run(self):

        """
        服务器服务一直运行，响应一个请求后继续等待下一个请求
        :return: 
        """
        fl = True
        print("Server Running on {0}:{1}...".format(self.ip, self.port))
        while fl:
            # 等待连接
            try:
                conn, addr = self.socket.accept()
            except:
                continue
            # ！！！返回的请求是字节流
            request = conn.recv(self.buffer_size)
            print("Client: {0}:{1}".format(addr[0], addr[1]))

            # 收到请求后，可以根据request的内容来响应，另外处理
            content = request.decode('utf-8')
            req = content.split(' ')
            # 过滤空请求
            if req is None or req == ['']:
                continue
            # 调试信息
            print("Method: ----> %s, Required Resourse: ----> %s"%(req[0], req[1]))

            # 对请求进行解析，并返回内容
            content = SimpleHttpServer.prepare_content(req)
            # 发送
            conn.sendall(content.encode('utf-8'))
            # 关闭连接（没有keepalive情况下直接关闭）
            conn.close()


if __name__ == '__main__':
    """
    实例化
    """
    server = SimpleHttpServer(ip="192.168.43.120", port=80)
    server.run()

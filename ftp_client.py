#!/usr/bin env python3
# filename: ftp_client

import socket
from socket import _GLOBAL_DEFAULT_TIMEOUT

FTP_PORT = 21
CRLF = '\r\n'
B_CRLF = b'\r\n'
MAXLINE = 8196
ERROR_BUFFER = ''


class Error(Exception): pass


class error_reply(Error): pass


class error_temp(Error): pass


class error_perm(Error): pass


class error_proto(Error): pass


class FtpClient:
    host = ''
    maxline = MAXLINE
    port = FTP_PORT
    file = None
    sock = None
    welcome = None
    data_type = None
    encoding = 'latin-1'
    passive = True

    def __init__(self, host='', user='', passwd='', acct='',
                 timeout=_GLOBAL_DEFAULT_TIMEOUT, source_address=None):
        self.timeout = timeout
        self.source_address = source_address
        self.data_type = 'I'
        if host:
            self.connect(host)
            if user:
                self.login(user, passwd, acct)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.sock is not None:
            try:
                self.quit()
            except (OSError, EOFError):
                pass
            finally:
                if self.sock is not None:
                    self.close()

    def quit(self):
        resp = self.voidcmd('QUIT')
        self.close()
        return resp

    def close(self):
        try:
            file = self.file
            self.file = None
            if file is not None:
                file.close()
        finally:
            sock = self.sock
            self.sock = None
            if sock is not None:
                sock.close()

    def login(self, user='', passwd='', acct=''):
        resp = self.sendcmd('USER ' + user)
        if resp[0] == '3':
            resp = self.sendcmd('PASS ' + passwd)
        if resp[0] == '3':
            resp = self.sendcmd('ACCT ' + acct)
        if resp[0] != '2':
            raise error_reply(resp)
        return resp

    def connect(self, host='', port=0, timeout=-999, source_address=None):
        if self.host != '':
            self.host = host
        if port > 0:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        else:
            self.timeout = _GLOBAL_DEFAULT_TIMEOUT
        if source_address is not None:
            self.source_address = source_address
        self.sock = socket.create_connection((host, port), self.timeout,
                                             self.source_address)
        self.file = self.sock.makefile('r', encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def getwelcome(self):
        return self.welcome

    def set_pasv(self, val=True):
        self.passive = val

    def putline(self, line):
        line = line + CRLF
        self.sock.sendall(line.encode(self.encoding))

    def putcmd(self, line):
        self.putline(line)

    def getline(self):
        line = self.file.readline(self.maxline + 1)
        if len(line) > self.maxline:
            raise BufferError("More than %d bytes" % self.maxline)
        if not line:
            raise EOFError
        if line[-2:] == CRLF:
            line = line[:-2]
        if line[-1:] in CRLF:
            line = line[:-1]
        return line

    def getmultiline(self):
        line = self.getline()
        if line[3:4] == '-':
            code = line[:3]
            while True:
                nextline = self.getline()
                line = line + ('\n' + nextline)
                if nextline[:3] == code and \
                                nextline[3:4] != '-':
                    break
        return line

    def getresp(self):
        resp = self.getmultiline()
        return resp

    def sendcmd(self, cmd):
        self.putcmd(cmd)
        return self.getresp()

    def voidresp(self):
        resp = self.getresp()
        if resp[:1] != '2':
            raise error_reply(resp)
        return resp

    def voidcmd(self, cmd):
        self.putcmd(cmd)
        return self.voidresp()

    def sendport(self, host, port):
        hbytes = host.split('.')
        pbytes = [repr(port // 256), repr(port % 256)]
        bytes = hbytes + pbytes
        cmd = 'PORT ' + ','.join(bytes)
        return self.voidcmd(cmd)

    def makeport(self):
        err = None
        sock = None
        for res in socket.getaddrinfo(None, 0, socket.AF_INET, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            fa, ty, proto, canoname, sa = res
            try:
                sock = socket.socket(fa, ty, proto)
                sock.bind(sa)
            except OSError as er:
                err = er
                if sock:
                    sock.close()
                sock = None
                continue
            break
        if sock is None:
            if err is not None:
                raise err
            else:
                raise OSError("getaddress info return empty list")

        sock.listen(1)
        host = self.sock.getsockname()[0]
        port = sock.getsockname()[1]
        resp = self.sendport(host, port)
        print(resp)
        if self.timeout != _GLOBAL_DEFAULT_TIMEOUT:
            sock.settimeout(self.timeout)
        return sock

    def makepasv(self):
        host, port = parse227(self.sendcmd('PASV'))
        return host, port


    def exec_cmd_mode_off(self, cmd, param=''):
        if param != '':
            cmd += ' '
        cmd += param
        if param == '..':
            cmd = 'CDUP'
        resp = self.sendcmd(cmd)
        return resp

    def exec_cmd_mode_on(self, cmd, param='', fp=None, callback=None):
        """
        RETR, STOR
        :param cmd: cmd to exec
        :param fp: file pointer
        :param callback: callback function
        :return: None
        """
        ori_cmd = cmd
        if param != '':
            cmd = cmd + ' '
        cmd += param
        if self.passive:
            host, port = self.makepasv()
            conn = socket.create_connection((host, port), timeout=self.timeout,
                                            source_address=(self.source_address))
            try:
                resp = self.sendcmd(cmd)
                if resp[:1] == '2':
                    resp = self.getresp()
                if resp[:1] != '1':
                    raise error_reply(resp)
            except:
                conn.close()
        else:
            sock = self.makeport()
            try:
                resp = self.sendcmd(cmd)
                if resp[:1] == '2':
                    resp = self.getresp()
                if resp[:1] != '1':
                    raise error_reply(resp)
            except:
                pass
            conn, addr = sock.accept()
            print("Connected.")
            if self.timeout != _GLOBAL_DEFAULT_TIMEOUT:
                conn.settimeout(self.timeout)
        if ori_cmd == 'RETR':
            if self.data_type == 'A':
                print("RETR TYPE A")
                lines = ''
                with conn.makefile('r', encoding=self.encoding) as fp:
                    while 1:
                        line = fp.readline(self.maxline + 1)
                        if not line:
                            break
                        if line[-2:] == CRLF:
                            line = line[:-2]
                        if line[-1:] in CRLF:
                            line = line[:-1]
                        lines += line
                        # callback to store the buf file
                callback('A', param, lines)
            else:
                print("RETR TYPE I")
                bufs = b''
                while 1:
                    buf = conn.recv(self.maxline + 1)
                    if not buf:
                        break
                    bufs += buf
                    # callback to store the buf file
                callback('I', param, bufs)
                # resp = self.getresp()
                # return resp
        elif ori_cmd == 'STOR':
            if self.data_type == 'A':
                print("STOR TYPE A")
                while 1:
                    buf = fp.readline(self.maxline + 1)
                    if not buf:
                        break
                    if buf[-2:] != B_CRLF:
                        if buf[-1:] in B_CRLF: buf = buf[:-1]
                        buf = buf + B_CRLF
                    conn.sendall(buf)
                    # callback is optional
            elif self.data_type == 'I':
                print("STOR TYPE I")
                while 1:
                    buf = fp.read(self.maxline + 1)
                    if not buf:
                        break
                    conn.sendall(buf)
                    # callback is optional
                    # resp = self.getresp()
                    # return resp
        elif ori_cmd == 'LIST':
            print("LIST CMD")
            with conn.makefile('r', encoding=self.encoding) as fp:
                lines = ''
                while 1:
                    line = fp.readline(self.maxline + 1)
                    if not line:
                        break
                    if line[-2:] == CRLF:
                        line = line[:-2]
                    if line[-1:] in CRLF:
                        line = line[:-1]
                    line += '\n'
                    lines += line
            resp = self.getresp()
            resp += '\n'
            return lines + resp
        else:
            print("CMD UNKNOWN, SORRY!")
        conn.close()
        resp = self.getresp()
        return resp

    def write_to_file(self, tp, filename, buf):
        import os, sys
        lock = True
        fl = False
        if os.path.exists(sys.path[0] + '/' + filename):
            fl = True
        if fl:
            ans = input("Do you want to OVERWRITE the file `{0}` ?(yes/no) ".format(filename))
            if ans[0] == 'Y' or ans[0] == 'y':
                lock = False
        else:
            lock = False
        if tp == 'A':
            if not lock:
                with open(filename, 'wt') as f:
                    f.write(buf)
        if tp == 'I':
            if not lock:
                with open(filename, 'wb') as f:
                    f.write(buf)


_227_re = None


def parse227(resp):
    '''Parse the '227' response for a PASV request.
    Raises error_proto if it does not contain '(h1,h2,h3,h4,p1,p2)'
    Return ('host.addr.as.numbers', port#) tuple.'''
    if resp[:1] != '2':
        raise error_reply(resp)
    global _227_re
    if _227_re is None:
        import re
        _227_re = re.compile(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', re.ASCII)
    m = _227_re.search(resp)
    if not m:
        raise error_proto(resp)
    numbers = m.groups()
    host = '.'.join(numbers[:4])
    port = (int(numbers[4]) << 8) + int(numbers[5])
    return host, port


_list = ['get', 'send', 'passive', 'active', 'binary', 'ascii', 'ls',
         'help', 'delete', 'pwd', 'cd', 'quit']

cmd_list = {'get <filename>': '获取文件', 'send <filename>': '发送文件',
            'passive': '被动模式', 'active': '主动模式', 'binary': '二进制式',
            'ascii': 'ascii式', 'ls': '列出文件', 'help': '显示帮助',
            'delete <filename>': '删除文件', 'pwd': '当前路径',
            'quit': '退出登录', 'cd': '更改路径'}


def sanitize(cmd):
    ori_cmds = {'get': 'RETR', 'send': 'STOR', 'passive': 'PASV', 'active': 'PORT',
                'binary': 'TYPE I', 'ascii': 'TYPE A', 'ls': 'LIST', 'help': 'HELP',
                'delete': 'DELE', 'pwd': 'PWD', 'cd': 'CWD', 'quit': 'QUIT',
                'NOOP': 'NOOP'}
    ori_cmd = ori_cmds[cmd]
    return ori_cmd


def parse_cp(proto_string=''):
    if proto_string.endswith('\r\n'):
        proto_string = proto_string.rstrip('\r\n')
    elif proto_string.endswith('\n'):
        proto_string = proto_string.rstrip('\n')
    _cmd = ''
    param = ''
    strings = proto_string.split(' ')
    try:
        strings = strings.remove(' ')
    except ValueError:
        pass
    if strings is not None:
        _cmd = str(strings[0])
        param = str(strings[-1])
    _cmd = _cmd.lower()
    param = param.lower()
    found = False
    for cmd in _list:
        if _cmd == str(cmd):
            found = True
            break
    if not found:
        _cmd = 'NOOP'
        param = ''
    if _cmd == param:
        param = ''
    _cmd = sanitize(_cmd)
    return _cmd, param


def print_help():
    cnt = 0
    for key, value in cmd_list.items():
        ed = '\n' if cnt % 2 else ' '
        cnt += 1
        print("%-20s :-> %-20s" % (key, value), end=ed)


    # TODO: TO distribute the methods:
    # """
    # 1.  get, send, ls, pwd, delete, cd, quit
    #       get, send, ls:要选择模式
    #       quit, pwd, delete, cd不用选模式 --fixed
    # 2. 将登陆交互化
    #       --不做了，，，再写就更长了
    # """

if __name__ == '__main__':
    ftp = FtpClient()
    ftp.connect('127.0.0.1', 21)
    ftp.login('heartz', 'hzs')
    print(ftp.getwelcome())
    print('Enter `help` for more information.')
    FIRST = False
    resp = ''
    while True:
        resp = ''
        if FIRST:
            print_help()
            FIRST = False
        string = input("ftp:>> ")
        cmd, param = parse_cp(string)
        print(cmd, param)
        if cmd == 'HELP':
            FIRST = True
        elif cmd == 'PASV':
            ftp.set_pasv(True)
        elif cmd == 'PORT':
            ftp.set_pasv(False)
        elif cmd == 'TYPE A':
            ftp.data_type = 'A'
            resp = ftp.sendcmd('TYPE A')
        elif cmd == 'TYPE I':
            ftp.data_type = 'I'
            resp = ftp.sendcmd('TYPE I')
        elif cmd == 'QUIT':
            resp = ftp.quit()
            break
        elif cmd == 'NOOP':
            continue
        elif cmd == 'RETR' or cmd == 'STOR' or cmd == 'LIST':
            if cmd == 'STOR':
                try:
                    fp = open(param, 'rb')
                    resp = ftp.exec_cmd_mode_on(cmd, param=param, fp=fp)
                except FileNotFoundError:
                    print("FileNotFound!")
            elif cmd == 'RETR':
                resp = ftp.exec_cmd_mode_on(cmd, param=param, callback=ftp.write_to_file)
            elif cmd == 'LIST':
                resp = ftp.exec_cmd_mode_on(cmd)
        else:
            resp = ftp.exec_cmd_mode_off(cmd, param=param)
        if resp != '':
            print(resp)
    print(resp)

import os
import socket
from threading import Thread
import struct
import string
import sys
import array
import codecs

def string2ip(ipstr):
    (a,b,c,d) = string.split(ipstr, ".")
    a = string.atoi(a)
    b = string.atoi(b)
    c = string.atoi(c)
    d = string.atoi(d)
    return a << 24 | b << 16 | c << 8 | d

def ip2string(ip):
    a = (ip & 0xff000000) >> 24
    b = (ip & 0x00ff0000) >> 16
    c = (ip & 0x0000ff00) >> 8
    d = (ip & 0x000000ff)
    return "%d.%d.%d.%d" % (a, b, c, d)

class QQWry:
    def __init__(self, data):
        self.data = data
        (self.first_index, self.last_index) = struct.unpack('II', self.data[0:8])
        self.count = (self.last_index - self.first_index) / 7 + 1
        self.position = 0

    def tell(self):
        return self.position

    def seek(self, position):
        if position >= len(self.data):
            position = len(self.data) - 1
        self.position = position

    def read(self, size):
        p = self.position + size
        if p >= len(self.data):
            p = len(self.data) - 1
        ret = self.data[self.position:p]
        self.position = p
        return ret

    def get_string(self, offset=0):
        if offset:
            self.seek(offset)

        if self.tell() == 0:
            return 'UNKNOWN_LOCATION'

        ret =''
        ch = self.read(1)
        (flag,) = struct.unpack('B', ch)
        while flag != 0:
            ret += ch
            ch = self.read(1)
            (flag,) = struct.unpack('B', ch)

        return ret

    def get_int3(self, offset=0):
        if offset:
            self.seek(offset)
        (a,b) = struct.unpack('HB', self.read(3))
        return (b << 16) | a

    def get_address_detail(self, offset=0):
        if offset:
            self.seek(offset)
        ch = self.read(1)
        (flag,) = struct.unpack('B', ch)
        if flag == 0x01 or flag == 0x02:
            p = self.get_int3()
            if p:
                return self.get_string(p)
            else:
                return ''
        else:
            return self.get_string(self.tell() - 1)

    def get_address(self, offset):
        self.seek(offset + 4)

        ch = self.read(1)
        (flag,) = struct.unpack('B', ch)
        if flag == 0x01:
            offset = self.get_int3()
            self.seek(offset)
            ch = self.read(1)
            (flag,) = struct.unpack('B', ch)
            if flag == 0x02:
                address = self.get_string(self.get_int3())
                self.seek(offset + 4)
            else:
                address = self.get_string(offset)
            detail = self.get_address_detail()
        elif flag == 0x02:
            address = self.get_string(self.get_int3())
            detail = self.get_address_detail(offset + 8)
        else:
            address = self.get_string(offset + 4)
            detail = self.get_address_detail()

        return address + '/' + detail

    def find(self, ip_addr, bi, ei):
        if (ei - bi <= 1):
            return bi
        else:
            mi = (bi + ei) / 2
            offset = self.first_index + mi * 7
            self.seek(offset)
            (addr,) = struct.unpack('I', self.read(4))
            if (ip_addr <= addr):
                return self.find(ip_addr, bi, mi)
            else:
                return self.find(ip_addr, mi, ei)

    def get_location(self, ip_addr):
        index = self.find(ip_addr, 0, self.count - 1)
        offset = self.first_index + index * 7
        offset = self.get_int3(offset + 4)
        return self.get_address(offset)

class QQWryThread(Thread):
    def __init__(self, qqwry, c_socket):
        Thread.__init__(self)
        self.qqwry = qqwry
        self.c_socket = c_socket

    def run(self):
        try:
            try:
                ipstr = self.c_socket.recv(1024)
                if not ipstr:
                    return
                ip = string2ip(ipstr)
                location = self.qqwry.get_location(ip)
                location = self.gbk2utf8(location)
                self.c_socket.send(location)
                #self.c_socket.send("\n")
            except:
                print "IPADDRESS: ", ipstr
                raise
        finally:
            self.c_socket.close()

    def gbk2utf8(self, gbk):
        unicode = codecs.decode(gbk, 'GBK', 'ignore');
        utf8 = codecs.encode(unicode,'UTF8', 'ignore')
        return utf8



def main(argv=None):
    SOCK_FILE = '/tmp/qqwry.sock'
    DATA_FILE = 'QQWry.Dat'

    try:
        os.remove(SOCK_FILE)
    except OSError:
        pass

    file = open(DATA_FILE, 'rb')
    data = file.read()
    file.close()

#    qqwry = QQWry(data)
#    print qqwry.get_location(string2ip('161.142.146.164'))
#    return

    s_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s_socket.bind((SOCK_FILE))
    s_socket.listen(5)
    while 1:
        (c_socket,addr) = s_socket.accept()
        thread = QQWryThread(QQWry(data), c_socket)
        thread.start()
    s_socket.close()

if __name__ == '__main__' :
    main()
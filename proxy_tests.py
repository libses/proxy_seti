import socket
import threading
import unittest.mock
import socketserver

from threading import Thread

import server_handler


class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        self.request.settimeout(server_handler.HttpProxyHandler.TIMEOUT)
        mes: bytes = self.request.recv(server_handler.HttpProxyHandler.PACKET_SIZE)
        self.request.sendall(mes)


class ProxyShould(unittest.TestCase):
    HTTPS_CONNECT = b'CONNECT www.google.com:443 HTTP/1.1\r\n' \
                    b'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0\r\n' \
                    b'Proxy-Connection: keep-alive\r\nConnection: keep-alive\r\nHost: localhost:443\r\n\r\n'

    HTTP_REQ = b'GET http://somkural.ru/ HTTP/1.1\r\n' \
               b'Host: localhost:8084\r\n' \
               b'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0\r\n' \
               b'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8\r\n' \
               b'Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3\r\n' \
               b'Accept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\n' \
               b'Cookie: BITRIX_SM_GUEST_ID=8005234; BITRIX_SM_LAST_VISIT=07.05.2022+20%3A07%3A02; BITRIX_SM_LAST_ADV=5\r\n' \
               b'Upgrade-Insecure-Requests: 1\r\n\r\n'

    def setUp(self) -> None:
        self.proxy = socketserver.TCPServer(('localhost', 8081), server_handler.HttpProxyHandler)
        self.http_server = socketserver.TCPServer(('localhost', 8084), EchoHandler)
        self.https_server = socketserver.TCPServer(('localhost', 443), EchoHandler)
        threading.Thread(target=self.proxy.serve_forever).start()
        threading.Thread(target=self.https_server.serve_forever).start()
        threading.Thread(target=self.http_server.serve_forever).start()

    def tearDown(self) -> None:
        self.proxy.shutdown()
        self.https_server.shutdown()
        self.http_server.shutdown()
        self.proxy.server_close()
        self.https_server.server_close()
        self.http_server.server_close()

    def test_when_https_should_return_connect_message(self):
        host = socket.socket()
        host.settimeout(server_handler.HttpProxyHandler.TIMEOUT)
        host.connect(('localhost', 8081))
        host.send(self.HTTPS_CONNECT)
        ans = host.recv(server_handler.HttpProxyHandler.PACKET_SIZE)
        host.send(b'')
        host.close()

        self.assertTrue("200" in ans.decode().lower())

    def test_when_https_should_to_transmitted_messages_after_connect(self):
        host = socket.socket()
        host.settimeout(server_handler.HttpProxyHandler.TIMEOUT)
        host.connect(('localhost', 8081))

        host.send(self.HTTPS_CONNECT)
        host.recv(1024)
        host.send(b'12345')
        res = host.recv(server_handler.HttpProxyHandler.PACKET_SIZE)
        host.close()

        self.assertTrue(res.decode() == '12345')

    def test_http_server_should(self):
        host = socket.socket()
        host.settimeout(server_handler.HttpProxyHandler.TIMEOUT)
        host.connect(('localhost', 8081))
        host.send(self.HTTP_REQ)
        answer = host.recv(60000)
        host.close()

        self.assertEqual(self.HTTP_REQ, answer)


if __name__ == '__main__':
    unittest.main()

import re
import socket
import socketserver
import threading

import server_handler
from connection_type import ConnectionType


class HttpProxyHandler(socketserver.BaseRequestHandler):
    CONNECTION_REPLY = b'HTTP/1.1 200 Connection established\r\n\r\n'
    LINK_REG = re.compile(r'(?<=Host: )(?P<name>[^\n:\r ]+)(:(?P<port>\d+))?')
    PACKET_SIZE = 65534
    TIMEOUT = 0.5

    def handle(self) -> None:
        try:
            print(f'connect to {self.client_address}')
            self.request.settimeout(self.TIMEOUT)
            data: bytes = self.request.recv(self.PACKET_SIZE)
            d_data = data.decode()
            connect_type = self.get_connection_type(d_data)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.TIMEOUT)
                addr = self.parse_address(d_data)
                name = addr['name']
                port = addr['port']
                if port is None:
                    port = 80 if connect_type is connect_type.HTTP else 443
                sock.connect((name, int(port)))
                if connect_type is connect_type.HTTPS:
                    self.request.sendall(self.CONNECTION_REPLY)
                else:
                    sock.sendall(data)
                a = threading.Thread(target=server_handler.HttpProxyHandler.handle_from_remote, args=(self, sock))
                a.start()
                with sock.dup() as sock_d:
                    self.handle_from_client(sock_d)
        except Exception as e:
            print(e)

    def finish(self) -> None:
        self.request.close()

    def handle_from_remote(self, remote_server: socket.socket):
        errors_count = 0
        while True:
            if errors_count > 5:
                break
            try:
                rec = remote_server.recv(self.PACKET_SIZE)
                self.request.sendall(rec)
                if len(rec) < 1:
                    break
                errors_count = 0
            except socket.timeout:
                errors_count += 1
                continue
                pass
            except Exception as e:
                print(f'{type(e)}----{e}')
                return

    def handle_from_client(self, remote_server: socket.socket):
        errors_count = 0
        while True:
            if errors_count > 5:
                break
            try:
                data = self.request.recv(self.PACKET_SIZE)
                remote_server.sendall(data)
                if len(data) < 1:
                    break
                errors_count = 0
            except socket.timeout:
                errors_count += 1
                pass
            except Exception as e:
                print(f'{type(e)}----{e}')
                return

    def parse_address(self, page: str) -> dict:
        return self.LINK_REG.search(page).groupdict()

    @staticmethod
    def get_connection_type(data: str) -> ConnectionType:
        return ConnectionType.HTTPS if "CONNECT" in data else ConnectionType.HTTP

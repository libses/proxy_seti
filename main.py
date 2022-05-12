import server_handler
import socketserver
from argparse import ArgumentParser

packet_size = 65534
timeout = 0.5


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-ho", dest="host", default='localhost',
                        help='Адрес, где будет хоститься прокси',
                        required=False)

    parser.add_argument("-p", dest="port", default=8081,
                        help='Порт, к которому будет производиться подключение',
                        type=int,
                        required=False)
    args = parser.parse_args()
    with ThreadingTCPServer((args.host, args.port), server_handler.HttpProxyHandler) as server:
        server.serve_forever()

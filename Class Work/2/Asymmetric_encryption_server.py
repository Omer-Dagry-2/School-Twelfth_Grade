import socket
import ssl


# Constants
IP = "0.0.0.0"
PORT = 8820
PACKET_LEN_DATA = 32
CRT_FILE = "certificate.crt"
PRIVATE_KEY_FILE = "privateKey.key"
MSG = "hello, have a nice day"
EXIT_CODE = "exit"
EXIT_RESPONSE = "bye bye"


def main():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CRT_FILE, PRIVATE_KEY_FILE)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen()
        server_socket_tls = context.wrap_socket(server_socket, server_side=True)
        client_socket, client_addr = server_socket_tls.accept()
        print("New Connection With '%s:%s'" % (client_addr[0], client_addr[1]))
        try:
            msg = ""
            while msg != EXIT_RESPONSE:
                msg_len = client_socket.recv(32).decode()
                while "#" in msg_len:
                    msg_len = msg_len[:-1]
                msg = client_socket.recv(int(msg_len)).decode()
                print("[Client]:", msg)
                if msg == EXIT_CODE:
                    msg = EXIT_RESPONSE
                client_socket.send(str(len(msg)).ljust(32, "#").encode())
                client_socket.send(msg.encode())
                print("[Server]:", msg)
            print("Connection is over.")
        except socket.error as err:
            print(str(err))
        finally:
            client_socket.close()
    except socket.error as err:
        print(str(err))
    finally:
        server_socket.close()


if __name__ == '__main__':
    main()

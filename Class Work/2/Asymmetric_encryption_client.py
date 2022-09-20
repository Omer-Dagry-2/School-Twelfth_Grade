import socket
import ssl


# Constants
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8820
PACKET_LEN_DATA = 32
EXIT_CODE = "bye bye"


def main():
    context = ssl.create_default_context()
    # allow self signed certification
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket_tls = context.wrap_socket(my_socket, server_hostname=SERVER_IP)
    try:
        my_socket_tls.connect((SERVER_IP, SERVER_PORT))
        answer = ""
        while answer != EXIT_CODE:
            msg = input("Please Enter A Message To Send: ")
            print(str(len(msg)).ljust(32, "#"))
            my_socket_tls.send(str(len(msg)).ljust(32, "#").encode())
            my_socket_tls.send(msg.encode())
            answer_len = my_socket_tls.recv(PACKET_LEN_DATA).decode()
            while "#" in answer_len:
                answer_len = answer_len[:-1]
            answer = my_socket_tls.recv(int(answer_len)).decode()
            print("Server Sent:", answer)
        print("Connection Is Over.")
    except socket.error as err:
        print(str(err))
    finally:
        my_socket_tls.close()


if __name__ == '__main__':
    main()

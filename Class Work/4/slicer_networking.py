# -*- coding: utf-8 -*-
#!/usr/bin/python
import base64
import os
import random
import socket
import threading

from PIL import Image


l = ['aw==', 'bg==', 'dA==', 'aA==', 'bg==', 'Zw==', 'bw==', 'dw==', 'bg==', 'dA==', 'aQ==', 'bg==']
IMGS_PATH = "imgs" + os.sep
DEBUG = True


def server_init():
    """
    starts a server socket

    :return: 1 if socket is up 0 if not
    """
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        msg_print(socket.gethostname())
        server_socket.bind(("0.0.0.0", 5014))

        server_socket.listen(10)

        msg_print("Server Initialized !", "i")

        return server_socket

    except:
        return 1


def server_action(server):
    """
    starts to accept clients using threads
    :param server: socket object for server
    """
    msg_print("Listening  !", "i")

    while True:
        try:
            client_socket, address = server.accept()
            t = threading.Thread(target=thread_func, args=(client_socket,))
            t.start()
        except:
            continue


def thread_func(client):
    """
    checks for valid password and if valid sends all the data

    :param client: socket object for client connection
    """
    global l
    msg_print("Client Here", "i")
    indication = True
    client.send("[~] Enter SecretPhrase : ".encode())
    secret_phrase = client.recv(len(l)).decode()
    if len(secret_phrase) == len(l):
        for i in range(len(secret_phrase)):
            if base64.b64encode(secret_phrase[i].encode()).decode().strip('\n') != l[i]:
            # if secret_phrase[i].encode("base64").strip('\n') != l[i]:
                indication = False
                break

        if indication:
            sender(IMGS_PATH, sock=client)

    client.close()


def msg_print(msg, lvl="d"):
    """
    prints message if global DEBUG is true
    :param msg: message to print
    """
    global DEBUG
    if DEBUG:
        print("[%s] %s" % (lvl, repr(msg)))
    else:
        if lvl != "d":
            print("[%s] %s" % (lvl, repr(msg)))


def sender(load_path, send_all=True, sock=""):
    """
    generates random file order aggregates all files data in load_path directory and sends via sock socket
    :param send_all: flag sets a chunk base sender or send all at once
    :param sock: if "" prints list files else socket to send files to
    :param load_path: directory of chunk files
    """
    files = os.listdir(load_path)
    print(files)
    random.SystemRandom().shuffle(files)
    msg_print("Generated random files order %s" % repr(files))
    files_data = []
    print(len(files))

    for f in files:
        with open(load_path + f, "r") as reader:
            data = reader.read()
            files_data.append(data)
            if not send_all:
                msg_print("Sending file %s as chunk" % f)
                sock.sendall(data.encode())

    if send_all:
        msg_print("Got socket object sending data num packets %d" % len(files_data))
        sock.sendall("".join(files_data).encode())


if __name__ == '__main__':
    sock = server_init()
    while sock == 1:
        continue
    server_action(sock)

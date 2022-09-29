import datetime
import socket
import threading
from typing import *


# Constants
MD5_HASH = "EC9C0F7EDCC18A98B1F31853B1813301".lower()
IP = "0.0.0.0"
PORT = 8820
START = "0000000000"
END = "9999999999"
TOTAL = int(END) - int(START)
MAX_CLIENTS = 8  # 27

# Globals
lock = threading.RLock()
clients_sockets = []
clients_working_range = {}
ranges = []
md5_hash_result = None
s = int(START)
for i in range(MAX_CLIENTS):
    if i == MAX_CLIENTS - 1:
        ranges.append((str(s).rjust(10, "0"), str(END).rjust(10, "0"), "free"))
    else:
        ranges.append((str(s).rjust(10, "0"), str(s + TOTAL // MAX_CLIENTS).rjust(10, "0"), "free"))
        s += TOTAL // MAX_CLIENTS
del s, i


def start_server() -> socket.socket:
    server_socket = socket.socket()
    server_socket.bind((IP, PORT))
    print("Server Is Up!!")
    server_socket.listen()
    return server_socket


def accept_client(server_socket: socket.socket) -> Union[socket.socket, None]:
    global clients_sockets
    lock.acquire()
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except socket.error:
        lock.release()
        return None
    print("New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    clients_sockets.append(client_socket)
    lock.release()
    return client_socket


def wait_for_result_from_client(client_socket: socket.socket):
    """
    Waits For Client To Finish Work And If Another
    Client Has Finished It Will Tell The Others To Stop Work
    """
    global clients_sockets, clients_working_range, ranges, lock, md5_hash_result
    answer = None
    client_socket.settimeout(2)
    while answer is None:
        lock.acquire()
        if md5_hash_result is not None:
            try:
                client_socket.send("stop".encode())
            except ConnectionResetError:
                pass
            print("Sent Client stop, md5 hash result found.")
            answer = "not found."
            break
        lock.release()
        try:
            try:
                answer = client_socket.recv(10).decode()
                if answer in ["", "not found."] or len(answer) == 10:
                    break
            except socket.error:
                answer = None
        except ConnectionResetError:
            answer = ""
            break
    lock.acquire()
    if answer == "not found.":
        print("Client Sent not found.")
        range_ = clients_working_range[client_socket]
        if range_ in ranges:
            ranges.remove(range_)
            print("Removed Range:", range_[:-1], "No Result Found In The Range.")
    elif answer == "":
        print("Client Disappeared.")
        range_ = clients_working_range[client_socket]
        if range_ in ranges:
            ranges[ranges.index(range_)] = (range_[0], range_[1], "free")
            print("The Range", range_[:-1], "Is Available Again.")
        try:
            client_socket.close()
        except socket.error:
            pass
    elif answer != "" and answer != "not found.":
        md5_hash_result = answer
    lock.release()


def distribute_work_and_wait_for_result(client_socket: socket.socket):
    """
    Checks The Available Ranges And Gives The Client A Range To Work On
    Starts A Thread That Will Check On The Client
    """
    global clients_working_range, ranges
    lock.acquire()
    found = False
    for i in range(0, len(ranges)):
        possible_range = ranges[i]
        if possible_range[-1] == "free":
            found = True
            client_socket.send(possible_range[0].encode() + possible_range[1].encode())
            client_socket.send(MD5_HASH.encode())
            ranges[i] = (possible_range[0], possible_range[1], "taken")
            clients_working_range[client_socket] = (possible_range[0], possible_range[1], "taken")
            print("Gave Client Work, Range:", possible_range[0], "-", possible_range[1])
            break
    lock.release()
    if not found:
        client_socket.close()
        print("Didn't Found Work For Client. Connection Closed")
    else:
        t = threading.Thread(target=wait_for_result_from_client, args=(client_socket,), daemon=True)
        t.start()
        print("Started A Thread To Wait For The Client's Result.")


def main():
    global lock, md5_hash_result
    start_time = datetime.datetime.now()
    print("Start Time:", start_time)
    server_socket = start_server()
    while ranges:
        if True in [True if p_r[-1] == "free" else False for p_r in ranges]:
            client_socket = accept_client(server_socket)
            if client_socket is not None:
                distribute_work_and_wait_for_result(client_socket)
        lock.acquire()
        if md5_hash_result is not None:
            print("\n\n" + "-" * 64)
            print("Found Result:", md5_hash_result)
            print("-" * 64 + "\n")
            end_time = datetime.datetime.now()
            print(end_time)
            print("Time Passed:", end_time - start_time)
            lock.release()
            # wait until all the threads send their client to stop work
            while threading.active_count() > 1:
                pass
        try:
            lock.release()
        except RuntimeError:
            exit()


if __name__ == '__main__':
    main()

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
MAX_CLIENTS: int = 27

# Globals
dont_print: bool = False
lock = threading.RLock()
clients_sockets = []
clients_working_range = {}
ranges: list[tuple[str, str, str]] = []
md5_hash_result: Union[str, None] = None
s = int(START)
for j in range(MAX_CLIENTS):
    if j == MAX_CLIENTS - 1:
        ranges.append((str(s).rjust(10, "0"), str(END).rjust(10, "0"), "free"))
    else:
        ranges.append((str(s).rjust(10, "0"), str(s + TOTAL // MAX_CLIENTS).rjust(10, "0"), "free"))
        s += TOTAL // MAX_CLIENTS
del s, j


def print_(*args, sep=' ', end='\n', file=None):
    global dont_print
    if not dont_print:
        print(*args, sep=sep, end=end, file=file)


def start_server() -> socket.socket:
    server_socket = socket.socket()
    server_socket.bind((IP, PORT))
    print_("Server Is Up!!")
    server_socket.listen()
    return server_socket


def accept_client(server_socket: socket.socket) -> Union[socket.socket, None]:
    """ Try To Accept New Client And Add To Clients List """
    global clients_sockets
    lock.acquire()
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except (socket.error, ConnectionRefusedError):
        lock.release()
        return None
    print_("New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    clients_sockets.append(client_socket)
    lock.release()
    return client_socket


def wait_for_result_from_client(client_socket: socket.socket):
    """
    Waits For Client To Finish Work And If Another
    Client Has Finished It Will Tell The Others To Stop Work
    """
    global clients_working_range, ranges, lock, md5_hash_result
    answer = None
    client_socket.settimeout(2)
    last_check_in = datetime.datetime.now()
    while answer is None:
        lock.acquire()
        if md5_hash_result is not None:
            try:
                client_socket.send("stop".encode())
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                pass
            print_("Sent Client stop, md5 hash result found.")
            answer = "not found."
            lock.release()
            break
        lock.release()
        try:
            try:
                answer = client_socket.recv(10).decode()
                if answer == "working...":
                    last_check_in = datetime.datetime.now()
                    answer = None
                elif answer in ["", "not found."] or len(answer) == 10:
                    break
            except socket.error:
                answer = None
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
            answer = ""
            break
        if (datetime.datetime.now() - last_check_in).seconds >= 120:
            print_("'%s:%s' Didn't Check In For 120 Seconds, Closing Connection." % client_socket.getpeername())
            try:
                client_socket.send("stop".encode())
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                pass
            answer = ""
            break
    if answer == "not found.":
        lock.acquire()
        print_("'%s:%s' Sent not found." % client_socket.getpeername())
        range_ = clients_working_range[client_socket]
        if range_ in ranges:
            ranges.remove(range_)
            print_("Removed Range:", range_[:-1], "No Result Found In The Range.")
        lock.release()
    elif answer == "":
        lock.acquire()
        print_("'%s:%s' Disappeared." % client_socket.getpeername())
        range_ = clients_working_range[client_socket]
        if range_ in ranges:
            ranges[ranges.index(range_)] = (range_[0], range_[1], "free")
            print_("The Range", range_[:-1], "Is Available Again.")
        try:
            client_socket.close()
        except socket.error:
            pass
        lock.release()
    elif answer != "" and answer != "not found.":
        lock.acquire()
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
        possible_range: tuple[str, str, str] = ranges[i]
        if possible_range[-1] == "free":
            found = True
            try:
                client_socket.send(possible_range[0].encode() + possible_range[1].encode())
                client_socket.send(MD5_HASH.encode())
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                break
            ranges[i] = (possible_range[0], possible_range[1], "taken")
            clients_working_range[client_socket] = (possible_range[0], possible_range[1], "taken")
            print_("Gave '%s:%s' Work, Range:" % client_socket.getpeername(),
                   possible_range[0], "-", possible_range[1])
            break
    lock.release()
    if not found:
        try:
            client_socket.send("no work")
            client_socket.close()
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
            pass
        lock.acquire()
        print_("Didn't Found Work For '%s:%s' * OR * "
               "Socket Error When Trying To Send Work. Connection Closed" % client_socket.getpeername())
        lock.release()
    else:
        lock.acquire()
        t = threading.Thread(target=wait_for_result_from_client, args=(client_socket,), daemon=True)
        t.start()
        print_("Started A Thread To Wait For '%s:%s' Result."
               % client_socket.getpeername())
        lock.release()


def main():
    global lock, md5_hash_result, dont_print
    start_time = datetime.datetime.now()
    print_("Start Time:", start_time)
    server_socket = start_server()
    while ranges:
        if True in [True if p_r[-1] == "free" else False for p_r in ranges]:
            client_socket = accept_client(server_socket)
            if client_socket is not None:
                distribute_work_and_wait_for_result(client_socket)
        lock.acquire()
        if md5_hash_result is not None:
            print_("\n\n" + "-" * 64)
            print_("Found Result:", md5_hash_result)
            print_("-" * 64 + "\n")
            end_time = datetime.datetime.now()
            print_(end_time)
            print_("Time Passed:", end_time - start_time)
            dont_print = True
            lock.release()
            # wait until all the threads send their client to stop work
            while threading.active_count() > 1:
                pass
        try:
            lock.release()
        except RuntimeError:
            exit()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

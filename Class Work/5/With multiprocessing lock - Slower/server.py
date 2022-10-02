import datetime
import socket
import threading
import time
import tkinter
from tkinter import ttk
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
number_of_checked_options = 0
dont_print: bool = False
lock = threading.Lock()
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


def accept_client(server_socket: socket.socket) -> Union[tuple[socket.socket, tuple[str, str]], tuple[None, None]]:
    """ Try To Accept New Client And Add To Clients List """
    global clients_sockets
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except (socket.error, ConnectionRefusedError):
        return None, None
    lock.acquire()
    print_("New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    clients_sockets.append(client_socket)
    lock.release()
    return client_socket, client_socket.getpeername()


def update_status_gui(checked_options_label: tkinter.Label, checked_options_progress_bar: ttk.Progressbar):
    """ Update The Status GUI """
    global lock, number_of_checked_options, md5_hash_result
    while True:
        lock.acquire()
        num = number_of_checked_options
        lock.release()
        # if this thread and server thread are active, it means the GUI thread is closed
        if threading.active_count() == 2:
            break
        try:
            if md5_hash_result is not None:  # if result found
                value = 100  # 100%
                checked_options_label.config(text="Found The Hashed Data: " + str(md5_hash_result))  # display result
            else:  # else
                value = (num * 100) / 10000000000  # percentage
                checked_options_label.config(text="So Far %d Options Were Checked (%f"
                                                  % (num,
                                                     value) + "%)")  # update number of checked oprtions
            checked_options_progress_bar["value"] = value  # update progress bar
        except RuntimeError:  # GUI was closed
            break
        time.sleep(2)


def wait_for_result_from_client(client_socket: socket.socket, client_ip_port: tuple[str, str]):
    """
    Waits For Client To Finish Work And If Another
    Client Has Finished It Will Tell The Others To Stop Work
    """
    global clients_working_range, ranges, lock, md5_hash_result, number_of_checked_options
    answer = None
    client_socket.settimeout(2)
    last_check_in = datetime.datetime.now()
    client_count = 0
    while answer is None:
        lock.acquire()
        if md5_hash_result is not None:
            lock.release()
            try:
                client_socket.send("stop".encode())
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                pass
            lock.acquire()
            print_("Sent Client stop, md5 hash result found.")
            answer = "not found."
            lock.release()
            break
        lock.release()
        try:
            try:
                answer = client_socket.recv(32).decode()
                count = 0
                while len(answer) != 32 and count != 10:
                    answer += client_socket.recv(32 - len(answer)).decode()
                    count += 1
                    time.sleep(1)
                if len(answer) != 32:
                    answer = ""
                    break
                elif "checked" in answer and "more" in answer:
                    last_check_in = datetime.datetime.now()
                    checked_x_more_options = int(answer.split("hecked '")[1].split("' mo")[0])
                    client_count += checked_x_more_options
                    lock.acquire()
                    number_of_checked_options += checked_x_more_options
                    lock.release()
                    answer = None
                elif answer in ["", "not found.".rjust(32, " ")] or len(answer) == 32:
                    break
            except socket.error:
                answer = None
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
            answer = ""
            break
        if (datetime.datetime.now() - last_check_in).seconds >= 80:
            lock.acquire()
            print_("'%s:%s' Didn't Check In For 120 Seconds, Closing Connection." % client_ip_port)
            lock.release()
            try:
                client_socket.send("stop".encode())
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                pass
            answer = ""
            break
    if answer == "not found.".rjust(32, " "):
        lock.acquire()
        print_("'%s:%s' Sent not found." % client_ip_port)
        range_ = clients_working_range[client_socket]
        if range_ in ranges:
            ranges.remove(range_)
            print_("Removed Range:", range_[:-1], "No Result Found In The Range.")
        lock.release()
    elif answer == "":
        lock.acquire()
        number_of_checked_options -= client_count
        print_("'%s:%s' Disappeared." % client_ip_port)
        if client_socket in clients_working_range:
            range_ = clients_working_range[client_socket]
            if range_ in ranges:
                ranges[ranges.index(range_)] = (range_[0], range_[1], "free")
                print_("The Range", range_[:-1], "Is Available Again.")
        lock.release()
        try:
            client_socket.close()
        except socket.error:
            pass
    elif answer != "" and answer != "not found.".rjust(32, " "):
        while answer.startswith(" "):
            answer = answer[1:]
        lock.acquire()
        md5_hash_result = answer
        lock.release()


def distribute_work_and_wait_for_result(client_socket: socket.socket, client_ip_port: tuple[str, str]):
    """
    Checks The Available Ranges And Gives The Client A Range To Work On
    Starts A Thread That Will Check On The Client
    """
    global clients_working_range, ranges
    found = False
    lock.acquire()
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
            print_("Gave '%s:%s' Work, Range:" % client_ip_port,
                   possible_range[0], "-", possible_range[1])
            break
    lock.release()
    if not found:
        try:
            client_socket.send("no work".rjust(20, " ").encode())
            client_socket.close()
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
            pass
        lock.acquire()
        print_("Didn't Found Work For '%s:%s' * OR * "+
               "Socket Error When Trying To Send Work. Connection Closed" % client_ip_port)
        lock.release()
    else:
        t = threading.Thread(target=wait_for_result_from_client, args=(client_socket, client_ip_port), daemon=True)
        t.start()
        lock.acquire()
        print_("Started A Thread To Wait For '%s:%s' Result."
               % client_ip_port)
        lock.release()


def accept_new_client_and_check_for_result(start_time: datetime.datetime.now):
    global lock, md5_hash_result, dont_print, number_of_checked_options
    server_socket = start_server()
    while ranges:
        if True in [True if p_r[-1] == "free" else False for p_r in ranges]:
            client_socket, client_ip_port = accept_client(server_socket)
            if client_socket is not None:
                distribute_work_and_wait_for_result(client_socket, client_ip_port)
        lock.acquire()
        if md5_hash_result is not None:
            print_("\n\n" + "-" * 64)
            print_("Found Result:", md5_hash_result)
            print_("-" * 64)
            end_time = datetime.datetime.now()
            print_(end_time)
            print_("Time Passed:", end_time - start_time)
            print_("Total Checked Options: '%d'" % number_of_checked_options)
            print_("\nTo Close The Program Close The GUI Window.\nOr Press Ctrl + C")
            dont_print = True
            lock.release()
            break  # found answer stop work
        try:
            lock.release()
        except RuntimeError:
            pass
    server_socket.close()


def main():
    start_time = datetime.datetime.now()
    print_("Start Time:", start_time)
    accept_new_client_and_check_for_result_thread = threading.Thread(target=accept_new_client_and_check_for_result,
                                                                     args=(start_time,), daemon=True)
    accept_new_client_and_check_for_result_thread.start()
    # --------------- GUI ---------------
    global lock, number_of_checked_options
    status_gui = tkinter.Tk()
    status_gui.title("Status")
    lock.acquire()
    checked_options_label = tkinter.Label(status_gui,
                                          text="So Far %d Options Were Checked." % number_of_checked_options,
                                          font=("helvetica", 16))
    lock.release()
    checked_options_progress_bar = ttk.Progressbar(status_gui, orient=tkinter.HORIZONTAL,
                                                   length=300, mode="determinate")
    checked_options_label.pack(pady=10)
    checked_options_progress_bar.pack(pady=20)
    update_status_gui_thread = threading.Thread(target=update_status_gui,
                                                args=(checked_options_label, checked_options_progress_bar),
                                                daemon=True)
    update_status_gui_thread.start()
    status_gui.mainloop()
    print("GUI Closed")
    while accept_new_client_and_check_for_result_thread.is_alive():
        time.sleep(10)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt")

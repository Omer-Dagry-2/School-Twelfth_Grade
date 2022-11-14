import time
import queue
import socket
import datetime
import platform
import threading
import subprocess
import multiprocessing

from typing import *


# Constants
LOCAL_SERVER_IP = "0.0.0.0"
LOCAL_SERVER_PORT = 8821
IP = "127.0.0.1"
# IP = "10.100.102.10"
PORT = 8820
NUMBERS = "0123456789"
CPU_COUNT = multiprocessing.cpu_count()
# LEN_OF_MD5_HASHED_DATA: int = 10

# Globals
len_of_md5_hashed_data: int = 0
number_of_checked_options = 0
local_server_stop = False


def recv_full(sock: socket.socket, msg_len: int) -> str:
    """ Loop On recv Until Received msg_len bytes From The Server """
    sock.settimeout(2)
    data = ""
    res = None
    count = 0
    while len(data) != msg_len and res != "" and count != 10:
        try:
            res = sock.recv(msg_len - len(data)).decode()
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error) as err:
            if not isinstance(err, socket.error):
                sock.close()
                main()
                break
        if res is not None:
            data += res
        count += 1
        time.sleep(0.5)
    sock.settimeout(None)
    if res is None or res == "no work".rjust(20, " ") or res == "":
        print("Server Has No Work")
        exit()
    return data


def recv_range_and_hash_from_server(sock: socket.socket) -> tuple[int, int, str]:
    """ Receives The Range And MD5 hash From The Server """
    global len_of_md5_hashed_data
    # get my range
    my_range = recv_full(sock, 20)  # start_from (10 digits) & end_at (10 digits)
    start_from = int(my_range[:10])
    end_at = int(my_range[10:])
    md5_hash = recv_full(sock, 32).lower()  # the md5 hash (32 digit)
    len_of_md5_hashed_data = int(recv_full(sock, 32))
    if len_of_md5_hashed_data <= 0:
        print("Error Received Non Positive Value For The Len Of The MD5 Hashed Data")
        exit()
    return start_from, end_at, md5_hash


def brute_force_decrypt_md5(md5_hash: str, multiprocessing_queue: queue.Queue,
                            start_range: str, end_range: str):
    """
    The Brute Force Function
    Recursive Function, Runs From start_from To end_at including both.
    Sends A Signal If The Result Is Found
    Sends A Signal If Finished Range And Didn't Found Result
    """
    global len_of_md5_hashed_data
    # because this func runs in other processes the try except in the main process isn't
    # catching KeyboardInterrupt in these processes, so another try except is added here
    # so if the user closes the program it will exit without a bunch of errors
    try:
        system = platform.system()
        crack_md5_hash = r".\crack_md5.exe" if system == "Windows" else r".\crack_md5.bin" if system == "Linux" else ""
        if crack_md5_hash == "":
            raise ValueError("OS not supported.")
        process = subprocess.run(f"{crack_md5_hash} {md5_hash} {start_range} {end_range} {len_of_md5_hashed_data} "
                                 f"{'127.0.0.1'} {str(LOCAL_SERVER_PORT)}",
                                 shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = process.stdout.decode()
        endl = "\r\n"
        if "Hashed Data" in result:
            multiprocessing_queue.put(result.split('Hashed Data: ')[-1].split(endl)[0])
            # print(f"MD5 Hashed Data: '{result.split(': ')[-1].split(endl)[0]}'")
        elif "Result Not Found." in result:
            multiprocessing_queue.put("not found, stopped at '%s'" % end_range)
            # print(f"Not Found.")
        else:
            # print(f"Unexpected Result From Crack MD5 Process:\t{result}")
            multiprocessing_queue.put(f"Unexpected Result From Crack MD5 Process:\t{result}")
    except KeyboardInterrupt:
        pass


def local_server_count_number_of_options(local_server_sock: socket.socket,
                                         threading_lock: threading.Lock):
    global number_of_checked_options, local_server_stop
    client_socket, client_addr = local_server_sock.accept()
    while not local_server_stop:
        res = None
        try:
            res = client_socket.recv(10000000).decode()
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error) as err:
            if not isinstance(err, socket.error):
                try:
                    client_socket.shutdown(1)
                    client_socket.close()
                except socket.error:
                    pass
                break
        if res is None:
            continue
        elif res == "":
            try:
                client_socket.shutdown(1)
                client_socket.close()
            except socket.error:
                pass
            break
        how_many_1 = res.count("1") * 10000  # the c++ program send '1' for every 10000 iterations
        if how_many_1 > 0:
            threading_lock.acquire()
            number_of_checked_options += how_many_1
            threading_lock.release()
        if "2" in res:
            try:
                client_socket.shutdown(1)
                client_socket.close()
            except socket.error:
                pass
            break
    local_server_sock.close()


def main():
    system = platform.system()
    if system != "Windows":
        print("Currently Not Supported On Linux.")
        exit(1)
    #
    global number_of_checked_options, local_server_stop, len_of_md5_hashed_data
    print("Trying To Connect To The Server...")
    # open socket to server
    sock = socket.socket()
    try:
        sock.connect((IP, PORT))
    except ConnectionRefusedError:
        print("Can't Reach The Server.")
        exit()
    print("Connected To Server.")
    # recv data
    start_from, end_at, md5_hash = recv_range_and_hash_from_server(sock)
    if len_of_md5_hashed_data <= 0:
        print("Error Received Non Positive Value For The Len Of The MD5 Hashed Data")
        exit()
    print("Server Sent: "
          "Start From:", str(start_from).rjust(10, "0"),
          "| End At:", str(end_at).rjust(10, "0"),
          "| MD5 Hash To Brute Force:", md5_hash)
    # ------------------ just for testing, skip until result in range ------------------
    # if not start_from < 3735928559 < end_at:
    #     msg = "not found.".rjust(32, " ").encode()
    #     sent_amount = sock.send(msg)
    #     while sent_amount != 32:
    #         sent_amount += sock.send(msg[sent_amount:])
    #     sock.close()
    #     main()
    # ----------------------------------------------------------------------------------
    # communication with processes
    multiprocessing_queue = multiprocessing.Queue()
    # local server socket, to communicate with the processes
    threading_lock = threading.Lock()
    local_server_sock = socket.socket()
    local_server_sock.bind((LOCAL_SERVER_IP, LOCAL_SERVER_PORT))
    local_server_sock.listen()
    local_server_thread = threading.Thread(target=local_server_count_number_of_options,
                                           args=(local_server_sock, threading_lock),
                                           daemon=True)
    local_server_thread.start()
    time.sleep(2)
    #
    crack_md5_process = multiprocessing.Process(target=brute_force_decrypt_md5,
                                                args=(
                                                    md5_hash.lower(),
                                                    multiprocessing_queue,
                                                    str(start_from),
                                                    end_at,
                                                ),
                                                daemon=True)
    crack_md5_process.start()
    #
    #
    decrypted_md5_hash: Union[None, str] = None
    process_finished = False
    sock.settimeout(2)
    res = b""
    last_check_in = datetime.datetime.now()
    # wait until all processes finish and
    # the thread of the local server finish updating the global var of options count
    # and this main thread finish sending to the server the count
    while decrypted_md5_hash is None or local_server_thread.is_alive() or number_of_checked_options != 0:
        if decrypted_md5_hash is None:
            time.sleep(2)
        # send the server the amount of options that were checked since the last time we sent
        if (datetime.datetime.now() - last_check_in).seconds >= 8:
            try:
                threading_lock.acquire()
                num = number_of_checked_options
                number_of_checked_options = 0
                threading_lock.release()
                msg = ("checked '%d' more" % num).rjust(32, " ").encode()
                sent_amount = sock.send(msg)
                while sent_amount != 32:
                    sent_amount += sock.send(msg[sent_amount:])
                last_check_in = datetime.datetime.now()
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                print("Lost Connection To Server. Exiting.")
                crack_md5_process.close()
                sock.shutdown(1)
                sock.close()
                exit(0)
        #
        #
        # check if server sent stop msg
        try:
            res = sock.recv(4)
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error) as err:
            if not isinstance(err, socket.error):
                print("Lost Connection To Server. Exiting.")
                crack_md5_process.close()
                sock.shutdown(1)
                sock.close()
                exit(0)
        if res == b"stop":
            crack_md5_process.close()
            sock.shutdown(1)
            sock.close()
            exit(0)
        # check if the md5_hash was found
        if not crack_md5_process.is_alive() and decrypted_md5_hash is None:
            process_finished = True
            try:
                # check if the process sent the result or sent not found msg
                decrypted_md5_hash = multiprocessing_queue.get(timeout=5)
                if decrypted_md5_hash is not None and "not found" in decrypted_md5_hash:
                    print("Process Finished And Returned Not Found.")
                    decrypted_md5_hash = None
                elif "Unexpected Result From Crack MD5 Process" in decrypted_md5_hash:
                    print(decrypted_md5_hash)
                    sock.shutdown(1)
                    sock.close()
                    decrypted_md5_hash = None
                    local_server_stop = True
                    time.sleep(5)
                    exit(1)
                elif decrypted_md5_hash is not None:
                    print("\n\n" + "-" * 64)
                    print("Process Finished And Found The Hashed Data:", decrypted_md5_hash)
                    print("-" * 64 + "\n")
                    local_server_stop = True
                    break
            except queue.Empty:
                pass
        time.sleep(2)
    # sent result to server if found
    # else tell server that the range doesn't contain the result and
    # close connection to server and start again (a new range will be given)
    if decrypted_md5_hash is not None:
        try:
            msg = decrypted_md5_hash.rjust(32, " ").encode()
            sent_amount = sock.send(msg)
            while sent_amount != 32:
                sent_amount += sock.send(msg[sent_amount:])
            sock.shutdown(1)
            sock.close()
            print("MD5 Hash Result Sent To Server.")
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error):
            print("Couldn't Send Result To Server. Connection Error")
        exit()
    elif process_finished:
        print("Didn't Found Result In Range.")
        try:
            msg = "not found.".rjust(32, " ").encode()
            sent_amount = sock.send(msg)
            while sent_amount != 32:
                sent_amount += sock.send(msg[sent_amount:])
            sock.shutdown(1)
            sock.close()
            print("Sent 'Not Found' To Server.")
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error):
            print("Couldn't Send not found To Server. Connection Error")
            exit(0)
        while local_server_thread.is_alive():
            time.sleep(1)
        print("-" * 64)
        print("Starting Again.")
        try:
            main()
        except ConnectionError as err:
            print(str(err))
    else:
        sock.shutdown(1)
        sock.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print("\nReceived KeyboardInterrupt")

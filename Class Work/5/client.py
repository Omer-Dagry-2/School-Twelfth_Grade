import hashlib
import socket
import multiprocessing
import queue
from typing import *


IP = "127.0.0.1"
PORT = 8820
PACKET_LEN = 32
NUMBERS = "0123456789"
CPU_COUNT = multiprocessing.cpu_count()
LEN_OF_MD5_HASHED_DATA = 10


def recv_range_and_hash_from_server(sock: socket.socket) -> tuple[int, int, str]:
    """ Receives The Range And MD5 hash From The Server """
    # get my range
    my_range = sock.recv(20).decode()  # start_from (10 digits) & end_at (10 digits)
    start_from = int(my_range[:10])
    end_at = int(my_range[10:])
    md5_hash = sock.recv(32).decode().lower()  # the md5 hash (32 digit)
    return start_from, end_at, md5_hash


def brute_force_decrypt_md5(md5_hash: str, base_string_length: int, multiprocessing_queue: queue.Queue,
                            start_from: str, end_at: str, current_string: str = "") -> Union[str, None]:
    """
    The Brute Force Function
    Recursive Function, Runs From start_from To end_at including both.
    Sends A Signal If The Result Is Found
    Sends A Signal If Finished Range And Didn't Found Result
    """
    global NUMBERS
    # start from
    numbers = NUMBERS[NUMBERS.index(start_from[0]):]
    for number in numbers:
        if base_string_length > 1:
            # after 1 run do all the numbers
            if numbers.index(number) != 0:
                start_from = "0" * base_string_length
            res = brute_force_decrypt_md5(md5_hash, base_string_length - 1, multiprocessing_queue,
                                          start_from[1:], end_at, current_string=current_string + number)
            if res is not None and "stop" in res and base_string_length != 10:
                return res
            elif res is not None and "stop" in res:
                multiprocessing_queue.put("not found, stopped at '%s'" % res.split("top, ")[1])
                break
            elif res is not None and base_string_length != 10:
                return res
            elif res is not None:
                multiprocessing_queue.put(res)
                break
        else:
            current_string_ = current_string + number
            if hashlib.md5(current_string_.encode()).hexdigest().lower() == md5_hash.lower():
                return current_string_
            if current_string_ == end_at:
                return "stop, " + current_string_
    if base_string_length != 10:
        return None


def close_all_processes(processes):
    """ Kills All The Processes That Were Created """
    for p_ in processes:
        if p_ is not multiprocessing.current_process():
            p_.kill()
    print("killed all processes")


def main():
    # open socket to server
    sock = socket.socket()
    try:
        sock.connect((IP, PORT))
    except ConnectionRefusedError:
        print("Can't Reach The Server.")
        exit()
    # recv data
    start_from, end_at, md5_hash = recv_range_and_hash_from_server(sock)
    print("Server Sent: "
          "Start From:", str(start_from).rjust(10, "0"),
          "| End At:", str(end_at).rjust(10, "0"),
          "| MD5 Hash To Brute Force:", md5_hash)
    # if not start_from < 3735928559 < end_at:
    #     sock.send("not found.".encode())
    #     main()
    total = end_at - start_from
    processes = []
    # communication with processes
    multiprocessing_queue = multiprocessing.Queue()
    # open processes (the number of processes is the number of cores)
    # each process gets a portion of the range that the server has sent
    for i in range(CPU_COUNT):
        if i == CPU_COUNT - 1:
            p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                        args=(md5_hash.lower(), LEN_OF_MD5_HASHED_DATA, multiprocessing_queue,
                                              str(start_from).rjust(10, "0"),
                                              str(int(end_at)).rjust(10, "0")),
                                        daemon=True)
            p.start()
            processes.append(p)
            print("Process %d Range:" % (i + 1),
                  str(start_from).rjust(10, "0"), "-",
                  str(int(end_at)).rjust(10, "0"))
        else:
            p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                        args=(md5_hash.lower(), LEN_OF_MD5_HASHED_DATA, multiprocessing_queue,
                                              str(start_from).rjust(10, "0"),
                                              str(start_from + (total // CPU_COUNT)).rjust(10, "0")),
                                        daemon=True)
            p.start()
            processes.append(p)
            print("Process %d Range:" % (i + 1),
                  str(start_from).rjust(10, "0"), "-",
                  str(start_from + (total // CPU_COUNT)).rjust(10, "0"))
            start_from += (total // CPU_COUNT)
    # wait for processes to return the md5 message
    # or until all processes finish
    decrypted_md5_hash: Union[None, str]
    decrypted_md5_hash = None
    sock.settimeout(2)
    res = b""
    while processes and decrypted_md5_hash is None:
        for p in processes:
            # check if server sent to stop
            try:
                res = sock.recv(4)
            except socket.error:
                pass
            if res == b"stop":
                close_all_processes(processes)
                sock.close()
                exit()
            # check if there is a process that finished
            if not p.is_alive() and decrypted_md5_hash is None:
                try:
                    # check if the process sent the result or sent not found msg
                    decrypted_md5_hash = multiprocessing_queue.get(timeout=5)
                    if decrypted_md5_hash is not None and "not found" in decrypted_md5_hash:
                        print("Process Finished And Returned: Not Found.")
                        decrypted_md5_hash = None
                    else:
                        print("\n\n" + "-" * 64)
                        print("Process Finished And Found The Encrypted Data:", decrypted_md5_hash)
                        print("-" * 64 + "\n\n")
                        # got result close all other processes
                        close_all_processes(processes)
                except queue.Empty:
                    pass
                processes.remove(p)
    # sent result to server if found
    # else tell server that the range doesn't contain the result and
    # close connection to server and start again (a new range will be given)
    if decrypted_md5_hash is not None:
        sock.send(decrypted_md5_hash.encode())
        sock.close()
        print("MD5 Hash Result Sent To Server.")
        exit()
    else:
        sock.send("not found.".encode())
        sock.close()
        main()


if __name__ == '__main__':
    main()

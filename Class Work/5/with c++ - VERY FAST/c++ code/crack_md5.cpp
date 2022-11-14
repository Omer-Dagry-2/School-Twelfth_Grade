#include <iostream>     // input output
#include <algorithm>    // to convert the md5_hash to lower case
#include <string>       // string variable type
#include <thread>       // threading
#include "md5.h"        // md5 hash
// sleep function for windows/linux depending 
// on the system this code runs on
#ifdef LINUX
#include <unistd.h>
#endif
#ifdef WINDOWS
#include <windows.h>
#endif

#include "Socket.cpp"

using namespace std;

const int CORE_COUNT = thread::hardware_concurrency();

string md5_data = "";
int threads_finished[1000] = {};


void crack_md5(string md5_hash_lower, long long int start_range, 
                 long long int end_range, int md5_data_length, int thread_pos, Socket sock) {
    /*
        try all options from start_range to end_range
    */
    char msg[] = "1";
    string option_string;
    long long int option_num = start_range;
    int count = 0;
    for (option_num; option_num < end_range; option_num++) {
        if (count == 10000) {
            try {while (sock.send_(msg, 1) != 1);}
            catch (...) {}
            count = 0;
        }
        count++;
        option_string = to_string(option_num);
        while (option_string.length() < md5_data_length) option_string.insert(0, "0");
        if (md5(option_string) == md5_hash_lower) {
            md5_data = option_string;
            // char msg[10] = {};
            // strncpy(msg, option_string.c_str(), sizeof(msg));
            // sock.send_(msg, option_string.length());
            break;  // md5_hash found stop work
        }
        else if (md5_data != "") break;
    }
    threads_finished[thread_pos] = 1;  // change val to 1 (thread finished)
}



void sleep(int sleep_time_ms) {
    // cross-platform sleep function
    #ifdef LINUX
    usleep(sleep_time * 10000);
    #endif
    #ifdef WINDOWS
    Sleep(sleep_time);
    #endif
}


int main(int argc, char** argv) {
    // check input
    if (argc != 7) {
        cout << "\nIncorrect Input.\n"
             << ".\\main.exe md5_hash start_range end_rage md5_data_length local_server_ip local_server_port";
        return 1;
    }
    // socket for local server (take input from argv - local_server_ip, local_server_port)
    Socket sock(argv[5], argv[6], "TCP");
    //
    // take input from argv (md5_hash, start_range, end_range, md5_data_length)
    string md5_hash = argv[1];
    long long int start_range = atoll(argv[2]);
    const long long int end_range = atoll(argv[3]);
    const int md5_data_length = atoi(argv[4]);
    // calc the total options (end_range - start_range)
    const long long int total = end_range - start_range;
    // lower the md5_hash
    transform(md5_hash.begin(), md5_hash.end(), md5_hash.begin(),[](unsigned char c){ return tolower(c); });
    const string md5_hash_lower = md5_hash;
    /*
        create and start all threads and give each one a range
    */
    // create all the threads
    thread threads_list[1000] = {};
    for (int core = 1; core <= CORE_COUNT; core++) {
        if (core == CORE_COUNT) {
            threads_list[core - 1] = thread(crack_md5, md5_hash_lower, start_range, 
                                            end_range, md5_data_length, core - 1, sock);
            cout << start_range << " - " << end_range << endl;
        }
        else {
            threads_list[core - 1] = thread(crack_md5, md5_hash_lower, start_range, 
                                            start_range + total / CORE_COUNT - 1, 
                                            md5_data_length, core - 1, sock);
            cout << start_range << " - ";
            start_range += total / CORE_COUNT;
            cout << start_range << endl;
        }
        threads_list[core - 1].detach();
    }
    /*
        wait until all threads finish
        or until result is found
    */
    bool stop = false;
    while (md5_data == "" && !stop) {
        stop = true;
        for (int core = 0; core < CORE_COUNT; core++) {
            if (threads_finished[core] == 0) {stop = false; break;}
        }
        sleep(2000);
    }
    // check result and print out
    if (md5_data != "") cout << "Hashed Data: " << md5_data << endl;
    else cout << "Result Not Found." << endl;
    //
    try {
        char msg[] = "2";
        sock.send_(msg, 1);
    }
    catch (...) {

    }
    sock.close();
}

#include <iostream>
#include <string.h>
#include <string>
#include <stdio.h>
#ifdef _WIN32  // windows
    #define WIN32_LEAN_AND_MEAN
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <stdlib.h>
    #include <stdio.h>
    #pragma comment (lib, "Ws2_32.lib")
    #pragma comment (lib, "Mswsock.lib")
    #pragma comment (lib, "AdvApi32.lib")
#else  // linux
    #include <sys/socket.h>
    #include <arpa/inet.h>
    #include <netdb.h>
    #include <unistd.h>
    #include <sys/types.h>
#endif

using namespace std;

class Socket {
    private:
        // Windows
        #ifdef _WIN32
        int sock_type = {};
        int sock_protocol = {};
        SOCKET sock = {};
        struct addrinfo *result = NULL,
                        *ptr = NULL,
                        hints;
        int iResult = {};
        // Linux
        #else
        throw runtime_error("Linux Is Not Supported Yet.\n")
        int sock = {};
        #endif
        //
        char *host_addr = {};
        char *port = {};
        bool closed = false;
        //
        //
        void connect_windows(PADDRINFOA result) {
            #ifdef _WIN32  // Windows
            for(ptr=result; ptr != NULL ;ptr=ptr->ai_next) {
                // Create a SOCKET for connecting to server
                this->sock = socket(ptr->ai_family, ptr->ai_socktype, ptr->ai_protocol);
                if (this->sock == INVALID_SOCKET) {
                    WSACleanup();
                    throw runtime_error("socket failed with error: " + to_string(WSAGetLastError()) + "\n");
                }

                // Connect to server.
                this->iResult = connect( this->sock, ptr->ai_addr, (int)ptr->ai_addrlen);
                if (this->iResult == SOCKET_ERROR) {
                    closesocket(this->sock);
                    this->sock = INVALID_SOCKET;
                    continue;
                }
                break;
            }
            freeaddrinfo(result);
            if (this->sock == INVALID_SOCKET) {
                WSACleanup();
                throw runtime_error("Unable to connect to server!\n");
            }
            #else  //Linux
                // TODO connect Linux socket
            #endif
        }
    public:
        Socket(char *host_addr, char *port, string type) {
            this->host_addr = host_addr;
            this->port = port;

            // init the socket
            #ifdef _WIN32
                if (type == "TCP") this->sock_type = SOCK_STREAM;
                else if (type == "UDP") this->sock_type = SOCK_DGRAM;
                else throw runtime_error("Unknown/Not-supported protocol\n");
                if (this->sock_type == SOCK_STREAM) this->sock_protocol = IPPROTO_TCP;
                else this->sock_protocol = IPPROTO_UDP;
                WSADATA wsaData;
                this->sock = INVALID_SOCKET;
                // Initialize Winsock
                this->iResult = WSAStartup(MAKEWORD(2,2), &wsaData);
                if (this->iResult != 0) {
                    throw runtime_error("WSAStartup failed with error: " + to_string(this->iResult) + "\n");
                }
                ZeroMemory( &hints, sizeof(hints) );
                this->hints.ai_family = AF_UNSPEC;
                this->hints.ai_socktype = this->sock_type;
                this->hints.ai_protocol = this->sock_protocol;
                // Resolve the server address and port
                this->iResult = getaddrinfo(this->host_addr, this->port, &hints, &result);
                if ( this->iResult != 0 ) {
                    WSACleanup();
                    throw runtime_error("getaddrinfo failed with error: " + to_string(this->iResult) + "\n");
                }
                this->connect_windows(result);
            #else
                throw runtime_error("Linux Is Not Supported Yet.\n")
                if (protocol == "TCP") this->type = SOCK_STREAM;
                else if (protocol == "UDP") this->type = SOCK_DGRAM;
                else throw runtime_error("Unknown/Not-supported protocol\n");
                this->sock = socket(AF_INET, this->type, 0);
                if (this->sock == -1) throw runtime_error("socket creation error\n");
            #endif
        }
        ~Socket() {
            if (! this->closed) this->close();
    }
    int recv_(char buff[], int len, int flags) {
        #ifdef _WIN32
        int r = recv(this->sock, buff, len, flags);
        if (r < 0) throw runtime_error("recv failed with error: " + to_string(WSAGetLastError()) + "\n");
        return r;
        #else
        //return recv()
        #endif
    }
    int send_(char msg[], int len, int flags=0) {
        #ifdef _WIN32
        int s = send(this->sock, msg, len, flags);
        if (s == SOCKET_ERROR) {
            this->close();
            throw runtime_error("send failed with error: " + to_string(WSAGetLastError()) + "\n");
        }
        return s;
        #else
        //return send()
        #endif
    }
    int close() {
        if (this->closed) throw runtime_error("Can't Close A Socket More Than 1 Time.");
        int status = 0;
        #ifdef _WIN32
            this->wsa_cleanup();
            status = shutdown(this->sock, SD_BOTH);
            if (status == 0) { status = closesocket(this->sock); }
        #else
            status = shutdown(this->sock, SHUT_RDWR);
            if (status == 0) { status = close(this->sock); }
        #endif
        this->closed = true;
        return status;
    }
    private:
        int wsa_cleanup() {
            #ifdef _WIN32  // Windows
                return WSACleanup();
            #endif
        }
};


// int main() {
//     char host_addr[] = "127.0.0.1";
//     char port[] = "8820";
//     Socket sock(host_addr, port, "TCP");
//     //
//     char msg[] = "HEAD / HTTP/1.0\r\n\r\n";
//     if (! sock.send_(msg, sizeof(msg))) throw runtime_error("socked send error\n");
//     //
//     char buff[4096] = {};
//     int received = 0;
//     Sleep(10000);
//     while (received < 6) received += sock.recv_(buff, 6, 0);
//     printf("buffer: %s\n", buff);
//     return 0;
// }
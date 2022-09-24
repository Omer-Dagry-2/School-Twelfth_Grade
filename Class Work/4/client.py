import socket
# import base64


sock = socket.socket()
sock.settimeout(5)

sock.connect(("127.0.0.1", 5014))

expected = "[~] Enter SecretPhrase : "
answer = ""
while answer != expected:
    answer += sock.recv(1).decode()

# l = ['aw==', 'bg==', 'dA==', 'aA==', 'bg==', 'Zw==', 'bw==', 'dw==', 'bg==', 'dA==', 'aQ==', 'bg==']
# l_dict = {}
# for key in l:
#     l_dict[key] = ""
#
# for key in l_dict:
#     for value in range(0, 1114111):
#         try:
#             if base64.b64encode(chr(value).encode()).decode().strip('\n') == key:
#                 l_dict[key] = chr(value)
#                 break
#         except UnicodeError:
#             pass
#
# for key in l:
#     print(l_dict[key], end="")
password = "knthngowntin"
sock.send(password.encode())

answer = ""
res = None
while res != "":
    res = sock.recv(1).decode()
    answer += res

# print(answer)
# print(len(answer))
# print(answer.count("<chunk number:"))


files_list = answer.split("<chunk number:")
while "" in files_list:
    files_list.remove("")
files_dict = {}
for file in files_list:
    files_dict[file[:file.index(">")]] = file[file.index(">") + 1:]

print(files_dict)

data = ""
for i in range(0, len(files_dict)):
    data += files_dict[str(i).rjust(2, "0")]

with open("result.png", "wb") as f:
    f.write(data.encode())


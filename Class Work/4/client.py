import socket


sock = socket.socket()
sock.settimeout(5)

sock.connect(("127.0.0.1", 5014))

expected = "[~] Enter SecretPhrase : "
answer = ""
while answer != expected:
    answer += sock.recv(1).decode()

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


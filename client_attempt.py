import socket

s = socket.socket()

def client_auth(s):
    msg = s.recv(1024)
    print(msg)
    username = raw_input()
    s.send(username)
    msg = s.recv(1024)
    print(msg)
    passwd = raw_input()
    s.send(passwd)
    return 0

port = 10101
s.connect(('127.0.0.1', port))
print(s.recv(1024))
s.send("Thanks.")
auth = client_auth(s)
s.close()

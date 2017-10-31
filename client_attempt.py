import socket

s = socket.socket()

def client_auth(s):
    msg = s.recv(1024)
    if msg == "Authenticated":
        return 1
    elif msg == "Authentication failed":
        return 0
    print(msg)
    username = raw_input()
    s.send(username)
    msg = s.recv(1024)
    print(msg)
    passwd = raw_input()
    s.send(passwd)
    return client_auth(s)

port = 10101
s.connect(('127.0.0.1', port))
print(s.recv(1024))
s.send("Thanks.")
auth = client_auth(s)
if auth:
    while True:
        msg = raw_input()
        print(msg)
        if len(msg) > 2:
            s.send(msg)
        else:
            break
            
s.close()

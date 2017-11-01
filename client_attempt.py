import socket
import select
import sys

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

def client_func(auth, s):
    if auth:
        # this part of the code is inspired by
        # http://www.geeksforgeeks.org/simple-chat-room-using-python/
        while True:
            recv_from = [s, sys.stdin]
            read_socks, write_socks, _ = select.select(recv_from, [], [])
            
            for sock in read_socks:
                if sock == s:
                    msg = sock.recv(1024)
                    print("<server> ", msg)
                else:
                    msg = sys.stdin.readline()
                    if msg.strip() == 'exit':
                        return
                    elif len(msg) > 2:
                        print("<me> ", msg)
                        s.send(msg)
                

client_func(auth, s)
s.close()

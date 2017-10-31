import socket

s = socket.socket()

port = 10101
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', port))
s.listen(5)

def authenticate(c, addr):
    c.send("Please enter your username.")
    username = c.recv(1024)
    print(username)
    c.send("Please enter your password.")
    passwd = c.recv(1024)
    print(passwd)
    return 0

while True:
    c, addr = s.accept()
    print("accepted connection from " + str(addr))
    c.send("You have been connected to the server.")
    print(c.recv(1024))
    auth = authenticate(c, addr);
    c.close()

    

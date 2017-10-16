import socket

s = socket.socket()

port = 10101
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', port))
s.listen(5)

while True:
    c, addr = s.accept()
    print("accepted connection from " + str(addr))
    c.send("You have been connected to the server.")
    c.close()

    

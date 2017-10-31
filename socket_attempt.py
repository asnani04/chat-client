import socket

class Server(object):
    """
    Class to implement a basic chat server
    """

    def __init__(self, port):
        self.s = socket.socket()
        self.port = port

    def connect(self, auth_file):
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', self.port))
        self.s.listen(5)
        self.auth_file = auth_file

    def auth_check(self, username, passwd):
        fid = open(self.auth_file, "r")
        for line in fid.readlines():
            un, pw = line.strip().split(" ")
            print(un, pw)
            if un == username and pw == passwd:
                return 1
        return 0
    
    def server_auth(self, c, addr, attempts=3):
        if attempts == 0:
            return 0
        c.send("Please enter your username.")
        username = c.recv(1024)
        print(username)
        c.send("Please enter your password.")
        passwd = c.recv(1024)
        print(passwd)
        valid = self.auth_check(username, passwd)
        if valid == 1:
            return 1
        else:
            self.server_auth(c, addr, attempts-1)

    def serve(self):
        while True:
            c, addr = self.s.accept()
            print("accepted connection from " + str(addr))
            c.send("You have been connected to the server.")
            print(c.recv(1024))
            auth = self.server_auth(c, addr);
            if auth == 1:
                print("Client successfully authenticated")
            else:
                # do something to stop the ip from trying to log in for some time
                pass
            c.close()


port = 10101
auth_file = "./auth_keys.txt"
server = Server(port)
server.connect(auth_file)
server.serve()



    

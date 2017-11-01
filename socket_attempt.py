import socket
import thread
import select

class Server(object):
    """
    Class to implement a basic chat server
    """

    def __init__(self, port):
        self.s = socket.socket()
        self.port = port
        self.active_clients = {}

    def connect(self, auth_file):
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('', self.port))
        self.s.listen(5)
        self.auth_file = auth_file

    def auth_check(self, username, passwd):
        """
        Check if the username, password corresponds to a valid user
        returns: 1 if such a user is found, 0 if not
        """
        fid = open(self.auth_file, "r")
        for line in fid.readlines():
            un, pw = line.strip().split(" ")
            # print(un, pw)
            if un == username and pw == passwd:
                return 1
        return 0
    
    def server_auth(self, c, addr, attempts=3):
        """
        Authentication handled by the server. attempts indicates the number of 
        attempts left for this particular client.
        """
        if attempts == 0:
            return [0, '']
        c.send("Please enter your username.")
        username = c.recv(1024)
        print(username)
        c.send("Please enter your password.")
        passwd = c.recv(1024)
        print(passwd)
        valid = self.auth_check(username, passwd)
        if valid == 1:
            return [1, username]
        else:
            return self.server_auth(c, addr, attempts-1)

    def client_thread(self, client, addr, username):
        """
        Separate thread for each client connected to the chat room
        """
        while True:
            try:
                msg = client.recv(1024)
                if msg:
                    print(username + " sent: ", msg)
                    recver, msg = msg.strip().split(">")
                    if recver.strip() == 'broadcast':
                        # broadcast message to all users
                        # print("broadcast message")
                        for client in self.active_clients.keys():
                            if client != username:
                                self.active_clients[client].send(msg.strip())
                                
                    else:
                        # send message to a specified username
                        try:
                            recver = recver.strip()
                            recv_sock = self.active_clients[recver]
                            print("recv_sock: ", recv_sock)
                            # read_sock, write_sock, _ = select.select(
                            #     [recv_sock], [], [], 2)
                            bytes_sent = recv_sock.send(msg.strip())
                            if bytes_sent > 0:
                                print("msg sent to user " + recver)
                            else:
                                print("user " + recver + " is offline")
                                self.active_clients.pop(recver, None)
                        except:
                            print("msg couldn't be sent to user " + recver)
                            fid = open(self.auth_file, "r")
                            found = 0
                            for line in fid.readlines():
                                un, pw = line.strip().split(" ")
                                if un == recver:
                                    print("user " + un + " is offline")
                                    found = 1
                                    break
                                    # code to send message to recver offline
                            if found == 0:
                                print("user " + recver + " doesn't exist")
            except:
                continue
        return 0
        
    def serve(self):
        while True:
            c, addr = self.s.accept()
            print("accepted connection from " + str(addr))
            c.send("You have been connected to the server.")
            print(c.recv(1024))
            auth = self.server_auth(c, addr);
            if auth[0] == 1:
                print("Client successfully authenticated")
                c.send("Authenticated")
                self.active_clients[auth[1]] = c
                thread.start_new_thread(self.client_thread, (c, addr, auth[1]))
            else:
                # do something to stop the ip from trying to log in for some time
                c.send("Authentication failed")
                continue
        c.close()
        self.s.close()


port = 10101
auth_file = "./auth_keys.txt"
server = Server(port)
server.connect(auth_file)
server.serve()



    

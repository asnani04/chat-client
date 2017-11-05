import socket
import thread
import select
import os

class Server(object):
    """
    Class to implement a basic chat server
    """

    def __init__(self, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        self.active_clients = {}
        self.block_list = {}

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
        # display messages that came when this user was offline
        filename = username + ".txt"
        if os.path.isfile("./" + filename):
            fid_un = open(username + ".txt", "r")
            for line in fid_un.readlines():
                client.send(line)
            fid_un.close()
        open(filename, "w").close()
        # check for incoming messages and send outgoing messages
        while True:
            try:
                msg = client.recv(1024)
                if not msg:
                    client.close()
                    print("user " + username + " is offline") 
                    self.active_clients.pop(username, None)
                    break
                else:
                    print(username + " sent: ", msg)
                    long_msg = msg.strip().split(">")
                    if len(long_msg) == 2:
                        recver, msg = long_msg[0], long_msg[1]
                    else:
                        recver, msg = "", long_msg[0]
                    if recver.strip() == 'broadcast':
                        # broadcast message to all users
                        for client in self.active_clients.keys():
                            if client != username:
                                self.active_clients[client].send(msg.strip())

                    # loop to take care of whoelse messages
                    elif msg.strip() == "whoelse":
                        for user in self.active_clients.keys():
                            if user != username:
                                client.send("user " + user + " is active.\n")

                    # request to block a user
                    elif msg.split(" ")[0].strip() == "block":
                        cmd, tgt = msg.split(" ")
                        print("blocking a user " + tgt.strip())
                        if username in self.block_list:
                            self.block_list[username].append(tgt.strip())
                        else:
                            self.block_list[username] = [tgt.strip()]
                        client.send("user " + tgt + " has been blocked.\n")

                    # request to unblock a user
                    elif msg.split(" ")[0].strip() == "unblock":
                        cmd, tgt = msg.split(" ")
                        if username in self.block_list:
                            print("unblocking " + tgt.strip())
                            self.block_list[username].remove(tgt.strip())
                            client.send(
                                "user " + tgt + " has been unblocked.\n")
                        else:
                            client.send(
                                "user " + tgt + " was already unblocked.\n")
                        
                    else:
                        # send message to a specified username
                        recver = recver.strip()
                        if recver in self.block_list:
                            if username in self.block_list[recver]:
                                client.send(
                                    "Sorry, user " + recver + " has blocked you from sending messages to them.\n")
                                continue
                            
                        if recver in self.active_clients:
                            recv_sock = self.active_clients[recver]
                            msg = username + " > " + msg.strip()    
                            bytes_sent = recv_sock.send(msg)
                        else:
                            print("msg couldn't be sent to user " + recver)
                            fid = open(self.auth_file, "r")
                            found = 0
                            for line in fid.readlines():
                                un, pw = line.strip().split(" ")
                                if un == recver:
                                    fid_un = open(un + ".txt", "a")
                                    fid_un.write(
                                        username + " > " + msg.strip() + "\n")
                                    fid_un.close()
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



    

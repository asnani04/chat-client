import socket
import thread
import select
import os
import time
import numpy as np

class Game(object):
    """
    A tic-tac-toe game
    """
    def __init__(self, p1, p2):
        self.players = [p1, p2]
        self.state = np.zeros([3, 3], dtype=np.float32)
        self.turn = 0

    def move(self, player, row, col):
        """
        player plays a move at [row, col]
        """
        row, col = int(row), int(col)
        if self.turn != self.players.index(player.strip()):
            return 0
        if row not in range(0, 3):
            return 0
        if col not in range(0, 3):
            return 0
        if player not in self.players:
            return 0
        if self.state[row][col] != 0:
            return 0
        p_id = self.players.index(player)
        if p_id == 0:
            self.state[row, col] = 1.0
        else:
            self.state[row, col] = -1.0
        self.turn = 1 - self.turn
        return 1

    def check_for_victory(self):
        """
        check if some player has already won the game
        """
        sums = []
        sums.extend(np.sum(self.state, 0))
        sums.extend(np.sum(self.state, 1))
        sums.append(np.sum(np.diagonal(self.state)))
        sums.append(np.trace(np.flip(self.state, 1)))
        if 3.0 in sums:
            return self.players[0]
        elif -3.0 in sums:
            return self.players[1]
        return "not ended"

    def to_string(self):
        """
        Send the game state as a string.
        """
        game_as_string = str(self.state[0,0]) + " | " + str(self.state[0,1]) + " | " + str(self.state[0,2]) + "\n"
        game_as_string = game_as_string + str(self.state[1,0]) + " | " + str(self.state[1,1]) + " | " + str(self.state[1,2]) + "\n"
        game_as_string = game_as_string + str(self.state[2,0]) + " | " + str(self.state[2,1]) + " | " + str(self.state[2,2])
        return game_as_string

class Server(object):
    """
    Class to implement a basic chat server
    """

    def __init__(self, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        self.active_clients = {}
        self.block_list = {}
        self.blocked_conns = {}
        self.last_login = {}
        self.games = {}

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
        if username in self.active_clients:
            return 0
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
                    self.last_login[username] = time.time()
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
                        for cl in self.active_clients.keys():
                            if cl != username:
                                self.active_clients[cl].send(msg.strip())

                    # loop to take care of whoelse messages
                    elif msg.strip() == "whoelse":
                        for user in self.active_clients.keys():
                            if user != username:
                                client.send("user " + user + " is active.\n")

                    elif msg.strip() == "wholasthr":
                        print("who last here called.", self.last_login)
                        for user in self.last_login:
                            print(user)
                            if self.last_login[user] + 3600.0 > time.time():
                                client.send("user " + user + " was active within the last one hour.")

                    elif "playgame" in msg.strip():
                        blocks = msg.split(" ")
                        if len(blocks) == 3:
                            tgt, ans = blocks[1].strip(), blocks[2].strip()
                            if tgt not in self.active_clients:
                                client.send(tgt + " has gone offline. Maybe some other time.")
                                continue
                            if ans == "yes":
                                game = Game(tgt, username)
                                self.games[tgt + "," + username] = game
                                tgtmsg = username + " has agreed for a game with you. Let it begin!"
                                self.active_clients[tgt].send(tgtmsg)
                                tgtmsg = "To make a move, send 'move <row> <col> <opponent>' to make your mark at [row, col]"
                                self.active_clients[tgt].send(tgtmsg)
                                srcmsg = "Acknowledgement sent to " + tgt
                                client.send(srcmsg)
                            else:
                                self.active_clients[tgt].send("Sorry, your game request was not approved.")
                        elif len(blocks) == 2:
                            tgt = msg.split(" ")[1].strip()
                            print(username + " wants to start a game with " + tgt)
                            if tgt in self.active_clients:
                                tgtmsg = username + " wants to start a game with you. Are you in for it? (playgame " + username + " yes/no)" 
                                self.active_clients[tgt].send(tgtmsg)
                                srcmsg = "Your request for a game has been sent to " + tgt
                                client.send(srcmsg)
                            else:
                                client.send("This user is either offline or does not exist.")

                    elif "move" in msg.strip():
                        command, row, col, tgt = msg.split(" ")
                        row, col, tgt = row.strip(), col.strip(), tgt.strip()
                        game_str = username + "," + tgt
                        if game_str not in self.games:
                            game_str = tgt + "," + username
                        if game_str not in self.games:
                            client.send("Sorry, no such game exists. Send playgame <player> to start a game with 'player'.")
                            continue
                        result_move = self.games[game_str].move(username, row, col)
                        if result_move == 0:
                            client.send("Sorry, this move could not be played. Make a separate move.")
                            client.send(self.games[game_str].to_string())
                        else:
                            client.send("Move played.")
                            client.send(self.games[game_str].to_string())
                            print tgt
                            
                            victory = self.games[game_str].check_for_victory()
                            print victory
                            tgt = tgt.strip()
                            if tgt.strip() in self.active_clients:
                                print("tgt exists, ", tgt)
                                # self.active_clients[tgt].send(" test message for a move.")
                                self.active_clients[tgt].send(username + " played a move.")
                                self.active_clients[tgt].send(self.games[game_str].to_string())
                                self.active_clients[tgt].send("To make a move, send 'move <row> <col> <opponent>' to make your mark at [row, col]")
                                if victory != "not ended":
                                    self.active_clients[tgt].send(username + " has already won. Better luck next time.")
                            if victory == username:
                                client.send("Congratulations! You have won.")
                                self.games.pop(game_str, None)
                        
                        
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
                            msg = username + " sent '" + msg.strip() + "'"    
                            bytes_sent = recv_sock.send(msg)
                            client.send("Message delivered to " + recver + ".")
                        else:
                            print("msg couldn't be sent to user " + recver)
                            fid = open(self.auth_file, "r")
                            found = 0
                            for line in fid.readlines():
                                un, pw = line.strip().split(" ")
                                if un == recver:
                                    fid_un = open(un + ".txt", "a")
                                    fid_un.write(
                                        username + " sent '" + msg.strip() + "'\n")
                                    fid_un.close()
                                    print("user " + un + " is offline")
                                    offline_msg = "user " + un + " is offline. Your message will be delivered as soon as they come online."
                                    client.send(offline_msg)
                                    found = 1
                                    break
                                    # code to send message to recver offline
                            if found == 0:
                                no_exist_msg = "user " + recver + " doesn't exist"
                                print(no_exist_msg)
                                client.send(no_exist_msg)
            except:
                continue
        return 0
        
    def serve(self):
        while True:
            c, addr = self.s.accept()
            print("accepted connection from " + str(addr))
            if addr[0] in self.blocked_conns:
                if time.time() <= 20.0 + self.blocked_conns[addr[0]]:
                    c.send("You have been blocked. Please try again later.")
                    continue
                else:
                    self.blocked_conns.pop(addr[0], None)
            c.send("You have been connected to the server.")
            print(c.recv(1024))
            auth = self.server_auth(c, addr);
            if auth[0] == 1:
                print("Client successfully authenticated")
                c.send("Authenticated.\nPlease send user > msg to send msg to user.")
                self.active_clients[auth[1]] = c
                thread.start_new_thread(self.client_thread, (c, addr, auth[1]))
            else:
                # do something to stop the ip from trying to log in for some time
                self.blocked_conns[addr[0]] = time.time()
                c.send("Authentication failed")
                continue
        c.close()
        self.s.close()


port = 10101
auth_file = "./auth_keys.txt"
server = Server(port)
server.connect(auth_file)
server.serve()



    

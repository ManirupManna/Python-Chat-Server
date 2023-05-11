import socket
import threading
class Server:
    def __init__(self):
        self.host = "localhost"
        self.port = 8000
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.connectionRequests = {}
        self.lock = threading.Lock()
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"Server started, Listening on {self.host}, {self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"new client joined : {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        username = client_socket.recv(1024).decode()
        self.lock.acquire()
        try:
            while(username in self.clients.keys()):
                client_socket.send(f"Username {username} is already taken, try using some other username. \n".encode())
                username = client_socket.recv(1024).decode()
            self.clients[username] = {"socket": client_socket, "engaged":False, "connected_with":"none"}
            # self.broadcast(f"[Server]: {username} is online".encode())
            print(f"\n[Server]: {username} is online")
            self.lock.release()
            while True:
                try:
                    command = client_socket.recv(1024).decode()
                    #client exited the connection with the server
                    if(not command):
                        print(f"{username} went offline")
                        self.lock.acquire()
                        try:
                            if(self.clients[username]["engaged"]):
                                other_user = self.clients[username]["connected_with"]
                                other_user_socket = self.clients[other_user]["socket"]
                                self.clients[other_user]["engaged"] = False
                                self.clients[other_user]["connected_with"] = "none"
                                del self.clients[username]
                                self.lock.release()
                                other_user_socket.send(f"connection with {username} ended\n".encode())
                            else:
                                del self.clients[username]
                                self.lock.release()
                        except Exception as e:
                            print(e)
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                        break
                    #client declined connection request
                    if(command.upper()=="N"):
                        self.lock.acquire()
                        try:
                            if(username in self.connectionRequests.keys()):
                                other_user = self.connectionRequests[username]
                                del self.connectionRequests[username]
                                other_user_socket = self.clients[other_user]["socket"]
                                self.lock.release()
                                other_user_socket.send(f"{username} declined your connection request".encode())
                            else:
                                self.lock.release()
                                client_socket.send("You are not requested for any connection".encode())
                        except Exception as e:
                            print(e)
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                        continue
                    #client accepted connection request
                    elif(command.upper()=="Y" and self.connectionRequests.get(username)!=None):
                        self.lock.acquire()
                        try:
                            other_user = self.connectionRequests[username]
                            self.clients[username]["engaged"] = True
                            self.clients[username]["connected_with"] = other_user
                            self.clients[other_user]["engaged"] = True
                            self.clients[other_user]["connected_with"] = username
                            del self.connectionRequests[username]
                            self.lock.release()
                            self.clients[username]["socket"].send(f"Connected with {other_user}".encode())
                            self.clients[other_user]["socket"].send(f"Connected with {username}".encode())
                        except Exception as e:
                            print(e)
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                    #client requested for connection
                    elif(command=="connect"):
                        self.lock.acquire()
                        try:
                            if(self.clients[username]["engaged"]): #client is already connected with some other client
                                connected_with = self.clients[username]["connected_with"]
                                self.lock.release()
                                client_socket.send(f"You are already connected with {connected_with}, first break the connection then create new connection".encode())
                                continue
                        except Exception as e:
                            print(e)
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                        client_socket.send("Enter username: \n".encode()) #client is asked for the username with whom it wants to connect
                        other_user = client_socket.recv(1024).decode()
                        if(other_user==username): #client entered it's own username
                            client_socket.send("You can't connect with yourself\n".encode())
                            continue
                        #other client is available
                        self.lock.acquire()
                        try:
                            if(other_user in self.clients.keys()):
                                if(self.clients[other_user]["engaged"]):
                                    self.lock.release()
                                    client_socket.send(f"{other_user} is busy with someone else\n".encode())
                                else:
                                    self.connectionRequests[other_user] = username
                                    other_user_socket = self.clients[other_user]["socket"]
                                    self.lock.release()
                                    other_user_socket.send(f"{username} wants to connect with you (y/n): \n".encode()) #other client is requested for accepting or declining connection request

                            else: #other_client is not connected with server
                                self.lock.release()
                                client_socket.send(f"{other_user} is not online".encode())
                        except Exception as e:
                            print(e)
                            break
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                    elif(command=='exit'): #client exiting the existing chat with other client
                        self.lock.acquire()
                        try:
                            if(not self.clients[username]["engaged"]): #client is not in chat with anyone
                                self.lock.release()
                                client_socket.send("You can't leave the conversation you have never joined".encode())
                                continue
                            #the connection with other client is broken by changing the clients dictionary
                            other_user = self.clients[username]["connected_with"]
                            self.clients[username]["engaged"] = False
                            self.clients[username]["connected_with"] = "none"
                            self.clients[other_user]["engaged"] = False
                            self.clients[other_user]["connected_with"] = "none"
                            other_user_socket = self.clients[other_user]["socket"]
                            self.lock.release()
                            other_user_socket.send(f"{username} left the chat".encode())
                            client_socket.send(f"You left the chat with {other_user}".encode()) #other client is informed that client left the chat
                        except Exception as e:
                            print(e)
                            break
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                    else: #client sending message to someone
                        self.lock.acquire()
                        try:
                            other_user = self.clients[username]["connected_with"]
                            if(other_user=="none"):
                                self.lock.release()
                                client_socket.send("You are not connected with anyone\n".encode())
                            else:
                                other_user_socket = self.clients[other_user]["socket"]
                                self.lock.release()
                                other_user_socket.send(f"[{username}]: {command}".encode())
                        except Exception as e:
                            print(e)
                            break
                        finally:
                            if(self.lock.locked()):
                                self.lock.release()
                except Exception as e:
                    print(e)
                    break
        except Exception as e:
            print(e)
        finally:
            if(self.lock.locked()):
                self.lock.release()     

if __name__ == "__main__":
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
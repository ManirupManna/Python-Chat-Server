import socket
import threading
# from signal import signal, SIGPIPE, SIG_DFL
# signal(SIGPIPE,SIG_DFL)
class Client:
    def __init__(self, username):
        self.username = username
        self.host = 'localhost'
        self.port = 8000
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.client_socket.connect((self.host, self.port))
        self.client_socket.send(self.username.encode())
        self.server_is_online = True
        threading.Thread(target=self.receive_messages).start()
        while True:
            msg = input(f"")
            if(not self.server_is_online):
                break
            self.client_socket.send(msg.encode())

    def receive_messages(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode()
                if(msg):
                    print(msg)
                else:
                    print("Server stopped responding, closing the connection (press Enter)")
                    self.server_is_online = False
                    self.disconnect()
            except:
                break
    def disconnect(self):
        self.client_socket.close()

if __name__ == '__main__':
    username = input("Enter username: ")
    print(username)
    client = Client(username)
    try:
        client.connect()
    except KeyboardInterrupt:
        client.disconnect()

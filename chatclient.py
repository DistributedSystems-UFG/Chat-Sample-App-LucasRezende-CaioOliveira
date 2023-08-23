from socket import *
import sys
import pickle
import threading
import const  # - addresses, port numbers, etc. (a rudimentary way to replace a proper naming service)

# Class to handle receiving messages from the server
class RecvHandler(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.client_socket = sock

    def run(self):
        while True:
            (conn, addr) = self.client_socket.accept()
            marshaled_msg_pack = conn.recv(1024)
            msg_pack = pickle.loads(marshaled_msg_pack)
            print("\nMESSAGE FROM: " + msg_pack[1] + ": " + msg_pack[0])
            conn.send(pickle.dumps("ACK"))
            conn.close()

# Get user's name from command-line argument
try:
    me = str(sys.argv[1])
except IndexError:
    print('Usage: python3 chatclient.py <Username>')
    sys.exit(1)

client_sock = socket(AF_INET, SOCK_STREAM)
my_port = const.registry[me][1]
client_sock.bind(('0.0.0.0', my_port))
client_sock.listen(5)

# Start receiving thread
recv_handler = RecvHandler(client_sock)
recv_handler.start()

while True:
    # Connect to the server
    server_sock = socket(AF_INET, SOCK_STREAM)
    try:
        server_sock.connect((const.CHAT_SERVER_HOST, const.CHAT_SERVER_PORT))
    except ConnectionRefusedError:
        print("Server is down. Exiting...")
        sys.exit(1)
    
    dest = input("ENTER DESTINATION: ")
    msg = input("ENTER MESSAGE: ")

    # Send message and wait for confirmation
    msg_pack = (msg, dest, me)
    marshaled_msg_pack = pickle.dumps(msg_pack)
    server_sock.send(marshaled_msg_pack)
    marshaled_reply = server_sock.recv(1024)
    reply = pickle.loads(marshaled_reply)
    if reply != "ACK":
        print("Error: Server did not accept the message (dest does not exist?)")
    else:
        print("Message sent successfully!")

    server_sock.close()

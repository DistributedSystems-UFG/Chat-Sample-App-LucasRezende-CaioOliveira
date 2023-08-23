from socket import *
import pickle
import threading
import logging
import const

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_message(dest_ip, dest_port, msg_pack):
    logging.info('Sending message to %s:%s', dest_ip, dest_port)
    client_sock = socket(AF_INET, SOCK_STREAM)

    try:
        client_sock.connect((dest_ip, dest_port))
    except ConnectionRefusedError:
        logging.error("Error: Destination client is down")
        return

    marshaled_msg_pack = pickle.dumps(msg_pack)
    client_sock.send(marshaled_msg_pack)

    marshaled_reply = client_sock.recv(1024)
    reply = pickle.loads(marshaled_reply)

    if reply != "ACK":
        logging.error("Error: Destination client did not receive message properly")
    client_sock.close()

def remove_client(conn):
    logging.info('Removing client from connected')
    for user, client_conn in connected_clients.items():
        if client_conn == conn:
            del connected_clients[user]
            break

class ClientThread(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.client_conn = conn
        self.client_addr = addr

    def run(self):
        logging.info("Thread started for client: %s", self.client_addr)
        marshaled_msg_pack = self.client_conn.recv(1024)
        msg_pack = pickle.loads(marshaled_msg_pack)
        msg, dest, src = msg_pack

        logging.info("RELAYING MSG: %s - FROM: %s - TO: %s", msg, src, dest)

        if dest == "ALL":
            if len(connected_clients) > 1:
                self.client_conn.send(pickle.dumps("ACK"))
            else:
                self.client_conn.send(pickle.dumps("NACK"))

            for dest_conn in connected_clients.values():
                remote_address = dest_conn.getpeername()

                if self.client_addr[0] != remote_address[0]:
                    dest_ip, dest_port = const.registry.get(dest, (None, None))
                    if dest_ip:
                        send_message(dest_ip, dest_port, (msg, src))
        else:
            dest_ip, dest_port = const.registry.get(dest, (None, None))

            if dest_ip:
                self.client_conn.send(pickle.dumps("ACK"))
                for dest_conn in connected_clients.values():
                    remote_address = dest_conn.getpeername()
                    if dest_ip == remote_address[0]:
                        send_message(dest_ip, dest_port, (msg, src))
            else:
                self.client_conn.send(pickle.dumps("NACK"))

server_sock = socket(AF_INET, SOCK_STREAM)
server_sock.bind(('0.0.0.0', const.CHAT_SERVER_PORT))
server_sock.listen(5)

logging.info("Chat Server is ready...")

connected_clients = {}

while True:
    conn, _ = server_sock.accept()
    username = conn.getpeername()[0]
    connected_clients[username] = conn
    client_thread = ClientThread(conn, addr)
    client_thread.start()

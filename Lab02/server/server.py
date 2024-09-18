"""
Server module for the anonymous chat application.
Manages client connections, stores messages, and broadcasts them.
"""

import socket
import threading
from datetime import datetime

class ChatServer:
    """
    A class to represent the chat server.
    Manages client connections, messages, and broadcasting.
    """
    def __init__(self, host='127.0.0.1', port=65432):
        """
        Initializes the ChatServer with a host and port.

        Args:
            host (str): The host address for the server.
            port (int): The port number for the server.
        """
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messages = []
        self.clients = []  # List to keep track of connected clients

    def start(self):
        """
        Starts the server and listens for client connections.
        """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, _ = self.server_socket.accept()
            self.clients.append(client_socket)  # Add new client to the list
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        """
        Handles communication with a connected client.

        Args:
            client_socket (socket): The client socket object.
        """
        # Send all previous messages to the newly connected client
        self.send_all_messages(client_socket)

        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                if message == '/count':
                    count = len(self.messages)
                    client_socket.sendall(f"Total messages: {count}".encode())
                elif message == '/show':
                    self.send_all_messages(client_socket)
                else:
                    self.add_message(message)
                    self.broadcast_message(f"New message: {message}", client_socket)
            except (ConnectionResetError, BrokenPipeError):
                break

        # Remove client from list on disconnect
        self.clients.remove(client_socket)
        client_socket.close()

    def add_message(self, content):
        """
        Adds a new message to the server's message list.

        Args:
            content (str): The message content.
        """
        timestamp = datetime.now()
        self.messages.append((content, timestamp))

    def send_all_messages(self, client_socket):
        """
        Sends all stored messages to a specific client.

        Args:
            client_socket (socket): The client socket object.
        """
        for content, timestamp in self.messages:
            try:
                message = f"[{timestamp}] {content}"
                client_socket.sendall(message.encode())
                # Wait briefly to avoid socket buffer overflow
                threading.Event().wait(0.1)
            except (ConnectionResetError, BrokenPipeError):
                # Handle client disconnection
                print("Failed to send messages to a client. Removing client.")
                self.clients.remove(client_socket)
                break

    def broadcast_message(self, message, sender_socket=None):
        """
        Broadcasts a message to all connected clients except the sender.

        Args:
            message (str): The message to broadcast.
            sender_socket (socket, optional): The socket of the client sending the message.
        """
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.sendall(message.encode())
                except (ConnectionResetError, BrokenPipeError):
                    # Handle client disconnection
                    print("Failed to broadcast message to a client. Removing client.")
                    self.clients.remove(client)

if __name__ == "__main__":
    server = ChatServer()
    server.start()


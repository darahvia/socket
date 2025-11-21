import socket
import threading
import crc
import random
import time
import tkinter as tk
from tkinter import scrolledtext

#Set Socket
server = socket.socket()
host_name = socket.gethostname()		#device name
ip = socket.gethostbyname(host_name)		#IP address of device
port = 1234					#Port to listen at for connection
server.bind((ip, port))

# list to store clients and their names
clients = []
client_names=[]
last_broadcast_message = ""
last_broadcast_sender = None
last_retransmit_time = 0

log_widget = None

def log(message):
    #Print to GUI if available, otherwise print to console
    if log_widget:
        log_widget.insert(tk.END, message + "\n")
        log_widget.see(tk.END)
    else:
        print(message)

# function to broadcast messages to all clients (send message to all clients except the sender)
def broadcast(message, sender_socket, is_error_msg=False):
    # 10% error simulation (but not for error messages)
    if not is_error_msg and random.random() < 0.1:
        packet = crc.create_packet(message)
        packet_str = packet.decode()
        # Corrupt by changing one character in CRC
        parts = packet_str.split('|')
        if len(parts) == 2 and len(parts[1]) > 0:  # check both parts exist
            corrupted_crc = parts[1][:-1] + ('1' if parts[1][-1] == '0' else '0')
            packet = (parts[0] + '|' + corrupted_crc).encode()
    else:
        packet = crc.create_packet(message)

    for client in clients:
        if client != sender_socket:
                client.send(packet)

# function to remove client
def remove_client(client_socket):
	if client_socket in clients:
		index = clients.index(client_socket)
		clients.remove(client_socket)
		name = client_names.pop(index)
		log(f"{name} has disconnected.")
		broadcast(f"--- {name} has left the chat ---", client_socket, is_error_msg=True)
		client_socket.close()  

def handle_client(c_socket, c_address):
    global last_broadcast_message, last_broadcast_sender, last_retransmit_time
    try:
        c_name = c_socket.recv(1024).decode()
        client_names.append(c_name)
        clients.append(c_socket)
        
        log(f"{c_name} at '{c_address}' has joined the server")
        
        msg = f"Hi {c_name}! Welcome to the server. Type [bye] to exit."
        c_socket.send(crc.create_packet(msg))
        
        broadcast(f"--- {c_name} has joined the chat ---", c_socket, is_error_msg=True)

        

        while True:
            recv_packet = c_socket.recv(1024)
            
            is_valid, recv_msg = crc.verify_packet(recv_packet)
            
            # received corrupted message from client
            if not is_valid:
                
                error_msg = "[ERROR_NOTIF_FROM_SERVER]"           # notify client that the received message is corrupted
                log(f"CRC Error from {c_name}.")
                c_socket.send(crc.create_packet(error_msg))
                continue
            
            log(f"{c_name} > {recv_msg}")

            if recv_msg == "[ERROR_NOTIF_FROM_CLIENT]":
                current_time = time.time()      #handle  multiple error notif
                if current_time - last_retransmit_time < 1.0:
                    log(f"Ignored redundant complaint from {c_name}")
                    continue

                last_retransmit_time = current_time

                log(f"Broadcast corrupted. Retransmitting for {c_name}...")
                broadcast("[ERROR: Broadcast corrupted. Rebroadcasting...]", None, is_error_msg=True)             # client is reporting broadcast error

                time.sleep(0.1)
                
                # rebroadcast
                if last_broadcast_message:
                    broadcast(last_broadcast_message, last_broadcast_sender)              
                continue
            
            if recv_msg == "[bye]":
                break
            
            broadcast_msg = f"{c_name} > {recv_msg}"
            last_broadcast_message = broadcast_msg
            last_broadcast_sender = c_socket
            broadcast(broadcast_msg, c_socket)
            
            
    except Exception as e:
        log(f"Error with client {c_address}: {e}")
    
    finally:  # when loop breaks
        remove_client(c_socket)
		
def start_server():
    log(f"Server has started on address: {ip} and port: {port}") 
    server.listen()
    log("Waiting for clients... ")
    
    while True:
        # accept new client
        (c_socket, c_address) = server.accept()
        
        # start a new thread to handle this client
        thread = threading.Thread(target=handle_client, args=(c_socket, c_address))
        thread.start()

class ServerGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Chat Server (Admin)")
        self.window.geometry("600x500")
        
        # log area
        self.log_text = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, width=70, height=20)
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        global log_widget
        log_widget = self.log_text
        
        # input area
        self.input_frame = tk.Frame(self.window)
        self.input_frame.pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)
        
        #entry field
        self.msg_entry = tk.Entry(self.input_frame, font=("Arial", 12))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        # enter to send
        self.msg_entry.bind("<Return>", lambda e: self.send_server_message())
        
        # send button
        self.send_button = tk.Button(self.input_frame, text="Broadcast", 
                                     bg="blue", fg="white", font=("Arial", 10, "bold"),
                                     command=self.send_server_message)
        self.send_button.pack(side=tk.RIGHT)
        
        #start server thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        self.window.mainloop()

    def send_server_message(self):
        #get text
        message = self.msg_entry.get().strip()
        
        if message:
            formatted_msg = f"[SERVER]: {message}"
            
            # locally
            log(formatted_msg)
            
            # broadcast to everyone
            broadcast(formatted_msg, None)
            
            # clear entry
            self.msg_entry.delete(0, tk.END)

if __name__ == "__main__":
    gui = ServerGUI()
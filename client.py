import socket
import threading
import crc
import tkinter as tk
from tkinter import scrolledtext, messagebox

class Client:
    def __init__(self, window):
        self.window = window
        self.window.title("Client Chat")
        
        self.client = None
        self.connected = False
        self.username = ""
        
        self.client_ui()
        self.show_connection_screen()

    def client_ui(self):
        # Login screen
        self.connection_frame = tk.Frame(self.window, bg="white")
        self.connection_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(self.connection_frame, text="Server IP Address:", 
                font=("Arial", 10), bg="white").pack(pady=5)
        self.ip_entry = tk.Entry(self.connection_frame, font=("Arial", 10), width=30)
        self.ip_entry.pack(pady=5)
        
        tk.Label(self.connection_frame, text="Name:", 
                font=("Arial", 10), bg="white").pack(pady=5)
        self.name_entry = tk.Entry(self.connection_frame, font=("Arial", 10), width=30)
        self.name_entry.pack(pady=5)
        
        self.connect_button = tk.Button(self.connection_frame, text="Connect", 
                                       font=("Arial", 10, "bold"), bg="green", 
                                       fg="white", width=15, command=self.connect_to_server)
        self.connect_button.pack(pady=20)
        
        # Chat screen
        self.chat_frame = tk.Frame(self.window)
        
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, 
                                                      state='disabled', height=20, 
                                                      font=("Arial", 10))
        self.chat_display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        self.chat_display.tag_config("system", foreground="green")
        self.chat_display.tag_config("error", foreground="red")
        self.chat_display.tag_config("user", foreground="blue", font=("Arial", 10, "bold"))
        
        input_frame = tk.Frame(self.chat_frame)
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.message_entry = tk.Entry(input_frame, font=("Arial", 10))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = tk.Button(input_frame, text="Send", font=("Arial", 10, "bold"),
                                     bg="blue", fg="white", width=10, 
                                     command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_button = tk.Button(input_frame, text="Disconnect", 
                                          font=("Arial", 10), bg="red", 
                                          fg="white", width=10, command=self.disconnect)
        self.disconnect_button.pack(side=tk.LEFT)
    
    # Login screen
    def show_connection_screen(self):
        self.chat_frame.pack_forget()
        self.connection_frame.pack(fill=tk.BOTH, expand=True)
        self.window.geometry("300x200")
    
    # Chat screen
    def show_chat_screen(self):
        self.connection_frame.pack_forget()
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        self.window.geometry("500x500")
        self.message_entry.focus()
    
    # Connect to server
    def connect_to_server(self):
        ip = self.ip_entry.get().strip()
        username = self.name_entry.get().strip()
        
        if not ip:
            messagebox.showerror("Error", "Please enter server IP address")
            return
        
        if not username:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        self.username = username
        self.connect_button.config(state='disabled', text="Connecting...")
        
        try:
            # Create socket and connect to server
            self.client = socket.socket()
            self.client.connect((ip, 1234))
            self.client.send(username.encode())
            
            self.connected = True
            self.show_chat_screen()
            self.add_message("Connected to server!", "system")
            
            # Start thread
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server:\n{e}")
            self.connect_button.config(state='normal', text="Connect")
    
    def receive_messages(self):
        while self.connected:
            try:
                # Receive packet from server
                packet = self.client.recv(1024).decode()
                
                if not packet:
                    self.add_message("Disconnected from server", "system")
                    self.connected = False
                    break
                
                # Check packet using CRC
                is_valid, message = crc.verify_packet(packet)
                
                if is_valid:
                    self.add_message(message)
                else:
                    self.add_message("[Error: Message corrupted]", "error")
                    
            except Exception as e:
                if self.connected:
                    self.add_message(f"Connection error: {e}", "error")
                break
    
    def send_message(self):
        message = self.message_entry.get().strip()
        
        if not message:
            return
        
        try:
            # Create CRC packet and send to server
            packet = crc.create_packet(message)
            self.client.send(packet)
            
            self.add_message(f"You > {message}", "user")
            self.message_entry.delete(0, tk.END)
            
            if message == "[bye]":
                self.window.after(500, self.disconnect)
                
        except Exception as e:
            self.add_message(f"Error sending message: {e}", "error")
    
    def disconnect(self):
        if self.connected:
            try:
                # Send message to server
                packet = crc.create_packet("[bye]")
                self.client.send(packet)
            except:
                pass
            
            # Close socket connection
            self.connected = False
            if self.client:
                self.client.close()
            
            self.add_message("Disconnected from server", "system")
        
        self.window.after(500, self.window.destroy)
    

    def add_message(self, message, tag="normal"):
        def _add():
            self.chat_display.config(state='normal')
            self.chat_display.insert(tk.END, message + "\n", tag)
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')
        
        if threading.current_thread() is threading.main_thread():
            _add()
        else:
            self.window.after(0, _add)

if __name__ == "__main__":
    window = tk.Tk()
    app = Client(window)
    window.mainloop()
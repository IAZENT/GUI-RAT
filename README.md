# Python GUI RAT (Remote Access Trojan)

This project is a **Remote Access Trojan (RAT) with a GUI-based server**, allowing full control over a compromised system. It includes **keylogging, screen sharing, webcam access, registry editing, file management, and system commands**.
![image](https://github.com/user-attachments/assets/4f64aaf3-4b58-4fc1-838b-56c977bf2cec)


---

## ⚠️ Disclaimer
**This software is for educational and research purposes only.**  
Unauthorized access to a system without consent is illegal and punishable by law. Use it only on systems you own or have permission to test.

---

## 📌 Features
### 🎯 **Server (GUI_Server.py)**
- **Graphical User Interface (GUI)**
- **Command execution** (cmd/powershell)
- **File management** (upload, download, delete, edit, search)
- **Screen & Webcam access** (live streaming & snapshots)
- **Keylogging** (start/stop keylogger, retrieve logs)
- **Task & Process Control** (list, kill processes)
- **System Control** (shutdown, reboot, volume control)
- **Registry Manipulation** (edit, create, delete keys)
- **Network Scanning** (IP config, port scan, WiFi profiles)
- **Send pop-up messages to the victim**
- **Geolocation tracking**

### 🖥️ **Client (client.py)**
- **Establishes connection with the server**
- **Executes received commands**
- **Captures screenshots & webcam feeds**
- **Logs keystrokes**
- **Blocks user input (mouse/keyboard)**
- **Runs in the background silently**

---

## 🔧 Installation & Usage
### 1️⃣ **Install Required Dependencies**
Run:
```bash
pip install -r requirements.txt

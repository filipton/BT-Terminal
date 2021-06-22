import subprocess
import threading
import requests
import base64
import socket
import sys
import os

VERSION = "0.8.1"

class BashWrapper:
    def __init__(self):
        print("INIT")
        self.proc = subprocess.Popen(["bash"], stderr=subprocess.PIPE,shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.alive = True
        threading.Thread(target=self.read_stdout).start()
        threading.Thread(target=self.read_stderro).start()

    def read_stdout(self):
        try:
            while self.alive == True:
                msg = self.proc.stdout.readline()
                if msg.decode().isspace() == False:
                    client.send(msg)
        except:
            print("FATAL ERROR! RESTARTING APPLICATION...")
            os.execv(sys.executable, ['python3'] + sys.argv)
    def read_stderro(self):
        try:
            while self.alive == True:
                msg = self.proc.stderr.readline()
                if msg.decode().isspace() == False:
                    client.send("Error in: ".encode() + msg)
        except:
            print("FATAL ERROR! RESTARTING APPLICATION...")
            os.execv(sys.executable, ['python3'] + sys.argv)
            

    def abort(self):
        self.alive = False

while 1:
    print("STARTING BLUETOOTH SOCKET...")
    termMode = False
    bw = None
    hostMACAddress = 'B8:27:EB:42:39:9A' # The MAC address of a Bluetooth adapter on the server.
    port = 1
    backlog = 1
    size = 1024
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.bind((hostMACAddress,port))
    s.listen(backlog)
    try:
        print("BLUETOOTH SOCKET STARTED SUCCESSFULLY!")
        client, address = s.accept()
        print("Client connected!")
        bw = BashWrapper()
        while 1:
            data = client.recv(size).decode("utf-8").strip()

            if data == "termmode on":
                termMode = True
                client.send("ENABLING TERMINAL MODE!\n".encode())
            elif data == "termmode off":
                termMode = False
                client.send("DISABLING TERMINAL MODE!\n".encode())
            else:
                if termMode == True:
                    bw.proc.stdin.write((data + '\n').encode())
                    bw.proc.stdin.flush()
                else:
                    if data == "reload":
                        client.send("RELOADING RFCOMM SERVER... YOU NEED TO RECONNECT!\n".encode())
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    elif data == "version":
                        client.send(f"CURRENT VERSION: {VERSION}\n".encode())
                    elif data == "update":
                        client.send("DOWNLOADING LATEST VERSION OF RFCOMM SERVER...\n".encode())
                        r = requests.get("https://api.github.com/repos/filipton/BT-Terminal/contents/rfcomm-server.py", allow_redirects=True)
                        open(sys.argv[0], 'wb').write(base64.b64decode(r.json()["content"]))
                        client.send("DONE... PLEASE RELOAD RFCOMM SERVER WITH COMMAND: 'reload'!\n".encode())
                    else:
                        client.send("TERMINAL MODE IS OFF!\n".encode())
    except KeyboardInterrupt:
        print("Bye")
        if bw != None:
            bw.abort()
            bw = None
        sys.exit()
    except:	
        print("Closing socket! ", sys.exc_info()[0])
        if bw != None:
            bw.abort()
            bw = None
        client.close()
        s.close()
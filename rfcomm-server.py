import subprocess
import threading
import requests
import base64
import socket
import shutil
import time
import sys
import os

VERSION = "1.3.2"
UPDATE_TMP_FILE = "/tmp/UPDATE"

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
    updateb64TerminalMode = False
    updateb64Buffer = ''
    bw = None
    hostMACAddress = '' # The MAC address of a Bluetooth adapter on the server. (Or create file MAC with your BT Controller MAC Adress)

    try:
        infile = open(os.getcwd()+"/MAC", 'r')
        hostMACAddress = infile.read().strip()
        infile.close()
    except:
        print(f"CANNOT FIND '{os.getcwd()}/MAC' FILE... USING DEAFULT. PLEASE WRITE YOUR BLUETOOTH CARD MAC TO THIS FILE AND REBOOT SCRIPT. (Error: {sys.exc_info()[0]})")
        hostMACAddress = subprocess.Popen("sudo hcitool dev | awk '/hci0/ {print $2}'", shell=True, stdout=subprocess.PIPE).stdout.readline().decode().strip()

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
                elif updateb64TerminalMode == True:
                    if data == "end":
                        client.send("ABORTING UPDATE...\n".encode())
                        updateb64Buffer = ''
                        updateb64TerminalMode = False
                    elif data == "confirm":
                        client.send("UPDATE CONFIRMED!\n".encode())
                        try:
                            open(UPDATE_TMP_FILE, 'a').close()
                            client.send("SAVING CURRENT VERSION FOR RESTORING...\n".encode())
                            shutil.copy2(sys.argv[0], os.getcwd()+"/old.py")
                            file = base64.b64decode(updateb64Buffer)
                            open(sys.argv[0], 'wb').write(file)
                            client.send("DONE... NOW RELOADING!\n".encode())
                            os.execv(sys.executable, ['python3'] + sys.argv)
                        except:
                            client.send("ERROR WHILE TRYING TO UPDATE FROM B64!\n".encode())
                    elif data == "show":
                        client.send(base64.b64decode(updateb64Buffer))
                    else:
                        updateb64Buffer += data
                else:
                    if data == "reload":
                        client.send("RELOADING RFCOMM SERVER... YOU NEED TO RECONNECT!\n".encode())
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    elif data == "version":
                        client.send(f"CURRENT VERSION: {VERSION}\n".encode())
                    elif data == "update":
                        try:
                            open(UPDATE_TMP_FILE, 'a').close()
                            client.send("SAVING CURRENT VERSION FOR RESTORING...\n".encode())
                            shutil.copy2(sys.argv[0], os.getcwd()+"/old.py")
                            client.send("DOWNLOADING LATEST VERSION OF RFCOMM SERVER...\n".encode())
                            r = requests.get("https://api.github.com/repos/filipton/BT-Terminal/contents/rfcomm-server.py", allow_redirects=True)
                            open(sys.argv[0], 'wb').write(base64.b64decode(r.json()["content"]))
                            client.send("DONE... NOW RELOADING!\n".encode())
                            os.execv(sys.executable, ['python3'] + sys.argv)
                        except requests.exceptions.ConnectionError:
                            client.send("NO INTERNET CONNECTION! CANT DOWNLOAD NEW UPDATE!\n".encode())
                        except:
                            client.send("ERROR WHILE TRYING TO UPDATE!\n".encode())
                    elif data == "restore":
                        client.send("RESTORING...\n".encode())
                        shutil.copy2(os.getcwd()+"/old.py", sys.argv[0])
                        client.send("DONE... NOW RELOADING!\n".encode())
                        os.execv(sys.executable, ['python3'] + sys.argv)
                    elif data == "update-confirm":
                        if os.path.exists(UPDATE_TMP_FILE):
                            os.remove(UPDATE_TMP_FILE)
                            client.send("UPDATE CONFIRMED!\n".encode())
                        else:
                            client.send("UPDATE FILE NOT FOUNDED! (MAYBE ALREADY CONFIRMED?)\n".encode())
                    elif data == "debug":
                        client.send("DEBUG INFO:\n".encode())
                        
                        client.send(f"===================== SERVER INFO =====================\n".encode())
                        client.send(f"CURRENT VERSION: {VERSION}\n".encode())

                        mod_date = time.ctime(os.path.getmtime(sys.argv[0]))
                        client.send(f"MODIFIED DATE: {mod_date}\n".encode())
                        
                        if os.path.exists(UPDATE_TMP_FILE):
                            client.send("UPDATE STATE: NOT CONFIRMED\n".encode())
                        else:
                            client.send("UPDATE STATE: CONFIRMED\n".encode())

                        tot_m, used_m, free_m = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
                        client.send(f"RAM USAGE: {used_m}MB/{tot_m}MB (FREE: {free_m}MB)\n".encode())

                        uptime = os.popen('uptime -p').read()[:-1].replace('up ', '')
                        client.send(f"UPTIME: {uptime}\n".encode())

                        client.send(f"=======================================================\n\n".encode())


                        try:
                            ls = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            ls.connect(("8.8.8.8", 80))
                            LOCAL_IP = ls.getsockname()[0]
                            ls.close()
                        except:
                            LOCAL_IP = "NOT CONNECTED!"

                        client.send(f"==================== NETOWRK INFO ====================\n".encode())
                        client.send(f"LOCAL IP: {LOCAL_IP}\n".encode())

                        cmd = subprocess.Popen('sudo iwconfig wlan0', shell=True, stdout=subprocess.PIPE)
                        for line in cmd.stdout:
                            Line = str(line.decode())
                            if 'Link Quality' in Line:
                                client.send(f"{Line.lstrip(' ').strip()}\n".encode())
                            elif 'Not-Associated' in Line:
                                client.send("No Signal\n".encode())

                        try:
                            r = requests.get("https://api.ipify.org", allow_redirects=True)
                            client.send(f"CONNECTION STATUS: True ({r.text})\n".encode())
                        except:
                            client.send("CONNECTION STATUS: False\n".encode())

                        client.send(f"=======================================================\n\n".encode())
                    elif data == "updateb64":
                        client.send("UPDATE TERMINAL IS NOW SELECTED! WRITE YOU BASE64 DATA THAN COMMAND 'show' TO SHOW DECODED UPDATE, 'confirm' TO CONFIRM UPDATE OR 'end' TO ABORT UPDATING!\n".encode())
                        updateb64TerminalMode = True
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
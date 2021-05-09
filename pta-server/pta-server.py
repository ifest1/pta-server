import os
import socket
import sys
sys.path.append('..')

from utils import decode64
from utils import encode64

responses = ['OK', 'NOK', 'ARQ', 'ARQS']

class PTAServer:
    def __init__(self, host='127.0.0.1', port=11550):
        self.host = host
        self.port = port
        self.connections_opened = []
        self.files_directory = 'files'
        self.seq_num = 0
        self.users = []

        self.operations = {
            'PEGA': self.send_file,
            'LIST': self.list_files,
            'CUMP': self.open_connection,
            'TERM': self.close_connection
        }

        with open('users.txt', 'r') as f:
            for user in f.readlines():
                self.users.append(user.rstrip('\n'))

    def send_packet(self, conn, payload, file=0):
        if not file:
            packet = str(self.seq_num) + ' ' + payload
            packet = encode64(packet.encode())

        else:
            packet = str(self.seq_num) + ' ARQ ' + str(len(payload)) + ' <'
            packet = encode64(packet.encode())
            packet = packet + encode64(payload)
            
        conn.sendall(packet)
       
        self.seq_num += 1

    def wrong_action(self, conn):
        self.send_packet(conn, responses[1])

    def open_connection(self, conn, user):
        if user in self.users:
            self.connections_opened.append(conn)
            self.send_packet(conn, responses[0])
            return 1
        else:
            self.wrong_action(conn)
            return -1

    def close_connection(self, conn):
        self.send_packet(conn, responses[0])
        conn.close()
        return 0

    def list_files(self, conn):
        if not self.is_connected(conn):
            self.wrong_action(conn)
            return -1

        filenames = []

        for _, _, files in os.walk('./{}'.format(self.files_directory)):
            for filename in files: filenames += [filename]
        
        size = len(filenames)
        filenames = ','.join(filenames)
        payload = '{} {} {} ,'.format(responses[3], str(size), filenames)
        
        self.send_packet(conn, payload)

        return 1
        
    def send_file(self, conn, filename):
        if not self.is_connected(conn):
            wrong_action(conn)
            return -1

        fd = open('./{}/{}'.format(self.files_directory, filename), 'rb')
        raw_file = fd.read()
        
        self.send_packet(conn, raw_file, file=1)

        fd.close()
        return 1

    def is_connected(self, conn):
        return conn in self.connections_opened

    def is_registered(self, user):
        return user in self.users

    def splitted_data(self, data):
        data = data.decode()
        data = data.split(' ')
        return data, data[1]

    def handle_incoming_data(self, conn):
        while True:
            try:
                data = conn.recv(1024)    
                if not data: break
                data, command = self.splitted_data(data)

                if command == 'PEGA' or command == 'CUMP':
                    response = self.operations[command](conn, data[2])
                else:
                    response = self.operations[command](conn)
                
                if not response: break
            
            except Exception as e: 
                print(e)
                self.wrong_action(conn)

        self.server.close()

    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        
        conn, addr = self.server.accept()

        self.handle_incoming_data(conn)


pta_server = PTAServer()
pta_server.listen()
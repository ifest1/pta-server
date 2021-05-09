import os
import socket
import sys
sys.path.append('..')

responses = ['OK', 'NOK', 'ARQ', 'ARQS']

class PTAServer:
    def __init__(self, host='127.0.0.1', port=11550):
        self.host = host
        self.port = port
        self.connections_opened = []
        self.files_directory = 'files'
        self.seq_num = None
        self.users = []

        self.operations = {
            'PEGA': self.send_file,
            'LIST': self.send_listof_files,
            'CUMP': self.open_connection,
            'TERM': self.close_connection
        }

        with open('users.txt', 'r') as f:
            for user in f.readlines():
                self.users.append(user.rstrip('\n'))

    def send_packet(self, conn, payload):
        try:
            payload = '{} {}'.format(str(self.seq_num), payload)
            payload = payload.encode()
            conn.sendall(payload)
    
        except:
            pass

    def send_listof_files(self, conn):
        if not self.is_connected(conn):
            self.bad_action(conn)
            return -1

        filenames = []

        for _, _, files in os.walk('./{}'.format(self.files_directory)):
            for filename in files: filenames += [filename]
        
        size = len(filenames)
        filenames = ','.join(filenames)

        payload = '{} {} {},'.format(responses[3], str(size), filenames)
        
        self.send_packet(conn, payload)

        return 1
        
    def send_file(self, conn, filename):
        if not self.is_connected(conn):
            self.bad_action(conn)
            return -1
        try:
            fd = open('./{}/{}'.format(self.files_directory, filename), 'rb')
        except Exception as e:
            self.bad_action(conn)
            return -1

        raw_file = fd.read()
        length = len(raw_file)
        payload = '{} {} {} '.format(self.seq_num, responses[2], length)
        payload = payload.encode() + raw_file
        conn.sendall(payload)
        fd.close()
        return 1

    def open_connection(self, conn, user):
        if user in self.users:
            self.connections_opened.append(conn)
            self.send_packet(conn, responses[0])
            return 1
        else:
            self.abort_connection(conn)
            return 0

    def abort_connection(self, conn):
        self.send_packet(conn, responses[1])
        conn.close()

    def close_connection(self, conn):
        self.send_packet(conn, responses[0])
        if self.is_connected(conn):
            idx = self.connections_opened.index(conn)
            del self.connections_opened[idx]
        conn.close()
        return 1

    def is_connected(self, conn):
        return conn in self.connections_opened

    def is_registered(self, user):
        return user in self.users

    def bad_action(self, conn):
        self.send_packet(conn, responses[1])

    def splitted_data(self, data):
        data = data.decode()
        data = data.split(' ')
        return data, data[1]

    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

        while True:
            conn, addr = self.server.accept()
            
            self.seq_num = None

            while True:
                data = conn.recv(1024)

                if not data: break

                data, command = self.splitted_data(data)

                self.seq_num = int(data[0])

                if command == 'PEGA' or command == 'CUMP':
                    if len(data) > 2:
                        status = self.operations[command](conn, data[2])
                        if not status: break

                elif command == 'LIST':
                    self.operations[command](conn)

                elif command == 'TERM':
                    self.operations[command](conn)
                    break

                else: self.bad_action(conn)


pta_server = PTAServer()
pta_server.listen()
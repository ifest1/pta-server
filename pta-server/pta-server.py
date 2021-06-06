import os
import socket

class PTAServer:
    def __init__(self, 
                host='127.0.0.1', 
                port=11550, 
                files='files'):

        self.host = host
        self.port = port
        self.connections_opened = []
        self.files_directory = files
        self.seq_num = None
        self.users = []

        self.responses = ['OK', 'NOK', 'ARQ', 'ARQS']
        self.operations = {
            'PEGA': self.send_file,
            'LIST': self.send_list_of_files,
            'CUMP': self.open_connection,
            'TERM': self.close_connection
        }

        self.set_users()
    
    def set_users(self):
        users = open('users.txt', 'r')
        self.users = [user.rstrip('\n') 
        for user in users.readlines()]

    def send_packet(self, conn, payload):
        payload = '{} {}'.format(str(self.seq_num), payload)
        payload = payload.encode()
        conn.sendall(payload)

    def send_list_of_files(self, conn):
        if not self.is_connected(conn):
            self.bad_action(conn)
            return

        filenames = ','.join(os.listdir('./{}'.format(
                                self.files_directory)))
        payload = '{} {} {},'.format(self.responses[3], 
                                    str(len(filenames)), 
                                    filenames)
                                
        self.send_packet(conn, payload)
        
    def send_file(self, conn, filename):
        if not self.is_connected(conn): 
            self.bad_action(conn)
            return

        try:
            raw_file = open('./{}/{}'.format(
                            self.files_directory, filename), 
                            'rb').read().close()
            payload = '{} {} '.format(self.responses[2], 
                                        len(raw_file))
            payload = payload.encode() + raw_file
            self.send_packet(conn, payload)

        except Exception: 
            self.bad_action(conn)

    def open_connection(self, conn, user):
        if user in self.users:
            self.connections_opened.append(conn)
            self.send_packet(conn, self.responses[0])
            return 1

        self.abort_connection(conn)
        return 0

    def abort_connection(self, conn):
        self.send_packet(conn, self.responses[1])
        conn.close()

    def close_connection(self, conn):
        self.send_packet(conn, self.responses[0])
        if self.is_connected(conn):
            idx = self.connections_opened.index(conn)
            del self.connections_opened[idx]
            conn.close()

    def is_connected(self, conn):
        return conn in self.connections_opened

    def is_registered(self, user):
        return user in self.users

    def bad_action(self, conn):
        self.send_packet(conn, self.responses[1])

    def splitted_data(self, data):
        data = data.decode()
        data = data.split(' ')
        return data, data[1]

    def listen(self):
        self.server = socket.socket(socket.AF_INET, 
                                    socket.SOCK_STREAM)
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

                if command == 'PEGA' or 
                    command == 'CUMP' and len(data) > 2:
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
import socket   
from utils import decode64
from utils import encode64

help_string = """ \
================= COMMANDS =====================
login <user>            --> authenticate as user
download <file>         --> download file
list                    --> list files
finish                  --> close connection
================================================
"""

commands = {
    'login': 'CUMP',
    'download': 'PEGA',
    'list': 'LIST',
    'finish': 'TERM'
}

seq_num = 0

def pta_session(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s

def handle_response(data, cmd):
    response = str(data).split(' ')
    
    cmd = cmd.split(' ')

    if data[1] == 'NOK': 
        if commands[cmd[0]] == 'CUMP':
            print('Wrong user.')

        elif commands[cmd[0]] == 'PEGA':
            print('Wrong filename')
        
        elif commands[cmd[0]] == 'LIST':
            print('You must login to list files')

        return -1

    if commands[cmd[0]] == 'TERM' and response[1] == 'OK':
        return 0

    elif commands[cmd[0]] == 'PEGA' and response[1] == 'ARQ':
        fd = open('{}'.format(cmd[1]), 'wb')
        delimiter = str(data).find('<')
        raw_data = data[delimiter-1:]    
        fd.write(raw_data)
        fd.close()
        

    elif commands[cmd[0]] == 'LIST' and response[1] == 'ARQS':
        for filename in response[3].split(','):
            print(filename)

    return 1

def send_packet(s, cmd):
    global seq_num

    cmd = cmd.split(' ')
    cmd_packet = ''
    cmd_packet += str(seq_num)
    cmd_packet += ' ' + commands[cmd[0]]

    if len(cmd) >= 2: cmd_packet += ' ' + cmd[1]
    bytes_encoded = cmd_packet.encode()
    s.send(bytes_encoded)
    seq_num += 1

    data = s.recv(65500000)
    
    bytes_decoded = decode64(data)
    
    return bytes_decoded

def main(port=11550):
    s = pta_session('127.0.0.1', port)
    print(help_string)

    while True:
        try:
            cmd = input('pta client prompt> ')
            data = send_packet(s, cmd)
        
            response_status = handle_response(data, cmd)
            
            if not response_status:
                s.close()
                break

        except Exception as e:
            print(e)
            pass

if __name__ == '__main__':
    main()
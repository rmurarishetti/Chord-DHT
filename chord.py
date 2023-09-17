#!/Users/rmurarishetti/opt/anaconda3/bin/python
import socket
import sys
import select
import time
import hashlib
import argparse
import ipaddress
import os

from protobuf import chord_pb2

global chord_ring
global chord_id
global finger_table
global successors
global links
global sock
global salt
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
links = {}
chord_ring = []
chord_id = 0
finger_table = []
successors = []
salt = b'55634e52-4567-89ab-cdef-123456789abc'



socket_node = -1
def join_parser():
    
    parser = argparse.ArgumentParser(description='Process some arguments.')
    
    parser.add_argument('-p', '--port', type=int, help='The port number to use')
    parser.add_argument('-i', '--ja', type=str, help='The IP address to use')
    parser.add_argument('--jp', type=int, help='The jp option')
    parser.add_argument('--sp', type=int, help='The sp option')
    parser.add_argument('--ffp', type=int, help='The ffp option')
    parser.add_argument('--cpp', type=int, help='The cpp option')
    parser.add_argument('-r', type=int, help='The r option')
    args = parser.parse_args()

    port = args.port
    ja = args.ja
    jp = args.jp
    sp = args.sp
    ffp = args.ffp
    cpp = args.cpp
    r = args.r
    mylist=[port,ja,jp,sp,ffp,cpp,r]
    my_dict = {str(key): value for key, value in zip(['port', 'ja', 'jp', 'sp', 'ffp', 'cpp', 'r'], mylist)}
    return(my_dict)



    
def create(dic):
    
    
    global chord_id
    global finger_table
    global successors
    global sock
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_address = ("", dic['port'])
    try:
     sock.bind(server_address)
     sock.listen(20)
     socket_node = sock
    except:
     print("An exception occurred") 

    ip_address = socket.gethostbyname(socket.gethostname())

    message_to_encode = (ip_address + str(dic['port'])).encode('utf-8')
    sha1 = hashlib.sha1(salt)
    sha1.update(message_to_encode)
    hash_digest = sha1.hexdigest()
    truncated_hash = hash_digest[:8]

    chord_id = bytes(truncated_hash, "utf-8")
    chord_id = int.from_bytes(chord_id, 'big')

    finger_dict = {'id': chord_id, 'ip': ip_address, 'port': dic['port']}
    finger_table = [finger_dict] * 64
    succesor_dict = {'id': chord_id, 'ip': ip_address, 'port': dic['port']}
    successors = [succesor_dict] * dic['r']
    chord_ring.append(truncated_hash)

    
def printState(returned_dictionary):
    ip_address = socket.gethostbyname(socket.gethostname())
    print(f"< Self {chord_id} {ip_address} {returned_dictionary['port']}") 

    for i in range(len(successors)):
        print(f"< Succesor[{i+1}] {successors[i]['id']} {successors[i]['ip']} {successors[i]['port']}")
    
    for i in range(len(finger_table)):
        print(f"< Finger[{i+1}] {finger_table[i]['id']} {finger_table[i]['ip']} {finger_table[i]['port']}")
    
def closest_preceding_node(hashed_id):
    for i in range(63, -1, -1):
        if (finger_table[i]['id']>chord_id and finger_table[i]['id']<hashed_id):
            return finger_table[i]['id']

    return chord_id     

def find_successors(hashed_id):
    
    first_successor = successors[0]
    if type(hashed_id) != int:
        hashed_id = int(hashed_id)

    if(first_successor['id'] == chord_id):
        return chord_id
    
    if(first_successor['id']>chord_id and hashed_id<=first_successor['id']):
        return first_successor['id']

    n = closest_preceding_node(hashed_id)
    return(find_successors(n))
            

def handleClient(server_sock,poller):
    global links
    conn, addr = server_sock.accept()
    links[conn.fileno()] = [conn,addr,True]
    poller.register(conn,select.POLLIN)
    print(f"Incoming connection from ${addr}")
    
def join(dic):

    global chord_id
    global finger_table
    global successors
    global sock

    ip_address = socket.gethostbyname(socket.gethostname())

    join_addr = dic['ja']
    join_port = dic['jp']
    
    try:
        sock.bind((ip_address,dic['port']))
        sock.connect((join_addr, join_port))
    except:
        print("Connection failed")

    
    message_to_encode = (ip_address + str(dic['port'])).encode('utf-8')
    sha1 = hashlib.sha1(salt)
    sha1.update(message_to_encode)
    hash_digest = sha1.hexdigest()
    truncated_hash = hash_digest[:8]
    
    chord_id = bytes(truncated_hash, "utf-8")
    chord_id = int.from_bytes(chord_id, 'big')

    finger_dict = {'id': chord_id, 'ip': ip_address, 'port': dic['port']}
    finger_table = [finger_dict] * 64
    successors = [finger_dict] * dic['r']

    successor = find_successors(chord_id)
   
    successors = [successor] * dic['r']
    message = chord_pb2.ChordMessage()
    request = chord_pb2.FindSuccessorRequest()
    request.key = chord_id

    
    message.msg.find_successor_request.CopyFrom(request)

    message.version = 417

    serialized_message = message.SerializeToString()
    sock.send(serialized_message)

    
def lookup(msg):
    msg_encoded = msg.encode("utf-8")
    sha1 = hashlib.sha1(salt)
    sha1.update(msg_encoded)

    hash_digest = sha1.hexdigest()
    truncated_hash = hash_digest[:8]

    msg_encoded = bytes(truncated_hash, "utf-8")
    msg_encoded = int.from_bytes(msg_encoded, 'big')

    print(f"< {msg} {msg_encoded}")

    #find which node the message will belong to 


    
    
    
def main():
    returned_dictionary = join_parser()
   
    if (returned_dictionary['jp']==None or returned_dictionary['ja']==None):
        create(returned_dictionary)
    
    else:
        join(returned_dictionary)

    poller = select.poll()
    poller.register(sock, select.POLLIN)
    poller.register(sys.stdin.fileno(), select.POLLIN)

    while True:

        events = poller.poll(300)
        for fd, event in events:
            if fd == sock.fileno():
                handleClient(sock, poller)

            elif event & select.POLLIN:
                if fd == sys.stdin.fileno():
                    line = sys.stdin.readline()

                    if "PrintState" in line:
                        printState(returned_dictionary)

                    elif "Lookup" in line:
                        msg = line.split()
                        msg = msg[-1]
                        lookup(msg)
                
                else:
                     try:
                        header = links[fd][0].recv(16)
                     except:
                        print("Some exception occured")
                        exit(1)
                    
                     print(header)

        
        
        
        

main()


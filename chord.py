#!/usr/bin/python3
import socket
import sys
import select
import sched, time
import hashlib
import argparse
import os
import threading

global already_joined
global chord_ring
global chord_id
global finger_table
global predecessor
global successors
global links
global sock
global salt
global self_ip_address
global self_port
global my_scheduler
global creator

my_scheduler = sched.scheduler(time.monotonic, time.sleep)
self_ip_address = socket.gethostbyname(socket.gethostname())
predecessor = {}
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
links = {}
chord_ring = []
chord_id = 0
creator = False
finger_table = []
successors = []
salt = b'55634e52-4567-89ab-cdef-123456789abc'

os.environ['PS1'] = "> "

socket_node = -1
def join_parser():
    
    parser = argparse.ArgumentParser(description='Process some arguments.')
    
    parser.add_argument('-p', '--port', type=int, help='The port number to use')
    parser.add_argument('-i', '--ja', type=str, help='The IP address to use')
    parser.add_argument('--jp', type=int, help='The jp option')
    parser.add_argument('--sp', type=int, choices=range(1, 601),help='The sp option')
    parser.add_argument('--ffp', type=int, choices=range(1, 601),help='The ffp option')
    parser.add_argument('--cpp', type=int, choices=range(1, 601),help='The cpp option')
    parser.add_argument('-r', type=int, choices=range(1,33),help='The r option')
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
    global predecessor
   
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_address = ("", dic['port'])
    try:
     sock.bind(server_address)
     sock.listen(20)
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
    predecessor = finger_dict
    finger_table = [finger_dict] * 64
    succesor_dict = {'id': chord_id, 'ip': ip_address, 'port': dic['port']}
    successors = [succesor_dict] * dic['r']
    chord_ring.append(finger_dict)
    
    
def scheduler_call(dic):
    run_scheduler(dic['sp'], stabilize, dic)
    run_scheduler(dic['ffp'], fix_fingers, ())
    run_scheduler(dic['cpp'], check_predecessor, dic)
    
    
def printState(returned_dictionary):
    ip_address = socket.gethostbyname(socket.gethostname())
    print(f"< Self {chord_id} {ip_address} {returned_dictionary['port']}") 

    for i in range(len(successors)):
        print(f"< Successor [{i+1}] {successors[i]['id']} {successors[i]['ip']} {successors[i]['port']}")
    
    for i in range(len(finger_table)):
        print(f"< Finger [{i+1}] {finger_table[i]['id']} {finger_table[i]['ip']} {finger_table[i]['port']}")
    
def closest_preceding_node(hashed_id):
    global self_ip_address, self_port
    for i in range(63, -1, -1):
        
        if(is_in_range(finger_table[i]['id'],chord_id,hashed_id)):          
            return finger_table[i]

    return {'id':chord_id, 'ip': self_ip_address, 'port': self_port}    

def is_in_range(x, b, c):
    if b < c:
        return b < x < c
    else:
        return x > b or x < c

def find_successors(hashed_id):
    global self_port, self_ip_address

    first_successor = successors[0]
    if type(hashed_id) != int:
        hashed_id = int(hashed_id)

    if(chord_id == first_successor['id']):
        return {'id':chord_id, 'ip': self_ip_address, 'port': self_port}
    
    elif(is_in_range(hashed_id,chord_id,first_successor['id'])):
        return first_successor

    else:
        n = closest_preceding_node(hashed_id)
        if chord_id!= n['id']:
            header = b'\x04\x17'
            message = str({'hashed_id':hashed_id,'chord_id':chord_id}).encode('utf-8')
            msg_len = len(message).to_bytes(4, 'big')
            msg_type = 6
            header = msg_len + header + msg_type.to_bytes(1, 'big') + message
            IP_ADDRESS = n['ip']  # replace with the target IP address
            PORT = n['port']+30000  # replace with the target port number

            sock_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_temp.connect((IP_ADDRESS, PORT))
            sock_temp.send(header)

            header = sock_temp.recv(7)
        
            if(len(list(header))==7):
                msgtype = list(header)[-1]
                if(msgtype==7):     
                    val = int.from_bytes(header[:4],"big")
                    payload = sock_temp.recv(val)
                    payload = payload.decode('utf-8')
                    payload = eval(payload)
                    sock_temp.close()
                    return(payload)
            
        else:
            return successors[0]

def stabilize(dic):
    global self_port, self_ip_address
    
    nsucc = successors[0]
    
    if (successors[0]['id']==chord_id):
        return

    ip_address = socket.gethostbyname(socket.gethostname())
    #nsucc_pred = closest_preceding_node(nsucc['id']) #change predecessor logic
    header = b'\x04\x17'
    nsucc_pred = str(-1)
    msg_len = len([]).to_bytes(4, 'big')
    msg_type = 4
    header = msg_len + header + msg_type.to_bytes(1, 'big')  
    IP_ADDRESS = nsucc['ip']  # replace with the target IP address
    PORT = nsucc['port']  # replace with the target port number
    sock_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock_temp.connect((IP_ADDRESS, PORT+40000))
    
    sock_temp.send(header)
    header = sock_temp.recv(7)

    if(len(list(header))==7):
        msgtype = list(header)[-1]
        if(msgtype==5):     
            val = int.from_bytes(header[:4],"big")
            payload = sock_temp.recv(val)
            payload = payload.decode('utf-8')
            payload = eval(payload)
            nsucc_pred = payload['id']
    sock_temp.close()
    
    if(nsucc_pred!=None and  is_between(nsucc_pred,  chord_id,nsucc['id'])):
        successors[0] = nsucc_pred
    header = b'\x04\x17'
    chord_id_str = str({'id':chord_id,'ip':ip_address,'port':dic['port']}).encode("utf-8")
    msg_len = len(chord_id_str).to_bytes(4, 'big')
    msg_type = 2
    header = msg_len + header + msg_type.to_bytes(1, 'big')  + chord_id_str 

    sock.send(header)
    header = sock.recv(7)
    
    if(len(list(header))==7):
        msgtype = list(header)[-1]
        if(msgtype==3):     
            val = int.from_bytes(header[:4],"big")
            payload = sock.recv(val)
            payload = payload.decode('utf-8')
 
def is_between(id, a, b):
    if a == b:
        return True
    if a < b:
        return id > a and id < b
    else:
        return id > a or id < b       

def handleClient(server_sock,poller):
    global links
    conn, addr = server_sock.accept()
    links[conn.fileno()] = [conn,addr,True]
    poller.register(conn,select.POLLIN)    
    
def check_predecessor(dic):
    global predecessor

    ip_address = socket.gethostbyname(socket.gethostname())

    if(not(predecessor['id']!=chord_id)):
        sock_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock_temp.connect((predecessor['ip'],predecessor['port']))
        except:
            predecessor = {'id':chord_id,'ip':ip_address,'port':dic['port']}
                  
    
def join(dic):

    global chord_id
    global finger_table
    global successors
    global sock
    global predecessor
    
    ip_address = socket.gethostbyname(socket.gethostname())

    join_addr = dic['ja']
    join_port = dic['jp']
    
    sock.bind((ip_address,dic['port']))
    try:
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
    predecessor = finger_dict
    finger_table = [finger_dict] * 64
    successors = [finger_dict] * dic['r']

    chord_ring.append(finger_dict)
    
    #custom find succesor request
    header = b'\x04\x17'
    chord_id_str = str(chord_id).encode("utf-8")
    msg_len = len(chord_id_str).to_bytes(4, 'big')
    msg_type = 0
    header = msg_len + header + msg_type.to_bytes(1, 'big')  + chord_id_str 

    sock.send(header)
    header = sock.recv(7)
    if(len(list(header))==7):
        msgtype = list(header)[-1]
        if(msgtype==1):     
            val = int.from_bytes(header[:4],"big")
            payload = sock.recv(val)
            payload = payload.decode('utf-8')
            my_dict = eval(payload)
            finger_table[0] = my_dict
            successors[0] = my_dict
            chord_ring.append(my_dict)


def fix_fingers(number=0):
    global self_ip_address
    global self_port

    for next in range(0, 64):
        if next == 0:
                finger_table[0] = successors[0]
        else:
            number = (chord_id + pow(2, next))%pow(2, 64)
            temp = find_successors(number)
            finger_table[next] = temp

    for i in range(1, len(successors)):
        temp = successors[i-1]
        if temp['id'] != chord_id:
            header = b'\x04\x17'
            
            msg_len = len([]).to_bytes(4, 'big')
            msg_type = 8
            header = msg_len + header + msg_type.to_bytes(1, 'big') 
            IP_ADDRESS = temp['ip']  # replace with the target IP address
            PORT = temp['port'] +30000  # replace with the target port number

            sock_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if number==0:
                sock_temp.connect((IP_ADDRESS, PORT))
            else:
                sock_temp.connect((IP_ADDRESS, PORT+10000))

            sock_temp.send(header)
            header = sock_temp.recv(7)

            if(len(list(header))==7):
                    msgtype = list(header)[-1]
                    if(msgtype==9):     
                        val = int.from_bytes(header[:4],"big")
                        payload = sock_temp.recv(val)
                        payload = payload.decode('utf-8')
                        payload = eval(payload)
                        successors[i] = payload
                        sock_temp.close()
        else:
            successors[i] = successors[0]
    
            

    
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
    ret = find_successors(msg_encoded)
    print(f"< {ret['id']} {ret['ip']} {ret['port']}")

def run_scheduler(delay, function, args):
    
    delay = delay / 10
    #add function to scheduler
    if args == ():
        my_scheduler.enter(delay, 2, function, ())
    else:
        my_scheduler.enter(delay, 1, function, (args,))
    
    my_scheduler.run(blocking=True)
    
    
def main():
    global self_port
    sys.stdout.write(os.environ['PS1'])
    sys.stdout.flush()

    returned_dictionary = join_parser()
    self_port = returned_dictionary['port']
   
    poller = select.poll()
    poller.register(sys.stdin.fileno(), select.POLLIN)

    if (returned_dictionary['jp']==None or returned_dictionary['ja']==None):
        create(returned_dictionary)
        poller.register(sock, select.POLLIN)
        
    else:
        join(returned_dictionary)
    
    #listening socket setup
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind((self_ip_address, self_port+30000))
    listen_sock.listen()
    poller.register(listen_sock, select.POLLIN)

    listen_sock_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock_2.bind((self_ip_address, self_port+40000))
    listen_sock_2.listen()
    poller.register(listen_sock_2, select.POLLIN)
    
    t = threading.Thread(target=scheduler_call, args=(returned_dictionary, ))
    t.start()

    while True:

        global predecessor

        min_time = min(returned_dictionary['sp'], returned_dictionary['ffp'], returned_dictionary['cpp'])
        events = poller.poll(min_time*100)

        for fd, event in events:

            if (fd == sock.fileno()):
                handleClient(sock, poller)
            
            elif (fd == listen_sock.fileno()):
                conn, addr = listen_sock.accept()
                poller.register(conn,select.POLLIN)
                links[conn.fileno()] = [conn,addr,True]

            elif (fd == listen_sock_2.fileno()):
                conn, addr = listen_sock_2.accept()
                poller.register(conn,select.POLLIN)
                links[conn.fileno()] = [conn,addr,True]


            elif event & select.POLLIN:
                
                if fd == sys.stdin.fileno():
                    line = sys.stdin.readline()

                    if "PrintState" in line:
                        printState(returned_dictionary)

                    elif "Lookup " in line:
                        msg = line.split()
                        msg = msg[-1]
                        lookup(msg)

                    sys.stdout.write(os.environ['PS1'])
                    sys.stdout.flush()

                else:
                     try:
                        header = links[fd][0].recv(7)
                        
                     except:
                        print("Some exception occured")
                        exit(1)

                     if(len(list(header))==7):
                         msgtype = list(header)[-1]
                         #RequestSuccesor Message
                         if(msgtype==0):
                             val = int.from_bytes(header[:4],"big")
                             payload = links[fd][0].recv(val)
                             payload = payload.decode('utf-8')
                             ret = find_successors(payload)
                            
                             #processing new joinee and adding to chord_ring datastructure on ring_creator side
                             addr, port = links[fd][1][:2]
                             node_dic = {'id': int(payload), 'ip': addr, 'port':port}
                             chord_ring.append(node_dic)

                             if(is_between(node_dic['id'], chord_id, successors[0]['id'])):
                                finger_table[0] = node_dic
                                successors[0] = node_dic
                                for i in range(2, len(successors), 2):
                                    successors[i] = node_dic
                           

                             ret = str(ret)
                            
                             chord_id_str = ret.encode("utf-8")
                             header = b'\x04\x17'
                             msg_len = len(chord_id_str).to_bytes(4, 'big')
                             msg_type = 1
                             header = msg_len + header + msg_type.to_bytes(1, 'big')  + chord_id_str 
                             links[fd][0].send(header)
                             
                         #NotifyRequest Message
                         if(msgtype==2):
                             val = int.from_bytes(header[:4],"big")
                             payload = links[fd][0].recv(val)
                             payload = payload.decode('utf-8')
                             payload = eval(payload)
                             pred = predecessor
                             if (not pred or is_between(payload['id'], pred['id'], chord_id)):
                                predecessor = payload
                             header = b'\x04\x17'
                             msg_len = len([]).to_bytes(4, 'big')
                             msg_type = 3
                             header = msg_len + header + msg_type.to_bytes(1, 'big')
                             links[fd][0].send(header)

                             
                         #RequestPredecessor Message
                         if(msgtype==4):
                             val = int.from_bytes(header[:4],"big")
                             payload = links[fd][0].recv(val)
                             payload = payload.decode('utf-8')
                             chord_id_str = str(predecessor).encode("utf-8")
                             header = b'\x04\x17'

                             msg_len = len(chord_id_str).to_bytes(4, 'big')
                             msg_type = 5
                             header = msg_len + header + msg_type.to_bytes(1, 'big')  + chord_id_str 
                             links[fd][0].send(header)

                             
                         if(msgtype==6):
                             val = int.from_bytes(header[:4],"big")
                             payload = links[fd][0].recv(val)
                             payload = payload.decode('utf-8')
                             payload = eval(payload)
                             n = find_successors(payload['hashed_id'])
                             chord_id_str = str(n).encode("utf-8")
                             header = b'\x04\x17'

                             msg_len = len(chord_id_str).to_bytes(4, 'big')
                             msg_type = 7
                             header = msg_len + header + msg_type.to_bytes(1, 'big')  + chord_id_str 
                             links[fd][0].send(header)


                         if(msgtype==8):
                             val = int.from_bytes(header[:4],"big")
                             n = successors[0]
                             chord_id_str = str(n).encode("utf-8")
                             header = b'\x04\x17'

                             msg_len = len(chord_id_str).to_bytes(4, 'big')
                             msg_type = 9
                             header = msg_len + header + msg_type.to_bytes(1, 'big')  + chord_id_str 
                             links[fd][0].send(header)

                          
main()


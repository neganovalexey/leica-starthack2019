import socket, select, sys
import argparse
import queue, threading
import time
from threading import Thread, Lock

def make_request(rpc, trId=None, params=[]):
    result = "\n%R1Q," + str(rpc)
    if trId != None:
        result += "," + str(trId+1)
    result += ":"
    result += ','.join(map(str, params))
    result += "\r\n"
    print(result)
    return bytes(result, "ascii")

def make_cancel_request():
    print('cancelling')
    return bytes("\nc\r\n", "ascii")

def parse_response(data):
    data = data.decode("ascii")
    data = data.split(':')
    hdr  = data[0].split(',')
    body = data[1].split(',')
    return {
          "RC_COM": int(hdr[1]),
          "TrId":   int(hdr[2]),
          "RC":     int(body[0]),
          "P":      body[1:-1],
    }

outputs = [queue.Queue(), queue.Queue()]

def do_request(sock, tid, rpc, params=[]):
    req = make_request(rpc, tid, params)
    sock.send(req)

def do_cancel_request(sock):
    req = make_cancel_request()
    sock.send(req)

parser = argparse.ArgumentParser(description='MS60 CLI')
parser.add_argument('--host',   default='192.168.12.59',  metavar='MS60 host')
parser.add_argument('--port',   default=1212,             metavar='MS60 port')
parser.add_argument('--rpc',    default=0,                metavar='RPC number')
parser.add_argument('--params', default="",               metavar='RPC parameters')
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((args.host, args.port))

def receive_responses():
    while True:
        rd, wr, err = select.select([sock], [], [])
        for s in rd:
            data = s.recv(4096)
            if not data:
                print('\nDisconnected from server')
                return
            else:
                out = parse_response(data)
                outputs[out["TrId"]-1].put(out)

reader = threading.Thread(target=receive_responses)
reader.start()

params = args.params.split(',') if len(args.params) > 0 else []
#out1 = do_request(sock, 0, args.rpc, params)
#out2 = do_request(sock, 1, args.rpc, params)
#print(outputs[0].get())
#print(outputs[1].get())

do_request(sock, 0, rpc=0)
time.sleep(1)
do_cancel_request(sock)
#do_request(sock, 0, 9029, params=[1,1,0]) # search
do_request(sock, 0, 9027, params=[-0.15, 0.52, '0', '0', '0']) # turn
for i in range(10):
    do_request(sock, 1, 17017, params=[2])
print('sent')
for i in range(10):
    print(outputs[1].get())
#make_cr(9027, params=[0.15, 0.55, '0', '0', '0'])
#time.sleep(3)
#make_cr(17019, params=[1])
#make_cr(17021, params=[1])
#make_cr(17017, params=[2])
#make_cr(17019, params=[5])
#time.sleep(3)

sock.close()
reader.join()

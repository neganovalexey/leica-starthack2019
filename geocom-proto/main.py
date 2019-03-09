import socket, select, sys
import argparse
import queue, threading
from threading import Thread, Lock

def make_request(rpc, trId=None, params=[]):
    result = "\n%R1Q," + str(rpc)
    if trId != None:
        result += "," + str(trId)
    result += ":"
    result += ','.join(map(str, params))
    result += "\r\n"
    print(result)
    return bytes(result, "ascii")

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

outputs = [queue.Queue(1), queue.Queue(1)]

def do(sock, q, rpc, params):
    req = make_request(rpc, q, params)
    sock.send(req)

parser = argparse.ArgumentParser(description='MS60 CLI')
parser.add_argument('--host',   default='192.168.43.131', metavar='MS60 host')
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
out1 = do(sock, 1, args.rpc, params)
out2 = do(sock, 2, args.rpc, params)
print(outputs[0].get())
print(outputs[1].get())

sock.close()
reader.join()

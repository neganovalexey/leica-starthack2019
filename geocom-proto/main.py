import socket
import argparse

def make_request(rpc, trId=None, params=[]):
    result = "\n%R1Q," + str(rpc)
    if trId != None:
        result += "," + str(trId)
    result += ":"
    result += ','.join(map(str, params))
    result += "\r\n"
    print(result)
    return bytes(result, "ascii")


parser = argparse.ArgumentParser(description='MS60 CLI')
parser.add_argument('--host',   default='192.168.43.131', metavar='MS60 host')
parser.add_argument('--port',   default=1212,             metavar='MS60 port')
parser.add_argument('--rpc',    default=0,                metavar='RPC number')
parser.add_argument('--params', default="",               metavar='RPC parameters')
args = parser.parse_args()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((args.host, args.port))

params = args.params.split(',') if len(args.params) > 0 else []
s.send(make_request(args.rpc, params=params))
s.close()

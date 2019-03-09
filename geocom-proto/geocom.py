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

def do_request(sock, rpc, params=[]):
    req = make_request(rpc, params=params)
    sock.send(req)
    data = s.recv(4096)
    if not data:
        print('\nDisconnected from server')
        return None
    else:
        return parse_response(data)

# Methods
# --------------------------------------------------------------------------------

def do_cancel_request(sock):
    req = make_cancel_request()
    sock.send(req)

# checking the communication
def COM_NullProc(sock):
    return do_request(sock, 0)

# turning the telescope to a specified position
def AUT_MakePositioning(sock, Hz, V, POSMode=0, ATRMode=0):
    return do_request(sock, 9027, [Hz, V, POSMode, ATRMode, 0])

# performing an automatic target search
def AUT_Search(sock, Hz_Area, V_Area):
    return do_request(sock, 9029, [Hz_Area, V_Area, 0])

# measuring Hz,V angles and a single distance
def BAP_MeasDistanceAngle(sock, DistMode):
    out = do_request(sock, 17017, [DistMode])
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "dHz":      float(params[0]),
            "dV":       float(params[1]),
            "dDist":    float(params[2]),
            "DistMode": int(params[3]),
        }
    return out

# setting the distance measurement program
def BAP_SetMeasPrg(sock, eMeasPrg):
    return do_request(sock, 17019, [eMeasPrg])

# setting the EDM type
def BAP_SetTargetType(sock, eTargetType):
    return do_request(sock, 17021, [eTargetType])

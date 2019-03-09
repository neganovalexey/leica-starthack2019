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
    body = data[1].rstrip().split(',')
    return {
          "RC_COM": int(hdr[1]),
          "TrId":   int(hdr[2]),
          "RC":     int(body[0]),
          "P":      body[1:],
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

# getting the coordinates of a measured point
def TMC_GetCoordinate(sock, WaitTime, Mode):
    out = do_request(sock, 2082, [WaitTime, Mode])
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "E":             float(params[0]),
            "N":             float(params[1]),
            "H":             float(params[2]),
            "CoordTime":     int(params[3]),
            "E-Cont":        float(params[4]),
            "N-Cont":        float(params[5]),
            "H-Cont":        float(params[6]),
            "CoordContTime": int(params[7]),
        }
    return out

# returning an angle and distance measurement
def TMC_GetSimpleMea(sock, WaitTime, Mode):
    out = do_request(sock, 2108, [WaitTime, Mode])
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "Hz":            float(params[0]),
            "V":             float(params[1]),
            "SlopeDistance": float(params[2]),
        }
    return out

# returning a complete angle measurement
def TMC_GetAngle1(sock, Mode):
    out = do_request(sock, 2003, [Mode])
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "Hz":              float(params[0]),
            "V":               float(params[1]),
            "AngleAccuracy":   float(params[2]),
            "AngleTime":       int(params[3]),
            "CrossIncline":    float(params[4]),
            "LengthIncline":   float(params[5]),
            "AccuracyIncline": float(params[6]),
            "InclineTime":     int(params[7]),
            "FaceDef":         int(params[8]),
        }
    return out

# returning a simple angle measurement
def TMC_GetAngle5(sock, Mode):
    out = do_request(sock, 2107, [Mode])
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "Hz": float(params[0]),
            "V":  float(params[1]),
        }
    return out

# returning a slope distance and hz-angle, v-angle
def TMC_QuickDist(sock):
    out = do_request(sock, 2117)
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "dHz":            float(params[0]),
            "dV":             float(params[1]),
            "dSlopeDistance": float(params[2]),
        }
    return out

# returning an angle, inclination and distance measurement
def TMC_GetFullMeas(sock, WaitTime, Mode):
    out = do_request(sock, 2167, [WaitTime, Mode])
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "Hz":        float(params[0]),
            "V":         float(params[1]),
            "AccAngle":  float(params[2]),
            "C":         float(params[3]),
            "L":         float(params[4]),
            "AccIncl":   float(params[5]),
            "SlopeDist": float(params[6]),
            "DistTime":  float(params[7]),
        }
    return out

# carrying out a distance measurement
# returning an angle, inclination and distance measurement
def TMC_DoMeasure(sock, Command, Mode):
    return do_request(sock, 2008, [Command, Mode])

# getting the EDM measurement mode
def TMC_GetEdmMode(sock):
    out = do_request(sock, 2021)
    if out != None and out['RC_COM'] == 0 and out['RC'] == 0:
        params = out["P"]
        out["P"] = {
            "Mode": int(params[0]),
        }
    return out

# setting EDM measurement modes
def TMC_SetEdmMode(sock, Mode):
    return do_request(sock, 2020, [Mode])

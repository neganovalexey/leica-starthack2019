from enum import Enum

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
    data = sock.recv(4096)
    if not data:
        print('\nDisconnected from server')
        return None
    else:
        return parse_response(data)

def is_ok(resp):
    return resp != None and resp['RC_COM'] == 0 and resp['RC'] == 0

# Enums
# --------------------------------------------------------------------------------

class TMC_INCLINE_PRG(Enum):
    TMC_MEA_INC   = 0
    TMC_AUTO_INC  = 1
    TMC_PLANE_INC = 2

class TMC_MEASURE_PRG(Enum):
    TMC_STOP         = 0
    TMC_DEF_DIST     = 1
    TMC_CLEAR        = 2
    TMC_SIGNAL       = 4
    TMC_DO_MEASURE   = 6
    TMC_RTRK_DIST    = 8
    TMC_RED_TRK_DIST = 10
    TMC_FREQUENCY    = 11

class EDM_MODE(Enum):
    EDM_MODE_NOT_USED   = 0
    EDM_SINGLE_TAPE     = 1
    EDM_SINGLE_STANDARD = 2
    EDM_SINGLE_FAST     = 3
    EDM_SINGLE_LRANGE   = 4
    EDM_SINGLE_SRANGE   = 5
    EDM_CONT_STANDARD   = 6
    EDM_CONT_DYNAMIC    = 7
    EDM_CONT_REFLESS    = 8
    EDM_CONT_FAST       = 9
    EDM_AVERAGE_IR      = 10
    EDM_AVERAGE_SR      = 11
    EDM_AVERAGE_LR      = 12
    EDM_PRECISE_IR      = 13
    EDM_PRECISE_TAPE    = 14

class BAP_MEASURE_PRG(Enum):
    BAP_NO_MEAS    = 0
    BAP_NO_DIST    = 1
    BAP_DEF_DIST   = 2
    BAP_CLEAR_DIST = 3
    BAP_STOP_TRK   = 4

class BAP_USER_MEASPRG(Enum):
    BAP_SINGLE_REF_STANDARD  = 0
    BAP_SINGLE_REF_FAST      = 1
    BAP_SINGLE_REF_VISIBLE   = 2
    BAP_SINGLE_RLESS_VISIBLE = 3
    BAP_CONT_REF_STANDARD    = 4
    BAP_CONT_REF_FAST        = 5
    BAP_CONT_RLESS_VISIBLE   = 6
    BAP_AVG_REF_STANDARD     = 7
    BAP_AVG_REF_VISIBLE      = 8
    BAP_AVG_RLESS_VISIBLE    = 9
    BAP_CONT_REF_SYNCHRO     = 10
    BAP_SINGLE_REF_PRECISE   = 11

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
def BAP_MeasDistanceAngle(sock, DistMode = 2):
    out = do_request(sock, 17017, [DistMode])
    if is_ok(out):
        params = out["P"]
        out["P"] = {
            "dHz":      float(params[0]),
            "dV":       float(params[1]),
            "dDist":    float(params[2]),
            "DistMode": int(params[3]),
        }
    else:
        out["P"] = {}
    return out

# setting the distance measurement program
def BAP_SetMeasPrg(sock, eMeasPrg):
    out = do_request(sock, 17019, [eMeasPrg.value])
    out["P"] = {}
    return out

# setting the EDM type
def BAP_SetTargetType(sock, eTargetType):
    out = do_request(sock, 17021, [eTargetType])
    out["P"] = {}
    return out

# getting the coordinates of a measured point
def TMC_GetCoordinate(sock, WaitTime, Mode):
    out = do_request(sock, 2082, [WaitTime, Mode])
    if is_ok(out):
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
    else:
        out["P"] = {}
    return out

# returning an angle and distance measurement
def TMC_GetSimpleMea(sock, WaitTime, Mode):
    out = do_request(sock, 2108, [WaitTime, Mode])
    if is_ok(out):
        params = out["P"]
        out["P"] = {
            "Hz":            float(params[0]),
            "V":             float(params[1]),
            "SlopeDistance": float(params[2]),
        }
    else:
        out["P"] = {}
    return out

# returning a complete angle measurement
def TMC_GetAngle1(sock, Mode):
    out = do_request(sock, 2003, [Mode])
    if is_ok(out):
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
    else:
        out["P"] = {}
    return out

# returning a simple angle measurement
def TMC_GetAngle5(sock, Mode):
    out = do_request(sock, 2107, [Mode])
    if is_ok(out):
        params = out["P"]
        out["P"] = {
            "Hz": float(params[0]),
            "V":  float(params[1]),
        }
    else:
        out["P"] = {}
    return out

# returning a slope distance and hz-angle, v-angle
def TMC_QuickDist(sock):
    out = do_request(sock, 2117)
    if is_ok(out):
        params = out["P"]
        out["P"] = {
            "dHz":            float(params[0]),
            "dV":             float(params[1]),
            "dSlopeDistance": float(params[2]),
        }
    else:
        out["P"] = {}
    return out

# returning an angle, inclination and distance measurement
def TMC_GetFullMeas(sock, WaitTime, Mode):
    out = do_request(sock, 2167, [WaitTime, Mode])
    if is_ok(out):
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
    else:
        out["P"] = {}
    return out

# carrying out a distance measurement
# returning an angle, inclination and distance measurement
def TMC_DoMeasure(sock, Command, Mode):
    out = do_request(sock, 2008, [Command, Mode])
    out["P"] = {}
    return out

# getting the EDM measurement mode
def TMC_GetEdmMode(sock):
    out = do_request(sock, 2021)
    if is_ok(out):
        params = out["P"]
        out["P"] = {
            "Mode": int(params[0]),
        }
    else:
        out["P"] = {}
    return out

# setting EDM measurement modes
def TMC_SetEdmMode(sock, Mode):
    out = do_request(sock, 2020, [Mode.value])
    out["P"] = {}
    return out

from serial import *
from time import *

ser = {}
inversion = 0

def opencom(Com, Vitesse, Parite, stopsBits, inverter):
    numport = str(Com)
    global inversion
    global ser
    ser[Com] = Serial()
    ser[Com].port = numport
    ser[Com].baudrate = Vitesse
    ser[Com].parity = Parite
    ser[Com].stopbits = stopsBits
    ser[Com].timeout = 0
    inversion = inverter
    ser[Com].open()

    txd(Com, 0)
    dtr(Com, 0)
    rts(Com, 0)
    sleep(0.01)

    if ser[Com].is_open:
        return 1
    else:
        return 0

def dcd(Com):
    if inversion:
        if ser[Com].cd == 1:
            return 0
        else:
            return 1
    else:
        if ser[Com].cd == 1:
            return 1
        else:
            return 0

def dsr(Com):
    if inversion:
        if ser[Com].dsr == 1:
            return 0
        else:
            return 1
    else:
        if ser[Com].dsr == 1:
            return 1
        else:
            return 0

def cts(Com):
    if inversion:
        if ser[Com].cts == 1:
            return 0
        else:
            return 1
    else:
        if ser[Com].cts == 1:
            return 1
        else:
            return 0

def ri(Com):
    if inversion:
        if ser[Com].ri == 1:
            return 0
        else:
            return 1
    else:
        if ser[Com].ri == 1:
            return 1
        else:
            return 0

def txd(Com, a):
    if inversion:
        if a == 0:
            ser[Com].break_condition = 1
        else:
            ser[Com].break_condition = 0
    else:
        if a == 0:
            ser[Com].break_condition = 0
        else:
            ser[Com].break_condition = 1

def dtr(Com, a):
    if inversion:
        if a == 0:
            ser[Com].dtr = 1
        else:
            ser[Com].dtr = 0
    else:
        if a == 0:
            ser[Com].dtr = 0
        else:
            ser[Com].dtr = 1

def rts(Com, a):
    if inversion:
        if a == 0:
            ser[Com].rts = 1
        else:
            ser[Com].rts = 0
    else:
        if a == 0:
            ser[Com].rts = 0
        else:
            ser[Com].rts = 1

def entreecom(Com):
    global ser
    result = 0
    if dcd(Com) == 1:
        result = result + 1
    if dsr(Com) == 1:
        result = result + 2
    if cts(Com) == 1:
        result = result + 4
    if ri(Com) == 1:
        result = result + 8
    return result

def decalers(Com, x):
    rts(Com, 0)
    for ci in range(len(x) - 1, -1, -1):
        masque = 128
        for i in range(7, -1, -1):
            dtr(Com, 0)
            if (masque & x[ci] == masque):
                txd(Com, 1)
            else:
                txd(Com, 0)
            dtr(Com, 1)
            masque = masque >> 1
        rts(Com, 1)

def decalere(Com, n):
    result = [0]
    result = result * n
    rts(Com, 0)
    for ci in range(n - 1, -1, -1):
        masque = 128
        for i in range(7, -1, -1):
            sleep(0.001)
            if dsr(Com) == 1:
                result[ci] = result[ci] | masque
            dtr(Com, 0)
            sleep(0.001)
            dtr(Com, 0)
            masque = masque >> 1
        rts(Com, 1)

def sendstring(Com, s):
    s = s + chr(13) + chr(10)
    ser[Com].write(s.encode('utf-8'))

def sendbyte(Com, s):
    ser[Com].write(s.encode('utf-8'))

def readstring(Com):
    result = ser[Com].read(80)
    return result.decode('utf-8')

def readbyte(Com):
    result = ser[Com].read()
    return result.decode('utf-8')

def closecom(Com):
    ser[Com].close()
# slbcom_linux.py
import serial
import time

class SLBCOM:
    def __init__(self):
        self.ser = None
        self.inversion = False

    # ---------------------------
    # OPEN PORT
    # ---------------------------
    def opencom(self, port, baudrate=9600, parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE, inversion=False):

        self.inversion = inversion

        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stopbits,
            timeout=0
        )

        # 🔥 IMPORTANT : état SAFE au démarrage
        self.txd(0)
        self.dtr(0)
        self.rts(0)

        time.sleep(0.05)

        return self.ser.is_open

    # ---------------------------
    # CONTROL LINES
    # ---------------------------
    def txd(self, value):
        # TXD simulé via BREAK (comme ton ancien code)
        state = bool(value)
        if self.inversion:
            state = not state
        self.ser.break_condition = state

    def dtr(self, value):
        state = bool(value)
        if self.inversion:
            state = not state
        self.ser.setDTR(state)

    def rts(self, value):
        state = bool(value)
        if self.inversion:
            state = not state
        self.ser.setRTS(state)

    # ---------------------------
    # SHIFT REGISTER 4094
    # ---------------------------
    def decalers(self, data):
        """
        data = liste de bytes [0xAA, 0xFF ...]
        """

        self.rts(0)  # STROBE OFF

        for byte in reversed(data):
            mask = 0x80

            for _ in range(8):

                self.dtr(0)  # CLOCK low

                bit = 1 if (byte & mask) else 0
                self.txd(bit)

                self.dtr(1)  # CLOCK rising edge
                mask >>= 1

        self.rts(1)  # STROBE ON (latch)

    # ---------------------------
    # CLOSE
    # ---------------------------
    def closecom(self):
        if self.ser:
            self.ser.close()


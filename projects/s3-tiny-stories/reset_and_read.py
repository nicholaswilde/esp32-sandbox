import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.setDTR(False)
ser.setRTS(True)
time.sleep(0.1)
ser.setDTR(False)
ser.setRTS(False)

start_time = time.time()
while time.time() - start_time < 15:
    char = ser.read(1)
    if char:
        print(char.decode('utf-8', errors='replace'), end='', flush=True)

import serial
import time

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    start_time = time.time()
    print("Listening to /dev/ttyACM0...")
    while time.time() - start_time < 15:
        line = ser.readline()
        if line:
            print(line.decode('utf-8', errors='replace'), end='')
except Exception as e:
    print("Error:", e)

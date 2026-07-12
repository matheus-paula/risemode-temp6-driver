import hid
import time
import psutil
import sys

VENDOR_ID = 0x1a2c
PRODUCT_ID = 0x4984

def get_cpu_temp():
    temps = psutil.sensors_temperatures()
    for sensor in ['coretemp', 'k10temp', 'zenpower']:
        if sensor in temps:
            return temps[sensor][0].current
    return 0

def get_cpu_usage():
    return psutil.cpu_percent(interval=None)

def split_digits(value):
    val = int(value)
    if val > 99: val = 99
    return [(val // 10) % 10, val % 10]

def open_device():
    paths = [b'1-2.4:1.0', b'1-2.4:1.1']
    for path in paths:
        try:
            device = hid.device()
            device.open_path(path)
            device.set_nonblocking(True)
            print(f"Successfully opened: {path}")
            return device
        except Exception as e:
            print(f"Could not open {path}: {e}")
    return None

def main():
    time.sleep(10)
    device = open_device()
    if not device:
        print("CRITICAL: Device not found.")
        sys.exit(1)

    try:
        device.write([0x07, 0xFD] + [0x00] * 62)
        
        while True:
            temp = get_cpu_temp()
            usage = get_cpu_usage()
            t_d = split_digits(temp)
            u_d = split_digits(usage)
            
            packet = [0] * 65
            packet[0] = 0x07
            packet[2], packet[3] = t_d[0], t_d[1]
            packet[6], packet[7] = u_d[0], u_d[1]
            
            device.write(packet)
            time.sleep(1)
    except Exception as e:
        print(f"Runtime error: {e}")
    finally:
        device.close()

if __name__ == "__main__":
    main()
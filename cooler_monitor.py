import hid
import time
import psutil

VENDOR_ID = 0x1a2c
PRODUCT_ID = 0x4984

def get_cpu_temp():
    temps = psutil.sensors_temperatures()
    for sensor in ['coretemp', 'k10temp', 'zenpower']:
        if sensor in temps:
            return temps[sensor][0].current
            
    if temps:
        return list(temps.values())[0][0].current
    return 0

def get_cpu_usage():
    return psutil.cpu_percent(interval=None)

def split_digits(value):
    val = int(value)
    if val > 99: 
        val = 99 
    return [(val // 10) % 10, val % 10]

def main():
    device = hid.device()
    try:
        device.open(VENDOR_ID, PRODUCT_ID)
        
        init_packet = [0x07, 0xFD] + [0x00] * 62
        device.write(init_packet)
        time.sleep(0.05)
        
        psutil.cpu_percent(interval=None) 
        
        while True:
            temp = get_cpu_temp()
            usage = get_cpu_usage()
            
            temp_digits = split_digits(temp)
            usage_digits = split_digits(usage)
            
            data_packet = [0] * 65
            data_packet[0] = 0x07  
            data_packet[1] = 0               
            data_packet[2] = temp_digits[0]  
            data_packet[3] = temp_digits[1]  
            data_packet[4] = 0x00            
            data_packet[5] = 0               
            data_packet[6] = usage_digits[0] 
            data_packet[7] = usage_digits[1] 
            
            device.write(data_packet)
            time.sleep(1)
            
    except IOError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        device.close()

if __name__ == "__main__":
    main()

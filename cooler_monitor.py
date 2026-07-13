import hid
import time
import psutil
import json

VENDOR_ID = 0x1a2c
PRODUCT_ID = 0x4984

last_energy = None
last_time = None

def load_config():
    default = {"temp_unit": "C", "metric_type": "usage"}
    try:
        with open("/opt/cooler-monitor/config.json", "r") as f:
            return json.load(f)
    except:
        return default

def get_cpu_temp():
    temps = psutil.sensors_temperatures()
    valid_temps = []
    for sensor in ['coretemp', 'k10temp', 'zenpower']:
        if sensor in temps:
            for entry in temps[sensor]:
                valid_temps.append(entry.current)
    if valid_temps:
        return max(valid_temps) 
    return 0

def get_cpu_usage():
    return psutil.cpu_percent(interval=None)

def get_cpu_power():
    global last_energy, last_time
    try:
        with open("/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj", "r") as f:
            current_energy = int(f.read().strip())
        current_time = time.time()
        
        if last_energy is None:
            last_energy = current_energy
            last_time = current_time
            return 0
        
        energy_diff = (current_energy - last_energy)
        time_diff = current_time - last_time
        
        last_energy = current_energy
        last_time = current_time
        
        if time_diff > 0:
            watts = (energy_diff / 1000000.0) / time_diff
            return int(watts)
        return 0
    except Exception as e:
        return 0

def split_3_digits(value):
    val = int(abs(value))
    if val > 999: val = 999
    return [(val // 100) % 10, (val // 10) % 10, val % 10]

def open_device():
    paths = [b'1-2.4:1.0', b'1-2.4:1.1']
    for path in paths:
        try:
            device = hid.device()
            device.open_path(path)
            device.set_nonblocking(True)
            return device
        except Exception:
            pass
    return None

def update_hardware_indicators(device, temp_unit, metric_type):
    """
    Sends the encrypted SET_REPORT payload to change the hardware LEDs.
    """
    mode_payloads = {
        ("F", "usage"): [0x07, 0x01, 0x00, 0x02, 0x11, 0x00, 0x00, 0x03],
        ("C", "usage"): [0x07, 0x00, 0x03, 0x06, 0x10, 0x00, 0x00, 0x02],
        ("F", "power"): [0x07, 0x00, 0x09, 0x06, 0x01, 0x00, 0x00, 0x08],
        ("C", "power"): [0x07, 0x00, 0x03, 0x07, 0x00, 0x00, 0x00, 0x09]
    }
    
    sequence = mode_payloads.get((temp_unit, metric_type), mode_payloads[("C", "power")])
    payload = sequence + [0x00] * (65 - len(sequence))
    
    try:
        device.send_feature_report(payload)
        print(f"[*] Hardware indicators set via Control Transfer: {temp_unit} / {metric_type}", flush=True)
    except Exception as e:
        print(f"[!] Failed to update indicators: {e}", flush=True)

def main():
    time.sleep(10)
    device = open_device()
    if not device:
        print("CRITICAL: Device not found.")

    try:
        device.write([0x07, 0xFD] + [0x00] * 62)
        time.sleep(0.1)

        while True:
            config = load_config()
            temp_unit = config.get("temp_unit", "C")
            metric_type = config.get("metric_type", "power")
            
            temp = get_cpu_temp()
            if temp_unit == "F":
                temp = (temp * 9/5) + 32
                
            if metric_type == "power":
                bottom_val = get_cpu_power()
            else:
                bottom_val = get_cpu_usage()

            t_d = split_3_digits(temp)
            b_d = split_3_digits(bottom_val)
            
            print(f"DEBUG LOG -> Temp: {int(temp)} | Bottom Metric: {bottom_val}", flush=True)
            
            packet = [0] * 65
            packet[0] = 0x07
            
            packet[1] = 0x00
            packet[2] = t_d[1]
            packet[3] = t_d[2]
            
            if temp_unit == "C" and metric_type == "usage":
                packet[4] = 0x10
                packet[7] = b_d[2]
            elif temp_unit == "F" and metric_type == "usage":
                packet[1] = 0x01
                packet[4] = 0x11
                packet[7] = b_d[2]
            elif temp_unit == "F" and metric_type == "power":
                packet[3] = 0x06
                packet[4] = 0x01
                packet[7] = 0x08  
            else:
                packet[3] = 0x07
                packet[7] = 0x09  

            device.write(packet)
            time.sleep(1)
            
    except Exception as e:
        print(f"Runtime error: {e}")
    finally:
        device.close()
        
if __name__ == "__main__":
    main()
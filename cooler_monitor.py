import hid
import time
import psutil
import json
import os

VENDOR_ID = 0x1a2c
PRODUCT_ID = 0x4984

last_energy = None
last_time = None
rapl_path = None

def load_config():
    default = {"temp_unit": "C", "metric_type": "usage", "debug_mode": False}
    try:
        with open("/opt/cooler-monitor/config.json", "r") as f:
            return json.load(f)
    except:
        return default

def get_cpu_temp():
    temps = psutil.sensors_temperatures()
    if not temps:
        return 0

    cpu_sensor_keys = ['coretemp', 'k10temp', 'zenpower', 'cpu_thermal']

    for sensor in cpu_sensor_keys:
        if sensor in temps:
            sensor_entries = temps[sensor]
            
            for entry in sensor_entries:
                label = entry.label.lower()
                if 'tctl' in label or 'tdie' in label or 'package' in label:
                    return entry.current
            
            valid_temps = [entry.current for entry in sensor_entries if entry.current > 0]
            if valid_temps:
                return max(valid_temps)

    all_valid_temps = []
    for sensor_name, entries in temps.items():
        for entry in entries:
            if entry.current > 0:
                all_valid_temps.append(entry.current)
                
    if all_valid_temps:
        return max(all_valid_temps)

    return 0

def get_cpu_usage():
    return int(psutil.cpu_percent(interval=None))

def get_cpu_power():
    global last_energy, last_time, rapl_path
    current_time = time.time()
    
    if rapl_path is None:
        try:
            if os.path.exists("/sys/class/powercap/"):
                for folder in os.listdir("/sys/class/powercap/"):
                    if folder.startswith("intel-rapl:"):
                        name_file = os.path.join("/sys/class/powercap/", folder, "name")
                        if os.path.exists(name_file):
                            with open(name_file, "r") as f:
                                if f.read().strip().startswith("package"):
                                    rapl_path = os.path.join("/sys/class/powercap/", folder, "energy_uj")
                                    break
        except Exception:
            pass
            
        if rapl_path is None and os.path.exists("/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"):
            rapl_path = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"

    if rapl_path and os.path.exists(rapl_path):
        try:
            with open(rapl_path, "r") as f:
                current_energy = int(f.read().strip())
            
            if last_energy is None:
                last_energy = current_energy
                last_time = current_time
                return 0
            
            energy_diff = current_energy - last_energy
            time_diff = current_time - last_time
            
            last_energy = current_energy
            last_time = current_time
            
            if energy_diff < 0:
                return 0
                
            if time_diff > 0:
                watts = (energy_diff / 1000000.0) / time_diff
                return int(watts)
        except Exception:
            pass

    try:
        if os.path.exists("/sys/class/hwmon/"):
            for hwmon in os.listdir("/sys/class/hwmon/"):
                hwmon_path = os.path.join("/sys/class/hwmon/", hwmon)
                for file in os.listdir(hwmon_path):
                    if file.startswith("power") and file.endswith("_input"):
                        with open(os.path.join(hwmon_path, file), "r") as f:
                            micro_watts = int(f.read().strip())
                            return int(micro_watts / 1000000.0)
    except Exception:
        pass

    return 0

def split_3_digits(value):
    val = int(abs(value))
    if val > 999: val = 999
    return [(val // 100) % 10, (val // 10) % 10, val % 10]

def open_device():
    for device_dict in hid.enumerate():
        if device_dict['vendor_id'] == VENDOR_ID and device_dict['product_id'] == PRODUCT_ID:
            try:
                device = hid.device()
                device.open_path(device_dict['path'])
                device.set_nonblocking(True)
                print(f"[+] Device connected at: {device_dict['path'].decode()}")
                return device
            except Exception as e:
                print(f"[!] Failed to open device at {device_dict['path']}: {e}")
                
    return None

def update_hardware_indicators(device, temp_unit, metric_type):
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
    print("Starting cooler monitor service...")
    device = None

    while True:
        if device is None:
            device = open_device()
            if not device:
                time.sleep(5)
                continue
            else:
                try:
                    device.write([0x07, 0xFD] + [0x00] * 62)
                    time.sleep(0.1)
                except Exception:
                    device.close()
                    device = None
                    continue

        try:
            config = load_config()
            temp_unit = config.get("temp_unit", "C")
            metric_type = config.get("metric_type", "power")
            debug_mode = config.get("debug_mode", False)
            
            temp = get_cpu_temp()
            if temp_unit == "F":
                temp = (temp * 9/5) + 32
                
            bottom_val = get_cpu_power() if metric_type == "power" else get_cpu_usage()

            t_d = split_3_digits(temp)
            b_d = split_3_digits(bottom_val)
            
            if debug_mode:
                print(f"DEBUG LOG -> Temp: {int(temp)} | Bottom Metric: {bottom_val}", flush=True)
            
            packet = [0] * 65
            packet[0] = 0x07
            
            packet[1] = 0x01 if temp_unit == "F" else 0x00
            packet[2] = t_d[1]
            packet[3] = t_d[2]
            
            if metric_type == "usage":
                packet[4] = 0x11 if temp_unit == "F" else 0x10
                packet[7] = b_d[2]
            else:
                packet[3] = 0x06 if temp_unit == "F" else 0x07
                packet[4] = 0x01
                packet[7] = b_d[2]

            device.write(packet)
            time.sleep(1)
            
        except OSError as e:
            print(f"USB connection dropped: {e}. Attempting to reconnect...")
            if device:
                device.close()
            device = None
            time.sleep(2)
        except Exception as e:
            print(f"Runtime error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
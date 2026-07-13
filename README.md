# Rise Mode Cooler Linux Monitor

A custom Linux driver and monitoring service for the Rise Mode hardware display (HID 1a2c:4984). This project bypasses the proprietary Windows-only driver, allowing you to display real-time CPU temperature and usage stats on your hardware's 7-segment display under Linux.


Tested with the model Rise Mode Temp 6 White

![](images/risemode-temp6.jpg)

## Technical Overview
The display communicates via a 65-byte HID payload. After reverse-engineering the protocol, it was discovered that the hardware bypasses the need for its built-in XOR obfuscation if the exact payload map from the Windows Control Transfers (`SET_REPORT`) is sent through the standard `Interrupt OUT` stream. This service sends a single unified payload that controls both the numeric 7-segment digit values and the hardware LEDs (Celsius/Fahrenheit, Power/Usage indicators) simultaneously.

## Prerequisites
- OS: Ubuntu 24.04 LTS (or similar Linux distribution)
- Dependencies: `psutil`, `hidapi`

## QuickInstall
For a deployment in one line, run the following command in your terminal (ensures the script is downloaded and executed instantly):

```bash
curl -sLS https://raw.githubusercontent.com/matheus-paula/risemode-temp6-driver/master/install.sh | sudo bash
```

## Manual Installation
Should you prefer to install it by coping files manually, follow the steps below.

### 1. Disable Auto-Driver Download
The device may attempt to run a script at boot to download its standard Windows driver. To prevent this from happening, blacklist the identifier:
```bash
sudo nano /etc/modprobe.d/blacklist-cooler.conf
```
add: 
```text
options usbhid quirks=0x1a2c:0x4984:0x04
```
```bash
sudo update-initramfs -u
```

## Installation

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install python3-pip
pip3 install psutil hidapi
```

### 2. Deploy Script
Move the script to a system directory:
```bash
sudo mkdir -p /opt/cooler-monitor
sudo cp cooler_monitor.py /opt/cooler-monitor/
```

### 3. Configure Indicators (optional)
The script now supports switching between Celsius/Fahrenheit and Watts/Usage percentage. Create a configuration file:
```bash
sudo nano /opt/cooler-monitor/config.json
```
Add the following JSON :
```json
{
    "temp_unit": "C",
    "metric_type": "usage"
}
```
*Supported values:*
- `temp_unit`: `"C"` or `"F"`
- `metric_type`: `"power"` (Watts) or `"usage"` (%)


### 4. Deploy the Service
1. Create the service file: 

```bash
sudo nano /etc/systemd/system/cooler-monitor.service
```
2. Paste the following configuration:

```ini
[Unit]
Description=Rise Mode Cooler Hardware Monitor
After=network.target

[Service]
CapabilityBoundingSet=CAP_SYS_RAWIO
AmbientCapabilities=CAP_SYS_RAWIO

Type=simple
User=root
Group=root
ExecStart=/usr/bin/python3 /opt/cooler-monitor/cooler_monitor.py
WorkingDirectory=/opt/cooler-monitor/
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```
3. Reload and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cooler-monitor
sudo systemctl start cooler-monitor
```

## Usage
Once enabled, the service runs automatically in the background. To change the display layout after initialization, simply edit `/opt/cooler-monitor/config.json`. The script will automatically pick up the new values on its next loop. 

You can manage the service using standard systemd commands:
* Check status: `sudo systemctl status cooler-monitor`** View logs: `journalctl -u cooler-monitor -f`
* Restart: `sudo systemctl restart cooler-monitor`

## License
This project is open-source and intended for non-commercial hardware interoperability.
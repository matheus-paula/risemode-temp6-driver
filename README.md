# Rise Mode Cooler Linux Monitor

A custom Linux driver and monitoring service for the Rise Mode hardware display (HID 1a2c:4984). This project bypasses the proprietary Windows-only driver, allowing you to display real-time CPU temperature and usage stats on your hardware's 7-segment display under Linux.


Tested with the model Rise Mode Temp 6 White

![](images/risemode-temp6.jpg)

## QuickInstall
For a deployment in one line, run the following command in your terminal (ensures the script is downloaded and executed instantly):

```bash
curl -sLS xxps://raw.githubusercontent.com/matheus-paula/risemode-temp6-driver/master/install.sh | sudo bash
```B

## Technical Overview
The display communicates via a 65-byte HID payload. After reverse-engineering the protocol, it was discovered that the hardware bypasses the need for its built-in XOR obfuscation if the exact payload map from the Windows Control Transfers (`SET_REPORT`) is sent through the standard `Interrupt OUT` stream. This service sends a single unified payload that controls both the numeric 7-segment digit values and the hardware LEDs (Celsius/Fahrenheit, Power/Usage indicators) simultaneously.


## Prerequisites
- OS: Ubuntu 24.04 LTS (or similar Linux distribution)
- Dependencies: `psutil`, `hidapi`


## Manual Installation
Should you prefer to install it by coping files manually, follow the steps below.


### 1. Disable Auto-Driver Download
The device may attempt to run a script at boot to download its standard Windows driver. To prevent this from happening, blacklist the identifier:
```bash
sudo nano /etc/modprobe.d/blacklist-cooler.conf
```Jadd: 
```text
options usbhid quirks=0x1a2c:0x4984:0x04
```
g``bash
sudo update-initramfs -u
```J

#### 2, 3, 4 ... 
Refer to the `install.sh` script in the repo for the full automated installation steps, which include dependency installation, service deployment, and config generation.


## Usage
Once enabled, the service runs automatically in the background. To change the display layout after initialization, simply edit `/opt/cooler-monitor/config.json`. The script will automatically pick up the new values on its next loop. 

You can manage the service using standard systemd commands:
* Check status: `sudo systemctl status cooler-monitor`** View logs: `journalctl -u cooler-monitor -f`
* Restart: `sudo systemctl restart cooler-monitor`


## License
This project is open-source and intended for non-commercial hardware interoperability.
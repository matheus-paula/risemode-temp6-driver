# Rise Mode Cooler Linux Monitor

A custom Linux driver and monitoring service for the Rise Mode hardware display (HID 1a2c:4984). This project bypasses the proprietary Windows-only driver, allowing you to display real-time CPU temperature and usage stats on your hardware's 7-segment display under Linux.

Tested with the model Rise Mode Temp 6 White

![](images/risemode-temp6.jpg)

## Technical Overview
The display communicates via a 65-byte HID packet stream. It utilizes a custom initialization handshake (0x07, 0xFD) followed by a precise 7-segment digit-mapping format that prevents hardware rejection by observing specific flags and padding requirements.

## Prerequisites
- OS: Ubuntu 24.04 LTS (or similar Linux distribution) (Tested on Ubuntu 26.04 LTS)
- Dependencies: psutil, hidapi
- Permissions: Rootless access via udev

## Installation

### 1. Install Dependencies
sudo apt update
sudo apt install python3-pip
pip3 install psutil hidapi

### 2. Permissions (Udev Rule)
To allow your user account to communicate with the USB device without sudo, create a udev rule:

echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="4984", MODE="0666"' | sudo tee /etc/udev/rules.d/99-cooler-monitor.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

### 3. Deploy the Service
1. Place your script: Ensure cooler_monitor.py is in your home directory (/home/<username>/cooler_monitor.py).
2. Create the service file:
sudo nano /etc/systemd/system/cooler-monitor.service

3. Paste the following configuration:
[Unit]
Description=Rise Mode Cooler Hardware Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/%u/cooler_monitor.py
WorkingDirectory=/home/%u/
Restart=always
User=%u
Group=%u
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target

4. Enable the service:
sudo systemctl daemon-reload
sudo systemctl enable cooler-monitor
sudo systemctl start cooler-monitor

## Usage
Once enabled, the service runs automatically in the background. You can manage it using standard systemd commands:
* Check status: sudo systemctl status cooler-monitor
* View logs: journalctl -u cooler-monitor -f
* Restart: sudo systemctl restart cooler-monitor

## License
This project is open-source and intended for non-commercial hardware interoperability.

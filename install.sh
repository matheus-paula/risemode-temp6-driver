#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "[!] Please run this script as root (use sudo)"
  exit 1
fi

echo "[*] Ensuring system configuration..."

BLACKLIST_FILE="/etc/modprobe.d/blacklist-cooler.conf"
QUIRK="options usbhid quirks=0x1a2c:0x4984:0x04"
if [ ! -f "$BLACKLIST_FILE" ] || ! grep -q "$QUIRK" "$BLACKLIST_FILE"; then
    echo "$QUIRK" >> "$BLACKLIST_FILE"
    update-initramfs -u
    echo "[+] Quirk added to blacklist."
fi

echo "[*] Installing dependencies..."
apt update
apt install -y python3-pip
pip3 install psutil hidapi --break-system-packages 

mkdir -p /opt/cooler-monitor

if [ -f "cooler_monitor.py" ]; then
    cp cooler_monitor.py /opt/cooler-monitor/
    echo "[+] Script deployed."
fi

if [ ! -f "/opt/cooler-monitor/config.json" ]; then
    echo '{
    "temp_unit": "C",
    "metric_type": "power",
    "debug_mode": false
}' > /opt/cooler-monitor/config.json
    echo "[+] Default configuration created with debug_mode: false."
fi

cat <<EOF > /etc/systemd/system/cooler-monitor.service
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
EOF

echo "[*] Enabling and starting service..."
systemctl daemon-reload
systemctl enable cooler-monitor
systemctl restart cooler-monitor

echo "[+] Installation/Update complete."
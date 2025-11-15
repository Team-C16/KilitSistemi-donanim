[Unit]
Description=Lock Service
After=multi-user.target network-online.target qrGenerator.service
Requires=network-online.target qrGenerator.service

[Service]
Type=simple
User=root
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=/bin/bash -c "while ! xrandr; do sleep 1; done; /usr/bin/python3 /KilitSistemi-donanim/mqtt-kilitKodu.py"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target


[Unit]
Description=QR Generator Service
After=network-online.target
Requires=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/xinit /usr/bin/python3 /KilitSistemi-donanim/tkinterDeneme.py -- :0
Restart=always
StandardOutput=journal

[Install]
WantedBy=multi-user.target

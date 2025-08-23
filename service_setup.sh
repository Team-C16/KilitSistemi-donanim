apt update -y
apt install python3 -y
apt install pip -y
apt-get install xosd-bin -y
pip install requests qrcode qrcode[pil] pygame jwt time --break-system-packages


DIRECTORY="/KilitSistemi-donanim"

if [ -d "$DIRECTORY" ]; then
stty -echo
echo "\n ---------------------------------------------------- \n \n \n Please Enter JWT Secret"
read -p "" jwtsecret
stty echo

echo "\n ---------------------------------------------------- \n \n \n Please Enter Rooom ID"
read -p "" roomid

echo "\n ---------------------------------------------------- \n \n \n Please Enter Nodejs for raspberrys IP"
read -p "" nodeip


qrfile="$DIRECTORY/qrGenerator.py"

escaped_jwtsecret=$(echo "$jwtsecret" | sed 's/[&/\]/\\&/g')

# 'JWT_SECRET' yazan yeri kullanıcı şifresi ile değiştirip, geçici dosyaya yaz
sed "s/\"JWT_SECRET\"/\"$escaped_jwtsecret\"/g" "$qrfile" > tempfile

# Orijinal dosyayı geçici dosyayla değiştir
mv tempfile "$qrfile"

# room_id değerini değiştirmek için sed kullanıyoruz
sed -i "s/^room_id = [0-9]\+/room_id = $roomid/" "$qrfile"

#ip yi girmek için sed kullanıyoruz
sed -i "s/^raspberryNodeip = '.*'/raspberryNodeip = '$nodeip'/" "$qrfile"



lockfile="$DIRECTORY/kilitKodu.py"

sed "s/\"JWT_SECRET\"/\"$escaped_jwtsecret\"/g" "$lockfile" > tempfile

sed -i "s|^raspberryNodeip = '.*'|raspberryNodeip = '$nodeip'|" "$lockfile"

# Orijinal dosyayı geçici dosyayla değiştir
mv tempfile "$lockfile"

#QR Servis adı
QR_SERVICE_NAME="qrGenerator"

#QR Python script yolu
QR_PYTHON_SCRIPT="$DIRECTORY/qrGenerator.py"

#Kilit Servis adı
LOCK_SERVICE_NAME="lock"

#Kilit Python script yolu
LOCK_PYTHON_SCRIPT="$DIRECTORY/kilitKodu.py"

# Kullanıcı adı (genellikle 'pi')
USER_NAME="pi"

# Servis dosyasını oluştur
QR_SERVICE_FILE="/etc/systemd/system/$QR_SERVICE_NAME.service"

echo "Servis dosyası oluşturuluyor: $QR_SERVICE_FILE"

sudo bash -c "cat > $QR_SERVICE_FILE" <<EOL
[Unit]
Description=QR Generator Service
After=default.target
Requires=display-manager.service

[Service]
Type=simple
User=$USER_NAME
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u $USER_NAME)
ExecStart=/bin/bash -c "while ! xrandr; do sleep 1; done; /usr/bin/python3 $QR_PYTHON_SCRIPT"
Restart=always

[Install]
WantedBy=default.target
EOL

# Servisi etkinleştir ve başlat
echo "QR Servis etkinleştiriliyor ve başlatılıyor..."
sudo systemctl daemon-reload
sudo systemctl enable $QR_SERVICE_NAME.service
sudo systemctl start $QR_SERVICE_NAME.service

# Servis dosyasını oluştur
LOCK_SERVICE_FILE="/etc/systemd/system/$LOCK_SERVICE_NAME.service"

echo "Servis dosyası oluşturuluyor: $LOCK_SERVICE_FILE"

sudo bash -c "cat > $LOCK_SERVICE_FILE" <<EOL
[Unit]
Description=Lock Service
After=graphical.target
Requires=display-manager.service


[Service]
Type=simple
User=$USER_NAME
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority
ExecStartPre=/usr/bin/xhost +SI:localuser:$USER_NAME
ExecStart=/bin/bash -c "while ! xrandr; do sleep 1; done; sudo python $LOCK_PYTHON_SCRIPT"
Restart=always

[Install]
WantedBy=multi-user.target
EOL



# Servisi etkinleştir ve başlat
echo "LOCK Servis etkinleştiriliyor ve başlatılıyor..."
sudo systemctl daemon-reload
sudo systemctl enable $LOCK_SERVICE_NAME.service
sudo systemctl start $LOCK_SERVICE_NAME.service




#Parmak izi Servis adı
FINGERPRINT_SERVICE_NAME="fingerprint"

#Parmak izi Python script yolu
FINGERPRINT_PYTHON_SCRIPT="$DIRECTORY/fingerprint.py"

FINGERPRINT_SERVICE_FILE="/etc/systemd/system/$FINGERPRINT_SERVICE_NAME.service"

echo "Servis dosyası oluşturuluyor: $FINGERPRINT_SERVICE_FILE"

sudo bash -c "cat > $FINGERPRINT_SERVICE_FILE" <<EOL
[Unit]
Description=QR Generator Service
After=default.target
Requires=display-manager.service

[Service]
Type=simple
User=$USER_NAME
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u $USER_NAME)
ExecStart=/bin/bash -c "while ! xrandr; do sleep 1; done; /usr/bin/python3 $FINGERPRINT_PYTHON_SCRIPT"
Restart=always

[Install]
WantedBy=default.target
EOL

# Servisi etkinleştir ve başlat
echo "FINGER Prınt Servis etkinleştiriliyor ve başlatılıyor..."
sudo systemctl daemon-reload
sudo systemctl enable $FINGERPRINT_SERVICE_NAME.service
sudo systemctl start $FINGERPRINT_SERVICE_NAME.service



# Servis durumu kontrol
sudo systemctl status $LOCK_SERVICE_NAME.service
sudo systemctl status $QR_SERVICE_NAME.service
sudo systemctl status $FINGERPRINT_SERVICE_NAME.service

else
git clone https://github.com/Team-C16/KilitSistemi-donanim /KilitSistemi-donanim
exec "$0"
fi

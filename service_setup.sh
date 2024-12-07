apt update -y
apt install python3 -y
apt install pip -y
pip install requests qrcode[pil] pygame io jwt time --break-system-packages


DIRECTORY="/BAP100-proje-donanim"

if [ -d "$DIRECTORY" ]; then
stty -echo
echo "\n ---------------------------------------------------- \n \n \n Please Enter JWT Secret"
read -p "" jwtsecret
stty echo
echo "$jwtsecret"

echo "\n ---------------------------------------------------- \n \n \n Please Enter Rooom ID"
read -p "" roomid


file="$DIRECTORY/qrGenerator.py"

escaped_jwtsecret=$(echo "$jwtsecret" | sed 's/[&/\]/\\&/g')

# 'JWT_SECRET' yazan yeri kullanıcı şifresi ile değiştirip, geçici dosyaya yaz
sed "s/\"JWT_SECRET\"/\"$escaped_jwtsecret\"/g" "$file" > tempfile

# Orijinal dosyayı geçici dosyayla değiştir
mv tempfile "$file"

# room_id değerini değiştirmek için sed kullan
sed -i "s/room_id\": [0-9]\+/room_id\": $roomid/g" "$file"

# Servis adı
SERVICE_NAME="qr_generator"

# Python script yolu
PYTHON_SCRIPT="$DIRECTORY/qrGenerator.py"

# Kullanıcı adı (genellikle 'pi')
USER_NAME="pi"

# Servis dosyasını oluştur
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

echo "Servis dosyası oluşturuluyor: $SERVICE_FILE"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=QR Generator Service
After=graphical.target


[Service]
Type=simple
User=$USER_NAME
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u $USER_NAME)
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 $PYTHON_SCRIPT
Restart=always

[Install]
WantedBy=graphical.target
EOL

# Servisi etkinleştir ve başlat
echo "Servis etkinleştiriliyor ve başlatılıyor..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME.service
sudo systemctl start $SERVICE_NAME.service

# Servis durumu kontrol
sudo systemctl status $SERVICE_NAME.service

else
git clone https://github.com/Kerem-Yavuz/BAP100-proje-donanim /BAP100-proje-donanim
exec "$0"
fi

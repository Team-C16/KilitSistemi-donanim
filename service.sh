#!/bin/bash

# --- 1. Temel Kurulumlar ---
echo "Sistem paketleri güncelleniyor ve gerekli kütüphaneler kuruluyor..."
apt update -y
apt install git -y
apt install python3 -y
apt install pip -y
apt-get install xosd-bin -y
apt install python3-rpi.gpio -y
apt install python3-gpiozero -y
apt install x11-xserver-utils -y
apt install xinit -y

# Python paketleri
pip install requests qrcode qrcode[pil] pygame jwt time paho-mqtt python-dotenv --break-system-packages

DIRECTORY="/KilitSistemi-donanim"
SECRETS_FILE="/etc/secrets.conf"

# --- 2. Klasör ve Repo Kontrolü ---
if [ ! -d "$DIRECTORY" ]; then
    echo "Proje klasörü bulunamadı, Git'ten çekiliyor..."
    git clone https://github.com/Team-C16/KilitSistemi-donanim "$DIRECTORY"
    
    echo "Repo çekildi. Script yeniden başlatılıyor..."
    exec "$0"
    exit
fi

# --- 3. Kullanıcıdan Değişkenleri Alma ---
echo -e "\n\n----------------------------------------------------"
echo "Lütfen Sistem Ayarlarını Giriniz"
echo "----------------------------------------------------"

# Şifreli giriş
stty -echo
echo "Lütfen JWT Secret giriniz:"
read jwt_secret
stty echo

echo "Lütfen Room ID giriniz:"
read room_id

echo "Lütfen Raspberry Node IP giriniz:"
read nodeip

echo "Lütfen MQTT Broker IP giriniz:"
read mqttbrokerip

echo "Lütfen MQTT Broker Port giriniz (Varsayılan 1883):"
read mqttbrokerport

if [ -z "$mqttbrokerport" ]; then
    mqttbrokerport=1883
fi

# --- 4. Secrets Dosyasını Oluşturma ---
echo "Konfigürasyon dosyası oluşturuluyor: $SECRETS_FILE"

cat > secrets_temp.conf <<EOL
jwt_secret=$jwt_secret
room_id=$room_id
nodeip=$nodeip
mqttbrokerip=$mqttbrokerip
mqttbrokerport=$mqttbrokerport
SECRET_KEY=$jwt_secret
BRANCH_NAME=main
DESTINATION_DIR=$DIRECTORY
SERVICE_QR=qrGenerator
SERVICE_LOCK=lock
EOL

mv secrets_temp.conf "$SECRETS_FILE"
chown root:root "$SECRETS_FILE"
chmod 600 "$SECRETS_FILE"

echo "Güvenlik ayarları tamamlandı."

# --- 5. DÜZELTİLMİŞ Dosya Seçimi Fonksiyonu ---
# Hata burada giderildi: Menü yazıları >&2 ile ekrana basılıyor, 
# sadece dosya yolu değişkene gidiyor.

select_file() {
    local pattern=$1
    local prompt_message=$2
    local files=($(ls $DIRECTORY/$pattern 2>/dev/null))

    if [ ${#files[@]} -eq 0 ]; then
        echo "HATA: $pattern formatında dosya bulunamadı!" >&2
        exit 1
    fi

    echo -e "\n$prompt_message" >&2
    local i=1
    for file in "${files[@]}"; do
        echo "[$i] $(basename "$file")" >&2
        ((i++))
    done

    local choice
    # Kullanıcıdan input alırken promptu da stderr'e verelim
    read -p "Seçim numarasını giriniz: " choice >&2
    
    local index=$((choice-1))
    
    if [ -n "${files[$index]}" ]; then
        # SADECE BURASI DEĞİŞKENE GİDECEK
        echo "${files[$index]}"
    else
        echo "Geçersiz seçim!" >&2
        exit 1
    fi
}

# --- 6. Script Seçimleri ---

# Değişken atamaları artık temiz olacak
SELECTED_QR=$(select_file "*qrGenerator.py" "Kullanılacak QR Generator Scriptini Seçiniz:")
echo "Seçilen QR Script: $SELECTED_QR"

SELECTED_LOCK=$(select_file "*kilitKodu.py" "Kullanılacak Kilit Kodu Scriptini Seçiniz:")
echo "Seçilen Kilit Script: $SELECTED_LOCK"

SELECTED_FINGERPRINT=$(select_file "*fingerprint.py" "Kullanılacak Parmak İzi Scriptini Seçiniz:")
echo "Seçilen Parmak İzi Script: $SELECTED_FINGERPRINT"

SELECTED_UPDATE="$DIRECTORY/mqtt-update.py"

# --- 7. Servis Dosyalarının Oluşturulması ---

# --- QR SERVICE ---
QR_SERVICE_FILE="/etc/systemd/system/qrGenerator.service"
echo "Servis oluşturuluyor: $QR_SERVICE_FILE"

cat > $QR_SERVICE_FILE <<EOL
[Unit]
Description=QR Generator Service
After=network-online.target
Requires=network-online.target

[Service]
Type=simple
User=root
EnvironmentFile=$SECRETS_FILE
ExecStart=/usr/bin/xinit /usr/bin/python3 $SELECTED_QR -- :0
Restart=always
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOL


# --- LOCK SERVICE ---
LOCK_SERVICE_FILE="/etc/systemd/system/lock.service"
echo "Servis oluşturuluyor: $LOCK_SERVICE_FILE"

cat > $LOCK_SERVICE_FILE <<EOL
[Unit]
Description=Lock Service
After=multi-user.target network-online.target qrGenerator.service
Requires=network-online.target qrGenerator.service

[Service]
Type=simple
User=root
EnvironmentFile=$SECRETS_FILE
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=/bin/bash -c "/usr/bin/python3 $SELECTED_LOCK"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL


# --- FINGERPRINT SERVICE ---
FINGERPRINT_SERVICE_FILE="/etc/systemd/system/fingerprint.service"
echo "Servis oluşturuluyor: $FINGERPRINT_SERVICE_FILE"

cat > $FINGERPRINT_SERVICE_FILE <<EOL
[Unit]
Description=Fingerprint Reader Service
After=default.target
Requires=display-manager.service

[Service]
Type=simple
User=root
EnvironmentFile=$SECRETS_FILE
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStartPre=/usr/bin/xhost +SI:localuser:root
ExecStart=/bin/bash -c "while ! xrandr; do sleep 1; done; /usr/bin/python3 $SELECTED_FINGERPRINT"
Restart=always

[Install]
WantedBy=default.target
EOL


# --- UPDATE LISTENER SERVICE ---
UPDATE_SERVICE_FILE="/etc/systemd/system/updateListener.service"
echo "Servis oluşturuluyor: $UPDATE_SERVICE_FILE"

cat > $UPDATE_SERVICE_FILE <<EOL
[Unit]
Description=MQTT Update Listener Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$DIRECTORY
EnvironmentFile=$SECRETS_FILE
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 $SELECTED_UPDATE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# --- 8. Servisleri Başlatma ---

echo "Servisler yenileniyor ve başlatılıyor..."
systemctl daemon-reload

systemctl enable qrGenerator.service
systemctl enable lock.service
systemctl enable fingerprint.service
systemctl enable updateListener.service

systemctl restart qrGenerator.service
systemctl restart lock.service
systemctl restart fingerprint.service
systemctl restart updateListener.service

echo "----------------------------------------------------"
echo "Kurulum Tamamlandı!"
echo "----------------------------------------------------"

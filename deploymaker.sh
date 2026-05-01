#!/bin/bash

# Kullanım:
# 1. Dev imajı küçült ve hazırla: sudo ./deploymaker.sh -s orijinal_dev.img hazir_deploy.img
# 2. Zaten küçük olan imajdan kopya çıkar ve hazırla: sudo ./deploymaker.sh kucuk_orijinal.img hazir_deploy.img

SHRINK_MODE=0

# Parametreleri parse et
while getopts "s" opt; do
  case ${opt} in
    s ) SHRINK_MODE=1 ;;
    \? ) echo "Kullanım: sudo $0 [-s] <girdi_imaji.img> <cikti_imaji.img>"; exit 1 ;;
  esac
done
shift $((OPTIND -1))

INPUT_IMG="$1"
OUTPUT_IMG="$2"
MOUNT_DIR="/mnt/img_root"

if [ "$EUID" -ne 0 ]; then
  echo "[-] Lütfen scripti root yetkileriyle çalıştırın (sudo $0 ...)"
  exit 1
fi

if [ -z "$INPUT_IMG" ] || [ -z "$OUTPUT_IMG" ]; then
  echo "[-] Hata: Girdi ve çıktı imaj dosyalarını belirtmelisiniz."
  echo "Kullanım: sudo $0 [-s] <girdi_imaji.img> <cikti_imaji.img>"
  exit 1
fi

if [ ! -f "$INPUT_IMG" ]; then
  echo "[-] Hata: Girdi imajı ($INPUT_IMG) bulunamadı."
  exit 1
fi

echo "========================================"
if [ "$SHRINK_MODE" -eq 1 ]; then
    echo "[*] SHRINK MODU AKTİF: Orijinal imaj küçültülerek yeni dosya oluşturuluyor..."

    # Bazzite uyumlu PiShrink kontrolü (Sistem dizini yerine mevcut klasörü kullanır)
    PISHRINK_PATH="./pishrink.sh"
    if [ ! -f "$PISHRINK_PATH" ]; then
        echo "[!] pishrink.sh bulunamadı. Mevcut klasöre indiriliyor..."
        wget -qO "$PISHRINK_PATH" https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
        chmod +x "$PISHRINK_PATH"
    fi

    # PiShrink'e iki argüman verirsen orijinali bozmadan küçültülmüş yeni dosya yaratır
    "$PISHRINK_PATH" "$INPUT_IMG" "$OUTPUT_IMG"

    if [ $? -ne 0 ]; then
        echo "[-] PiShrink işlemi başarısız oldu."
        exit 1
    fi
else
    echo "[*] STANDART MOD: Girdi imajının kopyası oluşturuluyor..."
    # --sparse=always parametresi boş alanları kopyalamaz, işlemi inanılmaz hızlandırır
    cp --sparse=always "$INPUT_IMG" "$OUTPUT_IMG"
fi
echo "========================================"

echo "[*] İşlem yapılacak imaj loop cihazına bağlanıyor: $OUTPUT_IMG"
LOOP_DEV=$(losetup -Pf --show "$OUTPUT_IMG")

if [ -z "$LOOP_DEV" ]; then
  echo "[-] Hata: Loop cihazı oluşturulamadı."
  exit 1
fi

ROOT_PART="${LOOP_DEV}p2"

echo "[*] $ROOT_PART mount ediliyor..."
mkdir -p "$MOUNT_DIR"
mount "$ROOT_PART" "$MOUNT_DIR"

echo "[*] SSH Host sertifikaları ve hassas veriler temizleniyor..."
rm -f "$MOUNT_DIR"/etc/ssh/ssh_host_*

echo "[*] İlk açılışta SSH keylerinin yeniden üretilmesi için otomatik servis ekleniyor..."
cat << 'EOF' > "$MOUNT_DIR/etc/systemd/system/generate-ssh-keys.service"
[Unit]
Description=Generate SSH keys on first boot
Before=ssh.service
ConditionPathExists=!/etc/ssh/ssh_host_rsa_key

[Service]
Type=oneshot
ExecStart=/usr/bin/ssh-keygen -A
ExecStartPost=/bin/systemctl disable generate-ssh-keys.service

[Install]
WantedBy=multi-user.target
EOF

mkdir -p "$MOUNT_DIR/etc/systemd/system/multi-user.target.wants/"
ln -sf /etc/systemd/system/generate-ssh-keys.service "$MOUNT_DIR/etc/systemd/system/multi-user.target.wants/generate-ssh-keys.service"

rm -f "$MOUNT_DIR"/etc/secrets.conf

echo "[*] Machine-ID sıfırlanıyor..."
if [ -f "$MOUNT_DIR"/etc/machine-id ]; then
    truncate -s 0 "$MOUNT_DIR"/etc/machine-id
fi
if [ -f "$MOUNT_DIR"/var/lib/dbus/machine-id ]; then
    rm -f "$MOUNT_DIR"/var/lib/dbus/machine-id
    ln -s /etc/machine-id "$MOUNT_DIR"/var/lib/dbus/machine-id
fi

echo "[*] Dosya sistemi senkronize ediliyor ve unmount yapılıyor..."
sync
umount "$MOUNT_DIR"
losetup -d "$LOOP_DEV"
rmdir "$MOUNT_DIR"

echo "[+] İŞLEM BAŞARILI!"
echo "[+] Orijinal imaj: $INPUT_IMG (Dokunulmadı)"
echo "[+] Yeni ve temizlenmiş dağıtım imajı: $OUTPUT_IMG"

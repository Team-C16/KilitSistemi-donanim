Öncelikle dietpi-config üzerinden wifi i kapat aç yapmak mantıklı olucaktır bu hem dosyaları oluşturur hemde gerekli şeyleri indirir fakat bu aşağıda yapılan bütün ayarları sıfırlayabilir o yüzden tekrar kontrol edin

# wpa_supplicant.conf

```
country=TR
ctrl_interface=DIR=/run/wpa_supplicant GROUP=netdev

update_config=1
network={
        ssid="eduroam"
        scan_ssid=1
        key_mgmt=WPA-EAP
        eap=PEAP
        identity="randevu.oys@izu.edu.tr"
        password="*******************************" #<-- Buraya Gerçek Şifre Gelicek
        phase2="auth=MSCHAPV2"
}
```
# /etc/network/interfaces

```
source interfaces.d/*

allow-hotplug eth0
iface eth0 inet dhcp
address 192.168.0.100
netmask 255.255.255.0
gateway 192.168.0.1
metric 100
#dns-nameservers 10.2.2.1 172.22.66.1



auto wlan0
allow-hotplug wlan0
iface wlan0 inet dhcp
address 0.0.0.0
#dns-nameservers 10.2.2.1 172.22.66.1
pre-up iw dev wlan0 set power_save off
post-down iw dev wlan0 set power_save on
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
metric 50
```

# /boot/config.txt

burada wifi kapatan hiçbir şeyin olmadığına emin ol 
Şunun gibi: dtoverlay=disable-wifi

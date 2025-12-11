# Dietpi için sertifika ile ssh eklenmesi

OpenSSH gerekiyor

ssh ile cihaz içine gir .pub uzantılı dosyanın içeriğini kopyala ve şöyle çalıştır

```
echo ".pub içeriği" > ~/.ssh/authorized_keys
```

## yetkileri ayarla
```
sudo chown -R root:root ~/.ssh
sudo chmod 700 ~/.ssh
sudo chmod 600 ~/.ssh/authorized_keys
```

## /etc/ssh/sshd_config için ssh ayarlarının şöyle olduğuna emin ol
Include edilenleride kapatalım
```
PubkeyAuthentication yes
PasswordAuthentication no
PermitRootLogin prohibit-password
```

## ssh servisini restart et
```
systemctl restart ssh
```
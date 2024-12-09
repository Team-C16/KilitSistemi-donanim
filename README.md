
!!! Setting up display is recommended to be made using ssh because, connecting monitor or any other hdmi display will mess up with the config of Raspberry Pi !!!

For LCD drivers run these

git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show/
sudo ./LCD35-show

After this it will restart

if onboard screen does not works 
try adding these lines at the end of the /boot/config.txt :

dtparam=spi=on
dtoverlay=ili9486
framebuffer_width=480
framebuffer_height=320

 
When screen works change the rotation of the screen with

/LCD-show/rotate.sh 270

After all of that setup the service with 

service_setup.sh 

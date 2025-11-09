Şuan bu kod daha test aşamasında. önce calibration.py çalıştırıp labdaki satranç tahtası çıktısını kameraya gösterip en az 10 defa c ye basılarak kalibrasyon yapılmalı bu kalibrasyon her kamera yeri değiştiğinde yada dokunulduğunda yapılmalı kamera ileride kapıya takıldığında da yeri değişmeyeceği için 1 kere kurulumda yapmak yeterli olucaktır. kalibrasyon yapıldıktan sonra çıkan .npz dosyası test.py için kullanılacak.

şuan test.py sadece kalibrasyonu alıp stereo bir görüntü oluşturmaya çalışıyor şuan tabi hiçbir şey yok.

camera finder ile kaliteli kamera ve daha yüksek fpsli kameraların idleri bulunup bunlar her iki kod içinde doğru şekilde ayarlanmalı
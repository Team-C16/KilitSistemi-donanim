import asyncio
import websockets
import jwt
import time
from time import sleep

jwtsecret = "JWT_SECRET"#DONT FORGET TO CHANGE SECRET

# JWT oluşturma fonksiyonu
def createjwt():
    encoded = jwt.encode(
        {
            "exp": time.time() + 30  # Token'ın geçerlilik süresi (30 saniye)
        },
        jwtsecret,
        algorithm="HS256"
    )
    return encoded

# WebSocket istemcisi
async def websocket_client():
    # Token'ı bağlantıyı başlatırken oluşturuyoruz
    token = createjwt()
    url = f"ws://localhost:8080?token={token}&roomid={1}"  # Sunucuya token'ı bağlantı başlatırken gönderiyoruz
    print(f"Connecting with URI: {url}")

    try:
        # WebSocket'e bağlan
        async with websockets.connect(url) as ws:
            print("Bağlantı başarılı!")

            # Sunucuya mesaj gönder
            message = "Merhaba, mesaj gönderiyorum!"

            sleep(3)
            await ws.send(message)
            
            while True:
                # Server'dan gelen mesajı al
                response = await ws.recv()
                print(f"Server'dan gelen mesaj: {response}")
                if(response == "opendoor"):
                    print("add open door function here")
    
    except Exception as e:
        print(f"Hata oluştu: {e}")

asyncio.run(websocket_client())

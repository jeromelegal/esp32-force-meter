import network
import time

SSID = "PHYLCERO"
PASSWORD = ""

def connect_wifi():
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.disconnect()
        time.sleep(2)

        if not wlan.isconnected():
            print("Connexion WiFi:", SSID)
            wlan.connect(SSID, PASSWORD)
            timeout = 15 
            while timeout > 0:
                if wlan.isconnected():
                    break
                time.sleep(1)
                timeout -= 1
                print(".", end="")
        print()

        if wlan.isconnected():
            ip = wlan.ifconfig()[0]
            print("✅ WiFi OK! IP:", ip)
            return ip
        else:
            print("❌ WiFi echoue")
            return None
    except Exception as e:
        print("❌ WiFi erreur:", e)
        return None

ip_address = connect_wifi() or "NoWiFi"


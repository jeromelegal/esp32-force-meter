import time
import json
import network
import socket
from machine import Pin, SoftI2C
import ssd1306
from hx711 import HX711
import serveur_web
import gestion_programmes

# --- 1. HARDWARE CONFIGURATION ---
PIN_SDA = 8
PIN_SCL = 9
PIN_BOUTON = 17
PIN_DT = 4   
PIN_SCK = 5  
FACTEUR_CALIBRAGE = 1683.78 
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJlbmd0aC1kZXZpY2UtdjEiLCJzY29wZXMiOlsiaW5nZXN0OnN0cmVuZ3RoIl0sImlzcyI6InBvbXBldHJhY2stZGV2aWNlIn0.uAm1CGALvtnXLKOczM_WMjLDd93goy-wR1gnn9bu0Lc"

# --- 2. HARDWARE INITIALIZATION ---
# Initialize I2C for OLED display
i2c = SoftI2C(scl=Pin(PIN_SCL), sda=Pin(PIN_SDA))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Initialize button with pull-up resistor
bouton = Pin(PIN_BOUTON, Pin.IN, Pin.PULL_UP)

# Initialize and calibrate HX711 load cell amplifier
capteur = HX711(dout=PIN_DT, pd_sck=PIN_SCK)
capteur.scale = FACTEUR_CALIBRAGE

# --- 3. DATA MANAGEMENT ---
# Load programs from the external module (handles JSON internally)
programmes = gestion_programmes.charger()

# Ensure all programs have the required keys ('valeurs' and 'total')
for p in programmes:
    if "valeurs" not in p:
        p["valeurs"] = []
    if "total" not in p:
        p["total"] = 3 

print("Loaded programs:", programmes)
index_prog_actuel = 0

# --- 4. NETWORK & WEBSERVER INITIALIZATION ---
wifi = network.WLAN(network.STA_IF)
current_ip = "Offline" # Default value if no WiFi

oled.fill(0)
if wifi.isconnected():
    current_ip = wifi.ifconfig()[0]
    oled.text("WiFi Connected!", 0, 10)
    oled.text(current_ip, 0, 30)
else:
    oled.text("No WiFi", 0, 10)
    oled.text("Offline Mode", 0, 30)
oled.show()
time.sleep(3)

serveur = None
if wifi.isconnected():
    # Start web server only if connected to WiFi
    serveur = serveur_web.init_serveur()
    print("Web server started on IP:", current_ip)

# --- 5. CORE FUNCTIONS ---

def afficher_menu():
    """ Displays the current selected program and network status on the OLED """
    oled.fill(0)
    prog = programmes[index_prog_actuel]
    oled.text("--- MENU ---", 24, 0)
    oled.text(prog["nom"], 0, 20)
    oled.text(f"Meas: {len(prog['valeurs'])}/{prog['total']}", 0, 35)
    oled.text("IP: " + current_ip, 0, 55)
    oled.show()

def lire_bouton():
    """ Reads button state and determines if the press was SHORT or LONG """
    if bouton.value() == 0:
        debut = time.ticks_ms()
        # Wait until the button is released
        while bouton.value() == 0:
            time.sleep_ms(10)
            
        duree = time.ticks_diff(time.ticks_ms(), debut)
        if duree > 800: return "LONG"
        elif duree > 50: return "COURT"
    return "RIEN"

def faire_mesure():
    """ Handles the measuring sequence: tare, countdown, and 5-sec sampling """
    oled.fill(0)
    oled.text("Taring...", 0, 25)
    oled.show()
    capteur.tare(15)

    # 3-second countdown
    for i in range(3, 0, -1):
        oled.fill(0)
        oled.text("GET READY", 25, 20)
        oled.text(f"--- {i} ---", 35, 40)
        oled.show()
        time.sleep(1)

    debut = time.ticks_ms()
    historique_lisse = []
    max_force = 0.0

    # 5-second measurement loop
    while time.ticks_diff(time.ticks_ms(), debut) < 5000:
        force_brute = capteur.get_units(times=1)
        historique_lisse.append(force_brute)
        
        # Keep only the last 5 values for a moving average
        if len(historique_lisse) > 5:
            historique_lisse.pop(0)

        # Calculate current smoothed force
        force_actuelle = sum(historique_lisse) / len(historique_lisse)
        
        # Update maximum recorded force
        if force_actuelle > max_force:
            max_force = force_actuelle

        # Display live feedback
        oled.fill(0)
        oled.text("LIVE FORCE:", 0, 0)
        oled.text(f"{force_actuelle:.1f} N", 0, 15)
        oled.text("MAXIMUM:", 0, 35)
        oled.text(f"{max_force:.1f} N", 0, 50)
        oled.show()

    # End of measurement
    oled.fill(0)
    oled.text("FINISHED!", 25, 20)
    oled.text(f"Score: {max_force:.1f} N", 0, 40)
    oled.show()
    time.sleep(3)

    return round(max_force, 1)

# --- 6. MAIN LOOP ---
# Initial display before entering the loop
afficher_menu()

while True:
    # 6.1 Handle Web Server requests (if active)
    if serveur:
        serveur_web.gerer_requetes(serveur, programmes, TOKEN)
        
    # 6.2 Handle User Inputs
    action = lire_bouton()

    if action == "COURT":
        # Cycle to the next program
        index_prog_actuel = (index_prog_actuel + 1) % len(programmes)
        afficher_menu()

    elif action == "LONG":
        prog = programmes[index_prog_actuel]
        # Check if the program still needs measurements
        if len(prog["valeurs"]) < prog["total"]:
            resultat = faire_mesure()
            prog["valeurs"].append(resultat)
            # Save data using the external module
            gestion_programmes.sauvegarder(programmes) 
        else:
            oled.fill(0)
            oled.text("ALREADY FULL", 15, 25)
            oled.show()
            time.sleep(2)
            
        afficher_menu()

    # Small delay to prevent high CPU usage
    time.sleep_ms(50)


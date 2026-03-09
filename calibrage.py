import time
from hx711 import HX711

PIN_DT = 4   # DT from HX711
PIN_SCK = 5  # SCK (Clock) from HX711
POIDS_REFERENCE = 20.0  

print("Initialisation du capteur...")
capteur = HX711(dout=PIN_DT, pd_sck=PIN_SCK)

print("Videz le capteur (aucun poids).")
print("Taring dans 3 secondes...")
time.sleep(3)
capteur.tare()
print(f"Tare terminée ! Offset enregistré : {capteur.offset}")

print("\n--- ATTENTION ---")
print(f"Placez votre charge de {POIDS_REFERENCE} Kg sur le dynamomètre.")
print("Lecture de la charge dans 10 secondes...")
time.sleep(10)

valeur_brute = capteur.get_value(times=10) # Fait une moyenne sur 10 lectures
facteur = valeur_brute / POIDS_REFERENCE

print("\n=== RÉSULTATS DU CALIBRAGE ===")
print(f"Valeur brute lue : {valeur_brute}")
print(f"POUR TON CODE FINAL, voici ton scale (facteur) : {facteur}")

# Petit test en direct
capteur.scale = facteur
print("\nTest en direct de la balance (Appuyez sur STOP dans Thonny pour arrêter) :")
while True:
    poids = capteur.get_units(times=3)
    print(f"Poids mesuré : {poids:.2f} Kg")
    time.sleep(0.5)

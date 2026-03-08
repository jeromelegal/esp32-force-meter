# ESP32 Force Meter
Micropython code for a custom force-meter
---
## Context :

---
## Step 1 — Pinning

### ESP32-S3 → HX711 amplifier

|HX711|ESP32-S3|Notes|
|---|---|---|
|VCC|3.3V||
|GND|GND||
|DT (DATA)|GPIO 4||
|SCK (CLOCK)|GPIO 5||

### ESP32-S3 → OLED SSD1306 screen

|OLED|ESP32-S3|Notes|
|---|---|---|
|VCC|3.3V||
|GND|GND||
|SCL|GPIO 22|I2C Clock|
|SDA|GPIO 21|I2C Data|

### ESP32-S3 → Push button

```
GPIO 0 ──── [Button] ──── GND
GPIO 0 ──── [Resistor 10kΩ] ──── 3.3V  (pull-up)
```

### ESP32-S3 → HX711 → Dynamometer DYLY-108

```
Dynamometer        HX711
Red      (E+)  ───── E+
Black    (E-)  ───── E-
Green    (A-)  ───── A-
White    (A+)  ───── A+
```

> ⚠️ DYLY-108 is a 4-wires Wheatstone bridge. Be careful to the colour wire.

# Smart House IoT – Specifikacija projekta (KT1)

## 1. Uvod

Ovaj dokument predstavlja specifikaciju projekta iz predmeta  
**Inženjerstvo softvera za Internet/Web of Things**.

Cilj projekta je implementacija sistema pametne kuće korišćenjem
Raspberry Pi uređaja, senzora i aktuatora.  
Projekat se realizuje kroz više kontrolnih tačaka.

Ova specifikacija odnosi se na **Kontrolnu tačku 1 (KT1)**.

---

## 2. Opis sistema pametne kuće

Sistem pametne kuće sastoji se od tri Raspberry Pi uređaja:

- **PI1** – ulazna vrata
- **PI2** – kuhinja
- **PI3** – spavaće i dnevne sobe

Za potrebe **KT1** implementiran je samo uređaj **PI1**.

---

## 3. PI1 – Uređaji

### 3.1 Senzori (ulazni uređaji)

| Oznaka | Naziv | Tip senzora |
|------|------|------------|
| DS1 | Door Sensor | Digitalni (Button) |
| DPIR1 | Door Motion Sensor | Digitalni (PIR) |
| DMS | Door Membrane Switch | Digitalni (Button) |
| DUS1 | Door Ultrasonic Sensor | Ultrazvučni (udaljenost) |

### 3.2 Aktuatori (izlazni uređaji)

| Oznaka | Naziv | Tip aktuatora |
|------|------|---------------|
| DL | Door Light | LED |
| DB | Door Buzzer | Buzzer |

Napomena: Web kamera (WEBC) nije deo implementacije za KT1.

---

## 4. Funkcionalni zahtevi (KT1)

Za prvu kontrolnu tačku implementirani su sledeći zahtevi:

1. Skripta se pokreće na Raspberry Pi uređaju **PI1**
2. Omogućena je konfiguracija rada uređaja:
   - **REAL** – rad sa stvarnim hardverom
   - **SIM** – simulacija uređaja bez hardvera
   - **OFF** – isključen uređaj
3. Ulazni podaci sa **svakog senzora se ispisuju u konzoli**
4. Omogućeno je upravljanje aktuatorima putem **konzolne aplikacije**
5. Web kamera nije implementirana

---

## 5. Arhitektura softvera

Aplikacija je organizovana po uzoru na kostur korišćen na laboratorijskim vežbama.

### 5.1 Struktura projekta

smart-house-iot/
├── docs/
│ └── SPEC.md
└── src/
├── main.py
├── settings.py
├── settings.json
├── components/
├── sensors/
├── simulators/
└── actuators/


### 5.2 Podela odgovornosti

- **main.py**  
  Pokretanje aplikacije, učitavanje konfiguracije i upravljanje nitima.

- **settings.json**  
  Konfiguracija rada uređaja (SIM/REAL/OFF) i GPIO pinova.

- **components/**  
  Logika rada pojedinačnih uređaja (DS1, DPIR1, DMS, DUS1).

- **sensors/**  
  Implementacija rada sa GPIO pinovima (REAL režim).

- **simulators/**  
  Simulacija senzora u slučaju kada hardver nije dostupan.

- **actuators/**  
  Upravljanje LED i buzzer uređajima.

---

## 6. Simulacija i rad bez hardvera

Sistem je dizajniran tako da može da radi:

- na Raspberry Pi uređaju (REAL režim)
- na standardnom računaru bez GPIO hardvera (SIM režim)

U slučaju da biblioteka **RPi.GPIO** nije dostupna, koristi se simulacija
ulaznih i izlaznih uređaja, što omogućava razvoj i testiranje bez fizičkog uređaja.

Ovakav pristup je u skladu sa zahtevima projektnog zadatka.

---

## 7. Ispis senzorskih podataka

Svaki senzor se periodično očitava u posebnoj niti.
Očitani podaci se prosleđuju putem callback funkcija i ispisuju u konzoli.

Primer ispisa u konzoli:

Code: DS1
Pressed: True

Code: DPIR1
Motion: False

Code: DUS1
Distance: 74.3 cm


Na ovaj način ispunjen je zahtev specifikacije:
**„Ulazne podatke sa svakog senzora potrebno je ispisati u konzoli.“**

---

## 8. Upravljanje aktuatorima

Upravljanje aktuatorima omogućeno je putem konzolne aplikacije.

Primer komandi:
- `dl on` – uključivanje svetla
- `dl off` – isključivanje svetla
- `db beep 3` – aktiviranje buzzera tri puta

U SIM režimu komande se ispisuju u konzoli,
dok u REAL režimu upravljaju stvarnim GPIO pinovima.

---

## 9. Zaključak

Ovom specifikacijom definisana je implementacija sistema pametne kuće za
Kontrolnu tačku 1.  
Rešenje zadovoljava sve zahteve zadatka, omogućava simulaciju uređaja
i predstavlja stabilnu osnovu za dalji razvoj sistema u narednim fazama projekta.

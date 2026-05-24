import requests
import time
import sys

# ip del robot, va cambiato con quello reale
IP_ROBOT = ""  # da inserire l'IP del braccio mrccanico
URL_BASE = f"http://{IP_ROBOT}"

TIMEOUT = 5


# funzione per mandare i comandi gcode al robot
def manda_gcode(comando):
    url = URL_BASE + "/rr_gcode"
    params = {"gcode": comando}
    
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code == 200:
            print("comando inviato: " + comando)
            return True
        else:
            print("errore, status code: " + str(r.status_code))
            return False
    except requests.exceptions.ConnectionError:
        print("errore: non riesco a connettermi al robot")
        print("controlla che sia acceso e in rete")
        return False
    except requests.exceptions.Timeout:
        print("errore: timeout, il robot non risponde")
        return False


# legge lo stato del robot (posizioni assi ecc)
def leggi_stato():
    url = URL_BASE + "/rr_status"
    params = {"type": 2}
    
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        else:
            print("errore nel leggere lo stato")
            return {}
    except Exception as e:
        print("errore: " + str(e))
        return {}


def aspetta(secondi=2.0):
    time.sleep(secondi)


# porta tutti gli assi a zero
def home():
    print("vado a home...")
    manda_gcode("G28")
    aspetta(3.0)


# muove un asse alla posizione indicata in gradi
# assi disponibili: X=base, Y=spalla, Z=gomito, U=polso rot, V=polso inc, W=pinza
def muovi_asse(asse, gradi, velocita=1000):
    asse = asse.upper()
    comando = "G1 " + asse + str(gradi) + " F" + str(velocita)
    print("muovo asse " + asse + " a " + str(gradi) + " gradi")
    manda_gcode(comando)
    aspetta(2.0)


# muove l'asse di una quantita relativa rispetto a dove si trova adesso
def muovi_relativo(asse, delta, velocita=800):
    asse = asse.upper()
    print("movimento relativo asse " + asse + ": " + str(delta) + " gradi")
    manda_gcode("G91")  # modalita relativa
    manda_gcode("G1 " + asse + str(delta) + " F" + str(velocita))
    manda_gcode("G90")  # torna in assoluto
    aspetta(2.0)


def apri_pinza():
    print("apro la pinza")
    manda_gcode("G1 W0 F500")
    aspetta(1.0)


def chiudi_pinza():
    print("chiudo la pinza")
    manda_gcode("G1 W90 F500")
    aspetta(1.0)


# sequenza di test: muove ogni asse di 30 gradi e poi torna a home
def sequenza_test():
    print("inizio sequenza di test")
    
    home()
    
    assi = ["X", "Y", "Z", "U", "V"]
    nomi = ["base", "spalla", "gomito", "polso rotazione", "polso inclinazione"]
    
    for i in range(len(assi)):
        print("test " + nomi[i] + " (asse " + assi[i] + ")")
        muovi_asse(assi[i], 30)
        aspetta(1.0)
        muovi_asse(assi[i], -30)
        aspetta(1.0)
        muovi_asse(assi[i], 0)
    
    print("test pinza")
    apri_pinza()
    chiudi_pinza()
    apri_pinza()
    
    home()
    print("sequenza di test finita")


# il braccio fa un movimento tipo saluto
def sequenza_saluto():
    print("inizio saluto")
    home()
    
    for i in range(3):
        print("saluto numero " + str(i+1))
        muovi_asse("Y", 45, 1200)
        muovi_asse("Y", 0, 1200)
    
    home()
    print("saluto finito")


# pick and place: prende un oggetto e lo sposta in un altro punto
# pos_pick e pos_place sono dizionari tipo {"X": 45, "Y": 30}
def sequenza_pick_and_place(pos_pick, pos_place):
    print("inizio pick and place")
    
    home()
    apri_pinza()
    
    # vai alla posizione di presa
    print("vado alla posizione di presa")
    for asse in pos_pick:
        muovi_asse(asse, pos_pick[asse])
    
    chiudi_pinza()
    aspetta(0.5)
    
    # vai alla posizione di rilascio
    print("vado alla posizione di rilascio")
    for asse in pos_place:
        muovi_asse(asse, pos_place[asse])
    
    apri_pinza()
    home()
    print("pick and place finito")


# menu principale
def menu():
    print("================================")
    print("  controller braccio robotico PRIMO")
    print("  ip robot: " + IP_ROBOT)
    print("================================")
    
    while True:
        print("\ncosa vuoi fare?")
        print("1 - home")
        print("2 - muovi un asse")
        print("3 - apri pinza")
        print("4 - chiudi pinza")
        print("5 - sequenza test")
        print("6 - saluto")
        print("7 - stato robot")
        print("8 - manda gcode manuale")
        print("0 - esci")
        
        scelta = input("scelta: ").strip()
        
        if scelta == "1":
            home()
        
        elif scelta == "2":
            print("assi: X=base, Y=spalla, Z=gomito, U=polso rot, V=polso inc, W=pinza")
            asse = input("quale asse? ").strip()
            try:
                gradi = float(input("quanti gradi? "))
                muovi_asse(asse, gradi)
            except ValueError:
                print("valore non valido")
        
        elif scelta == "3":
            apri_pinza()
        
        elif scelta == "4":
            chiudi_pinza()
        
        elif scelta == "5":
            sequenza_test()
        
        elif scelta == "6":
            sequenza_saluto()
        
        elif scelta == "7":
            stato = leggi_stato()
            if stato:
                print(stato)
            else:
                print("nessun dato ricevuto")
        
        elif scelta == "8":
            cmd = input("scrivi il gcode: ").strip()
            if cmd:
                manda_gcode(cmd)
        
        elif scelta == "0":
            print("uscita")
            sys.exit(0)
        
        else:
            print("scelta non valida, riprova")


# avvio
if __name__ == "__main__":
    if len(sys.argv) > 1:
        IP_ROBOT = sys.argv[1]
        URL_BASE = "http://" + IP_ROBOT
    
    menu()
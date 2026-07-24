import json
import sqlite3
import serial
import time
import sounddevice as sd
from scipy.io.wavfile import write
import ollama
from faster_whisper import WhisperModel
from slbcom.slbcom_linux import SLBCOM



class Pixy:
    
    def __init__(self, fs : int=24000, seconde : int=5):
        self.fs = fs
        self.seconde = seconde
        self.model = WhisperModel(
            "large-v1",
            device="cpu",
            compute_type="int8"
        )
        self.slb = SLBCOM()
        

    def Record(self):
        audio = sd.rec(
            int(self.seconde * self.fs),
            samplerate=self.fs,
            channels=1
        )
        sd.wait()
        write("audio.wav",self.fs,audio)
    
    
    def Voice_decode(self,audio_path : str) -> str:
        print("Traitement en cours ....")

        segments,info = self.model.transcribe(
            audio_path,
            language="fr"
        )
        
        print("Decodage de la demande".center(100,"="))

        text= ""

        for i in segments:
            text += i.text

        return text
    
    def Thinks(self,text : str) -> str:
        print(text)
        print("Commande reçu !  \nExecution de la tâche demandée")
        SYSTEM_PROMPT = open("SYS_PROMPT.txt","r",encoding="UTF-8").read()
        reponse = ollama.chat(
            "llama3:latest",
            messages=[
                {
                    'role' : "system",
                    'content' : SYSTEM_PROMPT
                },
                {
                    'role' : "user",
                    'content' : text
                }
            ],
            keep_alive=-1,
            options={
                "temperature": 0,
                "top_k": 1,
                "top_p": 0.1,
                "num_ctx": 1024,
                "num_predict": 10
            },
        )
        rps = reponse["message"]["content"].replace("'","").replace("TOI","")
        print(rps,"reponse de llm")
        return rps
    
    def Create_db(self):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        query = open("query_create_tb.sql","r").read()
        cursor.execute(query)

        conn.commit()
        conn.close()

        print("Database Created")
    
    def Insert_db(self, Nom: str, Commande: str):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Components (Nom, Commande)
            VALUES (?, ?)
        """, (Nom, Commande))

        conn.commit()
        conn.close()
    
    def Update_db(self, Commande: str, cmd_all : str =""):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        if cmd_all == "ON":
            cursor.execute("""
                UPDATE Components 
                SET Etat_logique = 0
            """)
        elif cmd_all == "OFF":
            cursor.execute("""
                UPDATE Components 
                SET Etat_logique = 1
            """)
        else:
            cursor.execute("""
                UPDATE Components 
                SET Etat_logique = NOT Etat_logique 
                WHERE Commande = ?
            """, (Commande,))

        conn.commit()
        conn.close()
        
        
    def Get_statut(self):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        data = cursor.execute("""
            SELECT Nom,Commande,Etat_logique FROM Components
                       """).fetchall()[:-1]
        conn.close()
        
        return data  
    
    def Migrate(self):
        with open("config.json","r") as file:
            file = json.load(file)["component"]
        for key,val in file.items():
            self.Insert_db(val,key)
            
    def Commande_slb(self,bit,port_com : str,baud_rate : int = 9600,commande : str = "") -> None|bool:
        bit = int(bit,2)
        slb = SLBCOM()        
        if slb.opencom(port_com,baud_rate):
            print("Connecté OK")
            
            slb.decalers([bit])
            slb.closecom()
            if commande == "":
                return
            if "ON" == commande:
                self.Update_db(commande,"ON")
                return True
            elif "OFF" == commande:
                self.Update_db(commande,"OFF")
                return True
            elif "OFF" in commande:
                commande = "".join(["ON",commande[-1]])
            self.Update_db(commande)
            return True
        
        
    def Execution(self,port_com_slb : str,port_com_gsm : str ,baud_rate_slb : int = 9600,baud_rate_gsm : int = 115200,Commande : str = "") -> bool|None:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        data = cursor.execute("""
            SELECT Etat_logique FROM Components ORDER BY Nom
                              """).fetchall()
        data_bit = [str(i[0]) for i in data][:-1]
        data_bit.reverse()
        data_bit = ["1","1","1","1"] + data_bit
        if "ON" in Commande:
            v = Commande[-1]
            if v == "N":
                data_bit = "11110000"
                self.Commande_slb(data_bit,port_com_slb,baud_rate_slb,Commande)
                return True
            elif data_bit[-int(v)] == "0":
                return False
            else:
                data_bit[-int(v)] = "0"
                self.Commande_slb("".join(data_bit),port_com_slb,baud_rate_slb,Commande)
                return True
            
        elif "OFF" in Commande:
            v = Commande[-1]
            if v == "F":
                data_bit = "11111111"
                self.Commande_slb(data_bit,port_com_slb,baud_rate_slb,Commande)
                return True
            elif data_bit[-int(v)] == "1":
                print(data_bit,"wesh")
                return False
            else:
                data_bit[-int(v)] = "1"
                print(data_bit)
                self.Commande_slb("".join(data_bit),port_com_slb,baud_rate_slb,Commande)
                return True
        
        elif Commande == "":
            self.Commande_slb("".join(data_bit),port_com_slb,baud_rate_slb,Commande)
            
        elif Commande in ["Pompier","Police","Hopital"]:
            self.gsm_call(port_com_gsm,baud_rate_gsm,Commande,"C/NGALIEMA C.A.C Q/L 4BIS")
            
        print(data_bit)
    
    def gsm_call(self, port_gsm: str, baudrate: int = 115200, service: str = "", sms_message: str = ""):
        """
        Envoie d'abord un SMS (si fourni) puis passe un appel téléphonique au service d'urgence.
        
        Args:
            port_gsm (str): Port série du module GSM (ex: '/dev/ttyUSB1').
            baudrate (int): Débit en bauds.
            service (str): Nom du service dans la base (ex: 'Police').
            sms_message (str): Contenu du SMS à envoyer avant l'appel. Si vide, pas de SMS.
        """
        # 1. Récupérer le numéro depuis la base de données
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT numero FROM Urgence WHERE nom = ?", (service,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            print(f"Aucun numéro trouvé pour le service '{service}'.")
            return

        numero = result[0]

        # 2. Connexion série au module GSM
        try:
            ser = serial.Serial(port_gsm, baudrate, timeout=2)
            time.sleep(0.5)
        except Exception as e:
            print(f"Erreur port série {port_gsm} : {e}")
            return

        # 3. Vérifier que le module répond
        ser.write(b"AT\r\n")
        time.sleep(0.3)
        if b"OK" not in ser.read(ser.inWaiting()):
            print("Module GSM muet.")
            ser.close()
            return

        # --- Envoi du SMS si un message est fourni ---
        if sms_message.strip():
            print(f"Envoi d'un SMS au {numero} : {sms_message}")
            # Passer en mode texte
            ser.write(b"AT+CMGF=1\r\n")
            time.sleep(0.3)
            # Spécifier le numéro du destinataire
            ser.write(f'AT+CMGS="{numero}"\r\n'.encode())
            time.sleep(0.3)
            # Envoyer le message suivi de Ctrl+Z (0x1A)
            ser.write((sms_message + "\x1A").encode())
            time.sleep(5)  # délai pour l'envoi
            # Vérifier si OK (optionnel)
            response = ser.read(ser.inWaiting())
            if b"OK" not in response:
                print("Échec de l'envoi du SMS.")
            else:
                print("SMS envoyé avec succès.")

        # 4. Composer le numéro pour l'appel
        print(f"Appel du service {service} au numéro {numero}...")
        cmd = f"ATD{numero};\r\n"
        ser.write(cmd.encode())
        print("Appel en cours...")

        # 5. Attendre (par exemple 30 secondes) puis raccrocher
        time.sleep(30)
        ser.write(b"ATH\r\n")
        time.sleep(0.5)
        ser.close()
        print("Appel terminé.")
    

if __name__ == "__main__":
    P = Pixy()
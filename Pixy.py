import json
import sqlite3
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
        print("Parler...")
        audio = sd.rec(
            int(self.seconde * self.fs),
            samplerate=self.fs,
            channels=1
        )
        sd.wait()
        write("audio.wav",self.fs,audio)
        print("Ordre reçu".center(100,"="))
    
    
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
        )
        rps = reponse["message"]["content"].replace("'","").replace("TOI","")
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
    
    def Update_db(self, Commande: str):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
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
            if "OFF" in commande:
                commande = "".join(["ON",commande[-1]])
            self.Update_db(commande)
            return True
        
        
    def Execution(self,port_com : str,baud_rate : int = 9600,Commande : str = "") -> bool|None:
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
                self.Commande_slb(data_bit,port_com,baud_rate,Commande)
                return True
            elif data_bit[-int(v)] == "0":
                return False
            else:
                data_bit[-int(v)] = "0"
                self.Commande_slb("".join(data_bit),port_com,baud_rate,Commande)
                return True
            
        elif "OFF" in Commande:
            v = Commande[-1]
            if v == "F":
                data_bit = "11111111"
                self.Commande_slb(data_bit,port_com,baud_rate,Commande)
                return True
            elif data_bit[-int(v)] == "1":
                return False
            else:
                data_bit[-int(v)] = "1"
                self.Commande_slb("".join(data_bit),port_com,baud_rate,Commande)
                return True
        
        elif Commande == "":
            self.Commande_slb("".join(data_bit),port_com,baud_rate,Commande)
            
        print(data_bit)
    

if __name__ == "__main__":
    P = Pixy()
    P.Execution("hjgjh","hgjhgh")
        
            
            
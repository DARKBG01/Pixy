import json
import sqlite3
import sounddevice as sd
from scipy.io.wavfile import write
import ollama
from faster_whisper import WhisperModel
import slbcom.slbcom as slb



class Pixy:
    def __init__(self, fs : int=24000, seconde : int=5):
        self.fs = fs
        self.seconde = seconde
        self.model = WhisperModel(
            "large-v1",
            device="cpu",
            compute_type="int8"
        )

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
        return reponse["message"]["content"]
    
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
        
        
    
    
    def Migrate(self):
        with open("config.json","r") as file:
            file = json.load(file)["component"]
        
        for key,val in file.items():
            self.Insert_db(val,key)
            
        
        
    def Execution(self,port_com : str,baude_rate : int = 9600,Commande : str = "",Simulation : bool = False) -> bool|None:
        if Simulation:
            self.Update_db(Commande)
            return True
        
        if slb.opencom(port_com,baude_rate,"N",1,1):
            r0 = 0
            slb.decalers(port_com,[r0])
        else:
            return 
        try:
            slb.decalers(port_com,[int(Commande[-1])])
            self.Update_db(Commande)
            return True
        except Exception as e:
            print(f"Erreur : {e}")
            
            
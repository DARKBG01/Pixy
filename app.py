import os
from flask import Flask,render_template,request,jsonify
from Pixy import Pixy

app = Flask(__name__)
Pixy_instance = Pixy()
port = "/dev/ttyUSB0"
Pixy_instance.Execution(port)

@app.route("/",methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/upload",methods=["POST"])
def upload():
    path = "audio.webm"
    request.files['audio'].save(path)
    voice_decode = Pixy_instance.Voice_decode(path)
    Commande = Pixy_instance.Thinks(voice_decode)
    
    Execuction = Pixy_instance.Execution(
        port,
        Commande=Commande
    )
    
    if Execuction:
        print("Commande executée avec success")
    return "ok"

@app.route("/stat",methods=["GET"])
def stat():
    c = Pixy_instance.Get_statut()
    print(c)
    
    return jsonify(c)
    
    

if __name__ == '__main__':
    if not (os.path.exists("database.db")):
        Pixy_instance.Create_db()
        Pixy_instance.Migrate()
    app.run("0.0.0.0","8000",debug=True)
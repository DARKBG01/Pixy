import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

# Enregistrement
fs = 44100
seconds = 5

print("Parlez...")

audio = sd.rec(
    int(seconds * fs),
    samplerate=fs,
    channels=1
)

sd.wait()

write("audio.wav", fs, audio)

print("ordre reçu".center(100,"="))

print("Traitement....")

# Whisper
model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    "audio.wav",
    language="fr"
)

texte = ""

for segment in segments:
    texte += segment.text

print("Vous avez dit :", texte)
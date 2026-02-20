import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import subprocess
import os
import winsound

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VOSK_MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-hi-0.22")

PIPER_EXE = os.path.join(BASE_DIR, "piper", "piper.exe")

SONG_PATH = os.path.join(BASE_DIR, "music", "Chammak Challo Ra One.wav")

# ---------------- AUDIO CONFIG ----------------
SAMPLE_RATE = 16000
q = queue.Queue()

# ---------------- STATE ----------------
awake = False
last_text = ""
music_playing = False

# 🔹 Male / Female voices
current_voice = "male"
VOICE_MODELS = {
    "male": os.path.join(BASE_DIR, "piper", "model", "hi_IN-rohan-medium.onnx"),
    "female": os.path.join(BASE_DIR, "piper", "model", "hi_IN-priyamvada-medium.onnx"),
}

WAKE_WORDS = ["सुनो", "हेलो", "अरे"]
SLEEP_WORDS = ["बंद", "चुप"]
TERMINATE_WORDS = ["पूरी तरह बंद", "सिस्टम बंद"]

# ---------------- LOAD VOSK ----------------
vosk_model = Model(VOSK_MODEL_PATH)
recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)

# ---------------- MIC CALLBACK ----------------
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

# ---------------- INTENT LOGIC ----------------
def handle_intent(text):
    global awake, current_voice, music_playing
    words = text.split()

    # ---- TERMINATE ----
    if "पूरी" in words and "बंद" in words:
        return "__TERMINATE__"

    # ---- WAKE ----
    if not awake:
        if any(w in words for w in WAKE_WORDS):
            awake = True
            return "हाँ"
        return None

    # ---- SLEEP ----
    if any(w in words for w in SLEEP_WORDS):
        awake = False
        return "ठीक है"

    # ---- MUSIC PLAY ----
    if ("गाना" or "गायन") in words and not music_playing:
        return "__PLAY_SONG__"

    # ---- MUSIC STOP ----
    if "बंद" in words and music_playing:
        return "__STOP_SONG__"

    # ---- VOICE SWITCH ----
    if "लड़की" in words or "महिला" in words:
        current_voice = "female"
        return "आवाज़ बदल दी"

    if "लड़का" in words or "पुरुष" in words:
        current_voice = "male"
        return "आवाज़ बदल दी"

    from datetime import datetime

    # ---- TIME / DATE ----
    if any(w in words for w in ["समय", "बजे", "कितना"]):
        return f"अभी का समय है {datetime.now().strftime('%H:%M')}"

    if "तारीख" in words:
        return f"आज की तारीख {datetime.now().strftime('%d %B %Y')} है"

    if "दिन" in words and "आज" in words:
        return f"आज {datetime.now().strftime('%A')} है"

    if "दिन" in words or "रात" in words:
        return "अभी दिन है" if 6 <= datetime.now().hour < 18 else "अभी रात है"

    # ---- IDENTITY ----
    if "नाम" in words:
        return "मेरा नाम हिंदी सहायक है"

    if "कौन" in words:
        return "मैं एक ऑफलाइन हिंदी सहायक हूँ"

    if "बनाया" in words:
        return "मुझे स्थानीय रूप से बनाया गया है"

    # ---- SOCIAL ----
    if any(w in words for w in ["नमस्ते", "हाय"]):
        return "नमस्ते"

    if "कैसे" in words:
        return "मैं ठीक हूँ"

    if "धन्यवाद" in words:
        return "आपका स्वागत है"

    if "अलविदा" in words:
        return "फिर मिलेंगे"

    return None

# ---------------- TTS ----------------
def speak(text):
    print("🔊 Speaking:", text)

    output_wav = "output.wav"

    subprocess.run(
        [
            PIPER_EXE,
            "--model", VOICE_MODELS[current_voice],
            "--output_file", output_wav
        ],
        input=text.encode("utf-8"),
        check=True
    )

    winsound.PlaySound(output_wav, winsound.SND_FILENAME)

# ---------------- MAIN LOOP ----------------
def main():
    global last_text, music_playing
    print("🎤 Hindi Assistant is listening...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        callback=audio_callback
    ):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if not text or text == last_text:
                    continue

                print("You said:", text)

                reply = handle_intent(text)

                if reply == "__PLAY_SONG__":
                    winsound.PlaySound(
                        SONG_PATH,
                        winsound.SND_FILENAME | winsound.SND_ASYNC
                    )
                    music_playing = True
                    last_text = text
                    continue

                if reply == "__STOP_SONG__":
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    music_playing = False
                    last_text = text
                    continue

                if reply == "__TERMINATE__":
                    speak("सहायक बंद हो रहा है")
                    break

                if reply:
                    print("Assistant:", reply)
                    speak(reply)

                last_text = text

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()

import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import subprocess
import os
import sys
import time
from datetime import datetime
import random

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "vosk-model-small-hi-0.22")
PIPER_EXE = os.path.join(BASE_DIR, "piper", "piper")
SONG_PATH = os.path.join(BASE_DIR, "music", "song.wav")

# ---------------- AUDIO CONFIG ----------------
SAMPLE_RATE = 48000
OUTPUT_DEVICE = "plughw:2,0"
q = queue.Queue()

# ---------------- STATE ----------------
awake = False
is_speaking = False
last_text = ""
music_process = None
current_voice = "male"
active_voice = None

VOICE_MODELS = {
    "male": os.path.join(BASE_DIR, "piper", "model", "hi_IN-rohan-medium.onnx"),
    "female": os.path.join(BASE_DIR, "piper", "model", "hi_IN-priyamvada-medium.onnx"),
}

WAKE_WORDS = ["सुनो", "हेलो", "अरे"]
SLEEP_WORDS = ["बंद", "चुप"]

# ---------------- LOAD VOSK ----------------
if not os.path.exists(VOSK_MODEL_PATH):
    print(f"Error: Vosk model missing at {VOSK_MODEL_PATH}")
    sys.exit(1)

vosk_model = Model(VOSK_MODEL_PATH)
recognizer = KaldiRecognizer(vosk_model, SAMPLE_RATE)

# ---------------- MIC CALLBACK ----------------
def audio_callback(indata, frames, time, status):
    if is_speaking:
        return
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# ---------------- INTENT LOGIC ----------------
def handle_intent(text):
    global awake, current_voice

    text = text.strip()
    if not text: return None

    # 1. EXIT / SHUTDOWN
    if "सिस्टम"  in text:
        return "__SHUTDOWN__"

    # 2. WAKE WORD
    if not awake:
        if any(w in text for w in WAKE_WORDS):
            awake = True
            return "नमस्ते, मैं सुन रहा हूँ"
        return None

    # 3. SLEEP
    if any(w in text for w in SLEEP_WORDS):
        awake = False
        return "ठीक है, जब ज़रूरत हो तो बुला लेना"

    # 4. GREETINGS
    if any(w in text for w in ["नमस्ते", "हैलो", "हाय", "नमस्कार"]):
        return "नमस्ते! मैं आपकी क्या मदद कर सकता हूँ?"

    # 5. TIME
    if any(w in text for w in ["समय", "बजे", "कितने", "टाइम"]):
        return f"अभी का समय है {datetime.now().strftime('%H:%M')}"

    # 6. DATE
    if any(w in text for w in ["तारीख", "तिथि", "दिनांक"]):
        return f"आज की तारीख है {datetime.now().strftime('%d %B %Y')}"

    # 7. DAY
    if "दिन" in text and any(w in text for w in ["कौन", "आज", "क्या"]):
        days = {"Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार",
                "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"}
        eng_day = datetime.now().strftime('%A')
        return f"आज {days[eng_day]} है"

    # 8. IDENTITY
    if "नाम" in text:
        return "मेरा नाम हिंदी सहायक है"
    if "कौन" in text or "क्या तुम" in text:
        return "मैं आपका निजी हिंदी सहायक हूँ"

    # 9. CREATOR
    if "किसने बनाया" in text or "बनाया" in text or "मालिक" in text or "जनक" in text:
        return "मुझे डेवलपर्स ने प्रोग्राम किया है ताकि मैं आपकी मदद कर सकूँ"

    # 10. USAGE
    if "उपयोग" in text:
        return "मुझे इस प्रकार बनाया गया है कि मैं आपके सवालों के जवाब दे सकूँ और आवश्यक जानकारी प्रदान कर सकूँ"

    # 11. HOW DO I WORK
    if "कैसे काम" in text:
        return "मैं आपकी आवाज़ को पहचानती हूँ, उसे टेक्स्ट में बदलती हूँ और फिर उसके अनुसार उत्तर देती हूँ"

    # 12. DEVICE
    if "डिवाइस" in text or "मशीन" in text:
        return "मैं रास्पबेरी पाई पर चल रही हूँ"

    # 13. HOW DO YOU KNOW TIME
    if "समय" in text and "जानती" in text:
        return "मैं रियल टाइम क्लॉक मॉड्यूल की मदद से समय प्राप्त करती हूँ"

    # 14. VOICE SWITCH
    if "महिला" in text or "लड़की" in text or "औरत" in text:
        current_voice = "female"
        return "ठीक है, अब मैं महिला की आवाज़ में बात करूँगी"
    if "पुरुष" in text or "लड़का" in text or "आदमी" in text:
        current_voice = "male"
        return "ठीक है, मैंने आवाज़ बदल दी है"

    # 15. MUSIC CONTROL
    if  "बंद" in text:
        return "__STOP_SONG__"
    if "गाना" in text or "संगीत" in text or "बजाओ" in text:
        return "__PLAY_SONG__"

    # 16. WEATHER
    if "मौसम" in text or "तापमान" in text:
        return "अभी स्थानीय तापमान सुहावना लग रहा है"

    # 17. JOKE
    if any(w in text for w in ["चुटकुला", "मज़ाक", "हंसाओ"]):
        jokes = [
            "पप्पू: मम्मी, क्या मैं भगवान की तरह दिखता हूँ? मम्मी: नहीं! पप्पू: क्यों? क्योंकि मैं जहाँ भी जाता हूँ लोग कहते हैं 'हे भगवान! फिर आ गया'!",
            "टीचर: बताओ सबसे पुराना जानवर कौन सा है? छात्र: ज़ेब्रा... क्योंकि वो ब्लैक एंड वाइट है!"
        ]
        return random.choice(jokes)

    return None

# ---------------- TTS ENGINE ----------------
tts_process = None
tts_aplay = None

def start_tts_engine():
    global tts_process, tts_aplay, active_voice
    if tts_process:
        try: tts_process.terminate()
        except: pass
    if tts_aplay:
        try: tts_aplay.terminate()
        except: pass

    model = VOICE_MODELS[current_voice]
    if not os.path.exists(model):
        print(f"TTS model missing: {model}")
        return

    aplay_cmd = ["aplay", "-t", "raw", "-r", "22050", "-f", "S16_LE", "-c", "1", "--buffer-time=50000"]
    if OUTPUT_DEVICE:
        aplay_cmd.extend(["-D", OUTPUT_DEVICE])

    tts_aplay = subprocess.Popen(aplay_cmd, stdin=subprocess.PIPE)
    tts_process = subprocess.Popen(
        [PIPER_EXE, "--model", model, "--output-raw", "--json-input"],
        stdin=subprocess.PIPE, stdout=tts_aplay.stdin
    )
    active_voice = current_voice

def speak(text):
    global is_speaking
    if current_voice != active_voice or not tts_process or tts_process.poll() is not None:
        start_tts_engine()
    if not tts_process:
        return

    is_speaking = True
    # Clear mic queue BEFORE speaking to prevent stacking
    while not q.empty():
        q.get()

    try:
        payload = json.dumps({"text": text}) + "\n"
        tts_process.stdin.write(payload.encode("utf-8"))
        tts_process.stdin.flush()
        # Estimate duration based on text length
        duration = len(text) * 0.12 + 0.5
        sd.sleep(int(duration * 1000))
    except Exception as e:
        print(f"Speak error: {e}")

    # Clear mic queue AFTER speaking to stop stacking
    while not q.empty():
        q.get()
    is_speaking = False

# ---------------- MAIN ----------------
def main():
    global last_text, music_process
    start_tts_engine()
    print("🚀 Hindi Assistant Ready (Clean State)")

    INPUT_DEVICE_INDEX = None  # Use default device; change to an int if needed

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=2000,
                            device=INPUT_DEVICE_INDEX, callback=audio_callback):
            print("READY. Say 'Suno' to start.")
            partial_text = ""
            last_partial_time = 0

            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result()).get("text", "").strip()
                else:
                    res = json.loads(recognizer.PartialResult()).get("partial", "").strip()

                if not res:
                    partial_text = ""
                    continue

                if res != partial_text:
                    partial_text = res
                    last_partial_time = time.time()

                # Trigger on 0.4s of silence (same as original working reference)
                if partial_text and (time.time() - last_partial_time > 0.4):
                    if partial_text == last_text:
                        continue

                    print("You said:", partial_text)
                    reply = handle_intent(partial_text)

                    if reply == "__SHUTDOWN__":
                        speak("सिस्टम बंद हो रहा है")
                        time.sleep(1)
                        os.system("sudo shutdown now")
                        break
                    elif reply == "__PLAY_SONG__":
                        if music_process:
                            music_process.terminate()
                        cmd = ["aplay"]
                        if OUTPUT_DEVICE:
                            cmd.extend(["-D", OUTPUT_DEVICE])
                        cmd.append(SONG_PATH)
                        music_process = subprocess.Popen(cmd)
                    elif reply == "__STOP_SONG__":
                        if music_process:
                            music_process.terminate()
                            music_process = None
                    elif reply:
                        speak(reply)

                    last_text = partial_text
                    partial_text = ""
                    recognizer.Reset()

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
     main()

# Setup Guide: Hindi Assistant on Raspberry Pi 4 (32-bit)

This guide provides step-by-step instructions to set up the Hindi Voice Assistant on a Raspberry Pi 4 running a fresh 32-bit OS (Raspberry Pi OS).

## Prerequisites
- Raspberry Pi 4
- Fresh installation of Raspberry Pi OS (32-bit)
- Internet connection on the Pi
- Microphone and Speaker connected (USB or 3.5mm jack)

## Step 1: Transfer Files to Raspberry Pi
You need to move the project files from your computer to the Raspberry Pi. You can do this via **SCP (SSH)** or a **USB Drive**.

### Files to Transfer:
1. `setup_rpi.sh`
2. `requirements.txt`
3. `assistant_rpi.py`
4. `fix_vosk.py` (optional, for debugging)
5. `debug_rpi.py` (optional, for debugging)

**Example using SCP (run from your PC):**
Assuming your Pi's IP is `192.168.1.100` and user is `pi`:
```bash
scp setup_rpi.sh requirements.txt assistant_rpi.py pi@192.168.1.100:~/hindi_assistant/
```

## Step 2: Run the Setup Script
Once the files are on the Pi, open a terminal on the Pi and navigate to the folder where you placed the files.

1. **Make the script executable:**
   ```bash
   chmod +x setup_rpi.sh
   ```

2. **Run the script:**
   ```bash
   ./setup_rpi.sh
   ```

   **What this script does:**
   - Updates the system (`apt update`).
   - Installs system dependencies: `python3-pip`, `libportaudio2` (for audio), `wget`, `unzip`, `tar`.
   - Installs Python libraries: `vosk`, `sounddevice`, `numpy`.
   - Downloads **Piper TTS** (optimized for 32-bit ARM).
   - Downloads **Hindi Voice Models** (Rohan & Priyamvada).
   - Downloads the **Vosk Speech-to-Text Model**.
   - Creates a placeholder song for music playback testing.

   *Note: This process may take 5-10 minutes depending on your internet speed.*

## Step 3: Configure Audio (Important)
Before running the assistant, ensure your microphone and speakers are correctly set up.

1. **List audio devices:**
   ```bash
   aplay -l  # Lists playback devices (Speakers)
   arecord -l # Lists capture devices (Microphone)
   ```

2. **Test Audio Output:**
   ```bash
   aplay /usr/share/sounds/alsa/Front_Center.wav
   ```
   If you don't hear anything, checks your volume settings with `alsamixer`.

3. **Test Microphone:**
   ```bash
   arecord -d 5 test.wav
   aplay test.wav
   ```

## Step 4: Run the Assistant
Start the assistant using Python 3.

```bash
python3 assistant_rpi.py
```

### Usage:
- **Wake Word:** "सुनो" (Suno), "हेलो" (Hello), "अरे" (Are)
- **Commands:**
  - "मेरा नाम क्या है?" -> "My name is Hindi Assistant"
  - "समय क्या है?" -> Tells current time
  - "गाना चलाओ" -> Plays the sample song
  - "आवाज़ बदलो" -> Switches between Male/Female voice
  - "सिस्टम बंद करो" -> Exits the program

## Troubleshooting

- **Error: "OSError: [Errno -9997] Invalid sample rate"**
  - Edit `assistant_rpi.py` and change `OUTPUT_DEVICE`.
  - Try finding the correct device index using `python3 -m sounddevice`.
  
- **Error: "Illegal instruction"**
  - This usually means you are running a 64-bit binary on a 32-bit OS. The `setup_rpi.sh` script downloads the 32-bit version of Piper ("armv7l"). Ensure your OS is indeed 32-bit (`uname -m` should show `armv7l`).

- **Permissions:**
  - If you get permission errors, try running with `sudo`, though it's better to add your user to the `audio` group:
    ```bash
    sudo usermod -aG audio $USER
    ```
    Then reboot.

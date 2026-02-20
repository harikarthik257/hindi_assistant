#!/bin/bash

# Setup Script for Hindi Assistant on Raspberry Pi 4
# Run this script on your Raspberry Pi: bash setup_rpi.sh

echo "========================================="
echo "   Hindi Assistant Setup - Raspberry Pi  "
echo "========================================="

# 1. Update System & Install Dependencies
echo "Step 1: Installing System Dependencies..."
sudo apt update
sudo apt install -y python3-pip libportaudio2 wget unzip tar
# libportaudio2 is required for sounddevice

# 2. Install Python Libraries
echo "Step 2: Installing Python Libraries..."
pip3 install -r requirements.txt --break-system-packages
# Note: --break-system-packages is often needed on newer Raspberry Pi OS unless using venv.
# If you prefer venv, remove the flag and set up a venv first.

# 3. Download Piper (TTS Engine)
echo "Step 3: Downloading Piper TTS (ARM64)..."
mkdir -p piper
cd piper

# Download official release for Linux armv7l (Raspberry Pi 32-bit)
# Using v1.2.0 as it's stable
if [ ! -f "piper" ]; then
    wget -O piper_linux.tar.gz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_armv7l.tar.gz
    tar -xvf piper_linux.tar.gz --strip-components=1
    rm piper_linux.tar.gz
    chmod +x piper
    echo "✅ Piper binary installed (32-bit ARM)."
else
    echo "ℹ️ Piper binary already exists."
fi

# 4. Download Voice Models (Hindi)
echo "Step 4: Downloading Hindi Voice Models..."
mkdir -p model
cd model

# Model 1: Rohan (Male)
if [ ! -f "hi_IN-rohan-medium.onnx" ]; then
    echo "Downloading Rohan (Male)..."
    wget -O hi_IN-rohan-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx
    wget -O hi_IN-rohan-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/rohan/medium/hi_IN-rohan-medium.onnx.json
fi

# Model 2: Priyamvada (Female)
if [ ! -f "hi_IN-priyamvada-medium.onnx" ]; then
    echo "Downloading Priyamvada (Female)..."
    wget -O hi_IN-priyamvada-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx
    wget -O hi_IN-priyamvada-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx.json
fi

cd ../.. # Back to root

# 5. Download Vosk Model (STT)
echo "Step 5: Downloading Vosk Model..."
if [ ! -d "vosk-model-small-hi-0.22" ]; then
    wget -O vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip
    unzip vosk-model.zip
    rm vosk-model.zip
    echo "✅ Vosk model installed."
else
    echo "ℹ️ Vosk model already exists."
fi

# 6. Create Dummy Song (if missing)
mkdir -p music
if [ ! -f "music/song.wav" ]; then
    echo "⚠️ music/song.wav not found. Please place a .wav file there."
    echo "Downloading a sample wav for testing..."
    # Download a small sample wav
    wget -O music/song.wav https://www2.cs.uic.edu/~i101/SoundFiles/StarWars3.wav
fi

echo "========================================="
echo "✅ SETUP COMPLETE!"
echo "To run the assistant, use:"
echo "python3 assistant_rpi.py"
echo "========================================="

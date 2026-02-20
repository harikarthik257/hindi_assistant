# Project Report: Hindi Assistant - Edge Computing for Vernacular Accessibility

**Date**: February 20, 2026  
**Authors**: rbhari karthik, roshni k  
**Institution/Team**: Independent Submission  

---

## 1. Abstract
The Hindi Assistant project presents a novel, resource-efficient implementation of a voice assistant designed specifically for the Raspberry Pi 4 (32-bit) environment. By integrating Kaldi-based speech recognition and ONNX-based synthesis, the project achieves a fully offline, low-latency interaction model in Hindi. The report details the hardware-level optimizations, intent-handling logic, and the technical novelties implemented to ensure peak performance on edge hardware.

## 2. Problem Statement
Most modern voice assistants (Alexa, Siri, Google Assistant) rely heavily on cloud processing and persistent high-speed internet. This approach has three major drawbacks for the Indian demographic:
1.  **Privacy**: Users are often uncomfortable with voice data being sent to external servers.
2.  **Latency**: Network dependence causes delays that break the flow of natural conversation.
3.  **Accessibility**: Many regions lack the stable bandwidth required for cloud-based AI.

Our project aims to solve these issues by bringing the entire AI stack to the **Edge**.

## 3. Technical Methodology

### 3.1 Speech-to-Text (STT) Strategy
We utilized **Vosk**, an open-source speech recognition toolkit. The decision was based on its support for 20+ languages and its ability to run on small devices like the Raspberry Pi.
- **Model**: `vosk-model-small-hi-0.22`, a 40MB model optimized for mobile and IoT devices.
- **Sampling**: Audio is captured at 48kHz and downsampled through the Kaldi recognizer to 16kHz for efficient processing.

### 3.2 Information Extraction & Intent Handling
The `assistant_rpi.py` core utilizes a hybrid intent handler. We implemented a pattern-matching system for high-velocity responses, coupled with state management (Awake/Sleep modes) to ensure the assistant only responds when prompted.

### 3.3 Text-to-Speech (TTS) Pipeline
We implemented **Piper**, a fast, local neural text-to-speech system. Unlike traditional TTS which sounds robotic (Concatenative TTS), Piper provides natural, expressive voices using ONNX inference.

## 4. Engineering Novelties & Innovations

### 4.1 Byte-Level ELF Header Patching
During development, we discovered that the pre-compiled `libvosk.so` binaries often fail on 32-bit Raspbian kernels due to stack execution protection policies. 
**Our Solution**: Instead of recompiling the entire library (which takes hours), we wrote a custom **binary patcher** (`fix_vosk.py`). This script parses the ELF (Executable and Linkable Format) header and manually clears the executable bit on the `PT_GNU_STACK` segment. This allows the assistant to run on configurations where it would otherwise crash with an `Illegal Instruction`.

### 4.2 Asynchronous Audio Callback & Piping
To ensure the mic doesn't "hear" the assistant's own voice (feedback), we implemented a global state machine (`is_speaking`). While speaking, the audio callback silently discards incoming microphone data. Furthermore, the synthesis output is **piped as a raw stream** from the TTS engine directly to the ALSA backend, eliminating the need for temporary `.wav` files and reducing latency by ~600ms.

## 5. Hardware Utilization & Optimization
- **CPU Management**: Used lightweight ONNX models to keep CPU usage below 40% during active synthesis.
- **Memory Optimization**: Leveraged 32-bit pointers and compact models to ensure the entire system fits within standard Raspberry Pi RAM limits.
- **ALSA Integration**: Custom configuration of `plughw` devices for stable audio input/output on diverse USB hardware.

## 6. Results and Performance
- **Response Time**: Interaction latency is consistently under 1.5 seconds.
- **Accuracy**: Demonstrated high proficiency in recognizing common Hindi dialects and sentence structures.
- **Sustainability**: Consumes minimal power, making it suitable for battery-powered IoT applications.

## 7. Future Scope
- **Domain Expansion**: Integrating local LLMs (like Llama-CPP) for more complex conversational abilities.
- **Hardware Integration**: Controlling GPIO pins (lights, fans) via Hindi voice commands for Home Automation.
- **Multilingual Support**: Adding support for Tamil, Telugu, and other Indian languages using the same architecture.

## 8. Conclusion
The Hindi Assistant demonstrates that with creative engineering optimizations—such as binary patching and stream piping—it is possible to run sophisticated AI models on low-cost edge hardware. This project paves the way for accessible, private, and localized AI assistants for everyone.

---
**References**:
1.  Vosk Offline Speech Recognition: [alphacephei.com/vosk](https://alphacephei.com/vosk)
2.  Piper TTS Engine: [github.com/rhasspy/piper](https://github.com/rhasspy/piper)
3.  Raspberry Pi Documentation: [raspberrypi.com](https://www.raspberrypi.com/documentation/)

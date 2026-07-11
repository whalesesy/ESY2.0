import sys
import speech_recognition as sr
import config

# Initialize TTS engine with robust exception handling
try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    # Configure voice properties
    tts_engine.setProperty("rate", config.VOICE_RATE)
    tts_engine.setProperty("volume", config.VOICE_VOLUME)
    
    # Try to set voice based on gender config
    try:
        voices = tts_engine.getProperty("voices")
        if config.VOICE_GENDER == "female" and len(voices) > 1:
            # Look for female voice
            for voice in voices:
                if "female" in voice.name.lower() or "f" in voice.id.lower():
                    tts_engine.setProperty("voice", voice.id)
                    break
        elif len(voices) > 0:
            tts_engine.setProperty("voice", voices[0].id)
    except Exception:
        pass
    
    tts_enabled = True
except Exception as e:
    print(f"[*] Voice output (TTS) disabled: {e}", file=sys.stderr)
    tts_engine = None
    tts_enabled = False

# Initialize STT / Microphone with robust fallback check
mic_enabled = False
try:
    # Attempt to import PyAudio and instantiate Microphone
    import pyaudio
    recognizer = sr.Recognizer()
    # Simple check to see if Microphone works
    with sr.Microphone() as source:
        pass
    mic_enabled = True
except (ImportError, AttributeError, Exception) as e:
    print(f"[*] Voice input (STT) disabled: {e}", file=sys.stderr)
    print("[*] Falling back to Console input mode.", file=sys.stderr)
    recognizer = sr.Recognizer()
    mic_enabled = False


def speak(text: str):
    """Speaks the text aloud if TTS is enabled, and always prints to the console."""
    # Print clean UI message
    print(f"\n[ESY]: {text}")
    
    if tts_enabled and tts_engine:
        try:
            # To avoid locking on some platforms, run the loop carefully
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"\n[!] Speech synthesis error: {e}", file=sys.stderr)


def listen() -> str:
    """Listens for voice input and returns recognized text, or prompts console input if fallback is active."""
    if not mic_enabled:
        # Fallback to keyboard terminal input
        try:
            user_input = input("\nYou: ")
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            return "exit"

    # Microphone interface
    with sr.Microphone() as source:
        print("\nListening...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.8)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
            print("Processing...")
            
            # Using Google's free speech recognition web service
            text = recognizer.recognize_google(audio)
            print(f"You (recognized): {text}")
            return text.strip()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            print("[!] Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"[!] Speech recognition service error: {e}")
            return ""
        except Exception as e:
            print(f"[!] Audio error: {e}")
            return ""

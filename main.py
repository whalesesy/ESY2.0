import sys
import os
import time
import argparse

# Add current directory to path to ensure correct relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
import voice
import commands
import core.memory as memory
import core.brain as brain
from core.plugin_manager import PluginManager

# ANSI Colors for Terminal Styling
CYAN = "\033[36m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    """Prints a beautiful cyberpunk startup banner."""
    banner = f"""
{CYAN}{BOLD}    ███████╗███████╗██╗   ██╗
    ██╔════╝██╔════╝╚██╗ ██╔╝
    █████╗  ███████╗ ╚████╔╝ 
    ██╔══╝  ╚════██║  ╚██╔╝  
    ███████╗███████║   ██║   
    ╚══════╝╚══════╝   ╚═╝   
{RESET}{BLUE}====================================
      {BOLD}ESY A.I. SYSTEM v2.0 (JARVIS){RESET}{BLUE}
===================================={RESET}
[*] Voice output: {"ENABLED" if voice.tts_enabled else "DISABLED (Console fallback)"}
[*] Voice input : {"ENABLED" if voice.mic_enabled else "DISABLED (Console fallback)"}
[*] AI Brain    : {config.AI_PROVIDER.upper()}
[*] Wake words  : {", ".join(config.WAKE_WORDS)}
------------------------------------
    """
    print(banner)


def extract_command(text: str) -> str:
    """Checks for wake word and extracts the command. Returns empty string if wake word not found."""
    import re
    text_lower = text.lower().strip()
    
    # If using console input mode, we don't strictly require a wake word (easier to type directly)
    if not voice.mic_enabled:
        return text
        
    for wake_word in config.WAKE_WORDS:
        # Check if the user said only the wake word
        if text_lower == wake_word:
            return "WAKE_WORD_ONLY"
            
        # Check if the sentence starts with the wake word
        if text_lower.startswith(wake_word + " "):
            return text[len(wake_word) + 1:].strip()
            
        # Check if the sentence contains the wake word
        if wake_word in text_lower:
            # Split by wake word and take everything after it
            parts = re.split(rf'\b{wake_word}\b', text, flags=re.IGNORECASE)
            if len(parts) > 1:
                return parts[1].strip()
                
    return ""


def main():
    parser = argparse.ArgumentParser(description="ESY Jarvis Assistant")
    parser.add_argument("--gui", action="store_true", help="Launch interactive PyQt6 HUD dashboard")
    parser.add_argument("--console", action="store_true", help="Run in terminal CLI console mode")
    args = parser.parse_args()

    # Initialize memory database
    memory.init_db()

    # Determine mode: default is GUI if a display is present and no CLI flag overrides it
    run_in_gui = args.gui
    if not args.console and not args.gui:
        # Automatically attempt GUI if DISPLAY env var is set (Linux/Mac)
        if os.getenv("DISPLAY") or os.name == "nt":
            run_in_gui = True

    if run_in_gui:
        print("[*] Launching ESY PyQt6 HUD Dashboard...")
        try:
            import gui.dashboard as dashboard
            dashboard.run_gui()
            return
        except Exception as e:
            print(f"[!] Failed to launch GUI: {e}. Falling back to Console CLI mode.", file=sys.stderr)

    # Console / CLI mode fallback
    print_banner()
    
    # Load plugins
    plugin_mgr = PluginManager(config.BASE_DIR / "plugins")
    plugin_mgr.load_plugins()

    # Startup greeting
    voice.speak("ESY system initialized. Online and ready.")
    
    should_continue = True
    while should_continue:
        try:
            # 1. Listen for input (Voice or Console)
            raw_input = voice.listen()
            
            if not raw_input:
                continue
                
            # 2. Extract command based on Wake Word rules
            command = extract_command(raw_input)
            
            if not command:
                continue
                
            if command == "WAKE_WORD_ONLY":
                # Prompt the user for their instruction
                voice.speak("Yes? I am listening.")
                # Give them a short window to say their command
                command = voice.listen()
                if not command:
                    voice.speak("Listening timed out.")
                    continue
            
            # Print command for clarity
            print(f"\n{YELLOW}[Processing command: '{command}']{RESET}")
            
            # 3. Route to plugins first
            is_handled, response = plugin_mgr.route_command(command)
            
            # 4. Route to local commands if not handled
            if not is_handled:
                is_handled, should_continue, response = commands.parse_and_execute(command)
                
            # 5. Route to AI Brain if still not handled
            if not is_handled:
                response = brain.query_brain(command)
                is_handled = True
                
            if response:
                voice.speak(response)
                
        except KeyboardInterrupt:
            print("\n[*] Exiting on user keyboard interrupt...")
            should_continue = False
        except Exception as e:
            print(f"\n[!] Error in main loop: {e}", file=sys.stderr)
            time.sleep(1)
            
    # Exit cleanup
    print(f"\n{GREEN}[ESY System Offline]{RESET}")


if __name__ == "__main__":
    main()


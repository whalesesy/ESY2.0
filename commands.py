import datetime
import webbrowser
import subprocess
import re
import sys
import voice

# Configuration for local app launching
APP_MAPPINGS = {
    "terminal": ["qterminal", "gnome-terminal", "xterm"],
    "firefox": ["firefox"],
    "browser": ["firefox", "chromium"],
    "file manager": ["thunar", "pcmanfm", "nautilus"],
    "calculator": ["galculator", "gnome-calculator", "kcalc"]
}

# Configuration for website launching
WEB_MAPPINGS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://www.github.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org"
}


def launch_app(app_name: str) -> bool:
    """Attempts to launch an application from list of candidates."""
    candidates = APP_MAPPINGS.get(app_name.lower())
    if not candidates:
        return False
        
    for cmd in candidates:
        try:
            # Check if command exists
            subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return False


def run_shell_command(cmd: str) -> str:
    """Runs a shell command safely, capturing stdout and stderr."""
    try:
        # Run command with 15 second timeout to prevent hanging
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = result.stdout.strip()
        errors = result.stderr.strip()
        
        # Format display output
        print(f"\n--- [Command Output] ---")
        if output:
            print(output)
        if errors:
            print(f"Errors:\n{errors}", file=sys.stderr)
        print(f"--- [Exit Code: {result.returncode}] ---")
        
        if result.returncode == 0:
            return f"Command executed successfully with exit code 0."
        else:
            return f"Command returned exit code {result.returncode}."
            
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"


def parse_and_execute(command_text: str) -> tuple[bool, bool, str]:
    """
    Parses user input and runs corresponding local automation.
    Returns: (is_local_command, should_continue, response_message)
    """
    text = command_text.strip().lower()
    
    # 1. System Termination Commands
    if text in ["shutdown", "exit", "quit", "stop", "go to sleep", "goodbye"]:
        return True, False, "Shutting down the ESY assistant system. Goodbye."
        
    # 2. Time & Date Commands
    if any(q in text for q in ["what time", "current time", "tell me the time"]):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        return True, True, f"The current time is {time_str}."
        
    if any(q in text for q in ["what date", "today's date", "what is the date", "what day is it"]):
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        day_str = now.strftime("%A")
        return True, True, f"Today is {day_str}, {date_str}."
        
    # 3. Website Openings
    for site, url in WEB_MAPPINGS.items():
        if f"open {site}" in text:
            try:
                webbrowser.open(url)
                return True, True, f"Opening {site.capitalize()} in your default browser."
            except Exception as e:
                return True, True, f"Failed to open browser: {e}"
                
    # Regex match generic url: "open website https://..." or "go to www.example.com"
    site_match = re.search(r'(?:open website|go to)\s+(\S+)', text)
    if site_match:
        url = site_match.group(1)
        if not url.startswith("http"):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return True, True, f"Opening URL {url}."
        except Exception as e:
            return True, True, f"Failed to open website: {e}"
            
    # 4. App Openings
    for app in APP_MAPPINGS.keys():
        if f"open {app}" in text:
            success = launch_app(app)
            if success:
                return True, True, f"Opening {app.capitalize()}."
            else:
                return True, True, f"Could not find or launch {app.capitalize()} on this system."
                
    # 5. Shell Command Executions
    # Matches: "run command [cmd]", "execute [cmd]", "terminal command [cmd]"
    cmd_match = re.search(r'^(?:run command|execute|terminal command)\s+(.+)$', command_text, re.IGNORECASE)
    if cmd_match:
        cmd_to_run = cmd_match.group(1)
        
        # Secure Confirmation flow
        warning_msg = f"Warning: You requested to execute the terminal command: '{cmd_to_run}'. Are you sure you want to run this? Say or type yes to confirm."
        voice.speak(warning_msg)
        
        # Listen for confirmation
        confirm = voice.listen().lower().strip()
        
        if confirm in ["yes", "y", "confirm", "sure", "do it"]:
            voice.speak("Executing command...")
            response = run_shell_command(cmd_to_run)
            return True, True, response
        else:
            return True, True, "Command execution aborted."
            
    # If no local command matches, pass to AI
    return False, True, ""

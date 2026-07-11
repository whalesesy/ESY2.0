import re
import datetime
import commands
import core.memory as memory
from core.plugin import BasePlugin

class ProductivityPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Productivity Manager"
        self.description = "Manages custom note taking, system alarms/reminders, and application launching."
        self.keywords = [
            "take note", "write note", "record note", "add note", "list notes", "show notes", "read notes", "clear notes", "delete notes",
            "remind me", "set reminder", "list reminders", "show reminders",
            "open terminal", "open firefox", "open browser", "open file manager", "open calculator"
        ]

    def execute(self, command_text: str) -> str:
        cmd_lower = command_text.lower().strip()
        
        # 1. Note-taking commands
        # "take note ...", "write note ...", etc.
        note_match = re.search(r'^(?:take note|write note|record note|add note)\s+(.+)$', command_text, re.IGNORECASE)
        if note_match:
            note_content = note_match.group(1).strip()
            memory.add_note(note_content)
            memory.log_event("info", f"Saved note: {note_content[:30]}...")
            return f"Note recorded: '{note_content}'."
            
        if any(kw in cmd_lower for kw in ["list notes", "show notes", "read notes", "get notes"]):
            notes = memory.get_all_notes()
            if not notes:
                return "You do not have any notes saved."
            note_list = [f"[{note['id']}] {note['content']} (saved {note['created_at']})" for note in notes]
            return "Here are your saved notes: " + " | ".join(note_list)
            
        if any(kw in cmd_lower for kw in ["clear notes", "delete notes", "remove notes"]):
            memory.delete_all_notes()
            memory.log_event("info", "Deleted all notes")
            return "All notes have been cleared."

        # 2. Reminder commands
        # "remind me in 5 minutes to take a break"
        # "remind me in 1 hour to sleep"
        reminder_match = re.search(
            r'remind me\s+(?:in\s+)?(\d+)\s*(minute|minutes|min|mins|hour|hours|hr|hrs|second|seconds|sec|secs)?\s*(?:to|that)?\s*(.+)',
            command_text,
            re.IGNORECASE
        )
        if reminder_match:
            amount = int(reminder_match.group(1))
            unit = reminder_match.group(2)
            message = reminder_match.group(3).strip()
            
            # Default to minutes if unit is not specified
            if not unit:
                unit = "minutes"
            else:
                unit = unit.lower()
                
            delta = None
            if "sec" in unit:
                delta = datetime.timedelta(seconds=amount)
            elif "hour" in unit or "hr" in unit:
                delta = datetime.timedelta(hours=amount)
            else: # min/minute
                delta = datetime.timedelta(minutes=amount)
                
            target_time = (datetime.datetime.now() + delta).isoformat()
            memory.add_reminder(message, target_time)
            memory.log_event("info", f"Set reminder: {message} at {target_time}")
            
            # Speakable confirmation
            time_label = f"{amount} {unit}"
            return f"Understood. I will remind you to '{message}' in {time_label}."
            
        if any(kw in cmd_lower for kw in ["list reminders", "show reminders"]):
            reminders = memory.get_pending_reminders()
            if not reminders:
                return "You have no pending reminders."
            rem_list = []
            for rem in reminders:
                try:
                    # Format ISO time nicely
                    dt = datetime.datetime.fromisoformat(rem['target_time'])
                    time_str = dt.strftime("%I:%M %p")
                    rem_list.append(f"'{rem['message']}' at {time_str}")
                except Exception:
                    rem_list.append(f"'{rem['message']}' at {rem['target_time']}")
            return "Your pending reminders: " + ", ".join(rem_list)

        # 3. Application Launcher (pass back to commands.py app launcher mappings)
        for app in commands.APP_MAPPINGS.keys():
            if f"open {app}" in cmd_lower:
                success = commands.launch_app(app)
                if success:
                    return f"Opening {app.capitalize()}."
                else:
                    return f"Could not launch {app.capitalize()} on this system."

        return "Productivity operation failed."

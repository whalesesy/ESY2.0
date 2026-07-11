import sqlite3
import datetime
from pathlib import Path
import sys
import config

DB_PATH = config.MEMORY_DIR / "esy_memory.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Reminders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            target_time TEXT NOT NULL,  -- ISO format string or datetime representation
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Audit/Audit Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Cybersecurity Training Lab Tracker Schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_labs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,       -- 'Hack The Box', 'TryHackMe', 'PortSwigger'
            room_name TEXT NOT NULL,      -- e.g., 'Archetype', 'Blue', 'SQL Injection'
            flags_found INTEGER DEFAULT 0, -- Number of flags captured
            completed_at TEXT NOT NULL,   -- Timestamp string
            notes TEXT                    -- Attack vector notes
        )
    """)
    
    # Lifestyle and Nutrition Tracker Schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lifestyle_nutrition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_type TEXT NOT NULL,      -- 'Breakfast', 'Lunch', 'Dinner', 'Snack'
            food_item TEXT NOT NULL,      -- e.g., 'Chicken and Rice', 'Oats'
            calories INTEGER DEFAULT 0,
            protein INTEGER DEFAULT 0,    -- Grams
            logged_at TEXT NOT NULL,      -- Timestamp string
            notes TEXT                    -- Notes about context or mental focus
        )
    """)
    
    conn.commit()
    conn.close()
    print("[*] Database initialized successfully.")


# --- Chat History Functions ---

def save_chat_message(role: str, content: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (role, content) VALUES (?, ?)",
            (role, content)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error saving chat message: {e}", file=sys.stderr)

def get_chat_history(limit=50) -> list:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        # Return in chronological order
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    except Exception as e:
        print(f"[!] Database error loading chat history: {e}", file=sys.stderr)
        return []

def clear_chat_history():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error clearing chat history: {e}", file=sys.stderr)

# --- Preference Functions ---

def get_preference(key: str, default: str = None) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["value"]
        return default
    except Exception:
        return default

def set_preference(key: str, value: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error setting preference: {e}", file=sys.stderr)

# --- Notes Functions ---

def add_note(content: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error adding note: {e}", file=sys.stderr)

def get_all_notes() -> list:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, created_at FROM notes ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "content": r["content"], "created_at": r["created_at"]} for r in rows]
    except Exception as e:
        print(f"[!] Database error getting notes: {e}", file=sys.stderr)
        return []

def delete_all_notes():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error deleting all notes: {e}", file=sys.stderr)

# --- Reminder Functions ---

def add_reminder(message: str, target_time: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (message, target_time, status) VALUES (?, ?, 'pending')",
            (message, target_time)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error adding reminder: {e}", file=sys.stderr)

def get_pending_reminders() -> list:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, message, target_time FROM reminders WHERE status = 'pending'")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r["id"], "message": r["message"], "target_time": r["target_time"]} for r in rows]
    except Exception as e:
        print(f"[!] Database error getting pending reminders: {e}", file=sys.stderr)
        return []

def mark_reminder_done(reminder_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET status = 'done' WHERE id = ?", (reminder_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Database error marking reminder done: {e}", file=sys.stderr)

# --- Audit Logs ---

def log_event(level: str, message: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (level, message) VALUES (?, ?)",
            (level, message)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

# --- Security Lab Tracker Functions ---

def log_lab_completion(platform: str, room_name: str, flags: int, notes: str = "") -> bool:
    """Logs a completed lab room or box into the database."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO security_labs (platform, room_name, flags_found, completed_at, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (platform, room_name, flags, timestamp, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Database Error logging lab: {e}", file=sys.stderr)
        return False

def get_lab_history(platform: str = None) -> list:
    """Retrieves lab completion history. Optionally filters by platform."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if platform:
            cursor.execute("""
                SELECT platform, room_name, flags_found, completed_at, notes 
                FROM security_labs WHERE LOWER(platform) = LOWER(?) ORDER BY completed_at DESC
            """, (platform,))
        else:
            cursor.execute("""
                SELECT platform, room_name, flags_found, completed_at, notes 
                FROM security_labs ORDER BY completed_at DESC
            """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "platform": r["platform"],
                "room_name": r["room_name"],
                "flags_found": r["flags_found"],
                "completed_at": r["completed_at"],
                "notes": r["notes"]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[!] Database Error getting lab history: {e}", file=sys.stderr)
        return []

def get_security_stats() -> dict:
    """Calculates global training metrics for the dashboard view."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(flags_found) FROM security_labs")
        total_rooms, total_flags = cursor.fetchone()
        conn.close()
        
        total_rooms = total_rooms or 0
        total_flags = total_flags or 0
        
        return {
            "total_rooms": total_rooms,
            "total_flags": total_flags
        }
    except Exception as e:
        print(f"[!] Database Error getting security stats: {e}", file=sys.stderr)
        return {"total_rooms": 0, "total_flags": 0}

# --- Lifestyle and Nutrition Tracker Functions ---

def log_food_entry(meal_type: str, food_item: str, calories: int, protein: int, notes: str = "") -> bool:
    """Logs a food item, calorie and protein intake into the database."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lifestyle_nutrition (meal_type, food_item, calories, protein, logged_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (meal_type, food_item, calories, protein, timestamp, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[!] Database Error logging nutrition: {e}", file=sys.stderr)
        return False

def get_nutrition_history(limit: int = 10) -> list:
    """Retrieves the recent nutrition history."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meal_type, food_item, calories, protein, logged_at, notes
            FROM lifestyle_nutrition ORDER BY logged_at DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "meal_type": r["meal_type"],
                "food_item": r["food_item"],
                "calories": r["calories"],
                "protein": r["protein"],
                "logged_at": r["logged_at"],
                "notes": r["notes"]
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[!] Database Error getting nutrition history: {e}", file=sys.stderr)
        return []

def get_nutrition_stats() -> dict:
    """Calculates daily nutrition metrics (totals for today)."""
    try:
        today_prefix = datetime.datetime.now().strftime("%Y-%m-%d") + "%"
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(calories), SUM(protein) FROM lifestyle_nutrition
            WHERE logged_at LIKE ?
        """, (today_prefix,))
        total_calories, total_protein = cursor.fetchone()
        conn.close()
        
        total_calories = total_calories or 0
        total_protein = total_protein or 0
        
        return {
            "total_calories": total_calories,
            "total_protein": total_protein
        }
    except Exception as e:
        print(f"[!] Database Error getting nutrition stats: {e}", file=sys.stderr)
        return {"total_calories": 0, "total_protein": 0}



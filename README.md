# ESY A.I. System v2.0 (Jarvis)

ESY is a cyberpunk-themed operations, cybersecurity, and lifestyle assistant designed to run locally on Linux. It features an interactive PyQt6 glassmorphic HUD dashboard, modular plugin managers, a persistent SQLite memory database, and a hybrid AI router that matches query complexity to active LLM providers.

---

## Key Features

1. **Cyberpunk PyQt6 HUD Dashboard**:
   * Displays real-time hardware metrics (CPU load, Memory, Disk space, Battery level).
   * Features an animated, paint-event soundwave reflecting voice input state.
   * Built-in terminal chat log showing input/output streams.
   * Background async worker thread (`QThread`) prevents speech and API calls from blocking the UI.

2. **Modular Plugin Architecture**:
   * **Security Intelligence**: Cross-references CVE codes against public CIRCL API databases and CISA's Known Exploited Vulnerabilities feed. Provides OWASP frameworks and maps vulnerable targets to Hack The Box, TryHackMe, and PortSwigger learning rooms.
   * **Lifestyle & Nutrition**: Contacts the Open Food Facts API for barcode/ingredient macro checks and tracks daily calorie and protein logs in the local database.
   * **System Monitor**: Lists active resource-hogging system processes, CPU, and Memory metrics.
   * **Network Diagnostics**: Scans active interface IP/MAC details and tests host-to-host ping latencies.
   * **Productivity Manager**: Handles database-linked notes, timers, active reminders, and launches local apps.
   * **Knowledge OSINT Search**: Hits DuckDuckGo and Wikipedia summaries to parse quick technical answers.

3. **Persistent SQLite Memory**:
   * Operates entirely out of a single-file database (`esy_memory.db`).
   * Archives chat transcripts, custom key-value preferences, daily food logs, CTF room completions, notes, and reminders.

4. **Hybrid LLM Routing Engine**:
   * Automatically selects the optimal engine based on internet status and keys: `Groq` -> `Gemini` -> `OpenAI` -> `Ollama (Local)` -> `Offline Rule System`.

---

## Installation & Setup

1. **Clone and Navigate**:
   ```bash
   git clone https://github.com/whalesesy/ESY2.0.git
   cd ESY2.0
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/env/activate  # Or your shell equivalent
   pip install -r requirements.txt
   ```

3. **Configure Environment variables (`.env`)**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_key
   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   ```

---

## Usage

You can launch ESY in either GUI or CLI mode:

### 1. Launch in GUI HUD Mode
To run the interactive desktop window:
```bash
.venv/bin/python main.py --gui
```

### 2. Launch in CLI Console Mode
To interact directly through your terminal shell:
```bash
.venv/bin/python main.py --console
```

---

## Operational Commands to Try

* **System Status**: `show cpu load` or `list running processes`
* **Network Latency**: `check internet connection` or `ping latency`
* **Vulnerability Threat Intel**: `check CVE-2021-44228`
* **CTF Progress Tracking**: `log room HTB Archetype flags 2 notes Exploited SMB`
* **Show Training History**: `show progress` or `lab stats`
* **Open Food Facts Lookup**: `check product oats` or `check product 5449000000996`
* **Log Daily Macros**: `log meal lunch oats 400 cals 20 protein`
* **Show Calorie Summary**: `show nutrition` or `nutrition stats`
* **Productivity**: `take note draft security architecture plan` or `read my notes`

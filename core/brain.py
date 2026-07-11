import os
import sys
import socket
import urllib.request
import json
import config
from openai import OpenAI
import core.memory as memory

# Clients cache
_groq_client = None
_gemini_model = None
_openai_client = None
_ollama_client = None

SYSTEM_PROMPT = (
    "You are Jarvis, an advanced cybersecurity operations assistant and efficiency engineer for the user's life operations. "
    "When answering security, network, or vulnerability questions, structure your answers through the lens of:\n"
    "1. OWASP Top 10 & CWE classifications (for Web / Application Flaws).\n"
    "2. NIST Standards & MITRE ATT&CK Matrices (for Enterprise / Network defense context).\n"
    "3. Recommend specific practical learning spaces: Hack The Box, TryHackMe, and PortSwigger Web Security Academy.\n"
    "When asked about food decisions, diets, or meal plans:\n"
    "1. Optimize for cognitive performance, sustainable energy output, and minimal cognitive load.\n"
    "2. Provide fast, highly structural meal blueprints (e.g., macros, prep time, and item dependencies).\n"
    "3. Factor in high-intensity workstation environments (suggest clean, minimal-mess foods near development equipment).\n"
    "Keep explanations highly technical, brief, actionable, and suitable for being read aloud by a Text-to-Speech system."
)



def check_internet(host="8.8.8.8", port=53, timeout=2) -> bool:
    """Checks internet connectivity by attempting to open a socket connection to Google DNS."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def check_ollama(timeout=1.5) -> bool:
    """Checks if a local Ollama instance is running and reachable."""
    url = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
    # Clean up to get root
    if "/v1" in url:
        root_url = url.replace("/v1", "")
    else:
        root_url = url
    try:
        req = urllib.request.Request(root_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True
    except Exception:
        pass
    return False

def get_best_provider() -> str:
    """Dynamically determines the best AI provider available based on internet & settings."""
    has_internet = check_internet()
    
    # 1. Groq (if key exists & internet works)
    if config.GROQ_API_KEY and has_internet:
        return "groq"
        
    # 2. Gemini (if key exists & internet works)
    if config.GEMINI_API_KEY and has_internet:
        return "gemini"
        
    # 3. OpenAI (if key exists & internet works)
    if config.OPENAI_API_KEY and has_internet:
        return "openai"
        
    # 4. Ollama (if running locally)
    if check_ollama():
        return "ollama"
        
    # 5. Offline Fallback
    return "offline"

def get_groq_client():
    global _groq_client
    if _groq_client is None and config.GROQ_API_KEY:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=config.GROQ_API_KEY)
        except Exception as e:
            print(f"[!] Failed to initialize Groq client: {e}", file=sys.stderr)
    return _groq_client

def get_gemini_model():
    global _gemini_model
    if _gemini_model is None and config.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            _gemini_model = genai.GenerativeModel(
                model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                system_instruction=SYSTEM_PROMPT
            )
        except Exception as e:
            print(f"[!] Failed to initialize Gemini client: {e}", file=sys.stderr)
    return _gemini_model

def get_openai_client():
    global _openai_client
    if _openai_client is None and config.OPENAI_API_KEY:
        try:
            _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        except Exception as e:
            print(f"[!] Failed to initialize OpenAI client: {e}", file=sys.stderr)
    return _openai_client

def get_ollama_client():
    global _ollama_client
    # Ollama uses openai client point to local endpoint
    if _ollama_client is None:
        try:
            base_url = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")
            _ollama_client = OpenAI(api_key="ollama", base_url=base_url)
        except Exception as e:
            print(f"[!] Failed to initialize Ollama client wrapper: {e}", file=sys.stderr)
    return _ollama_client

def query_brain(prompt: str) -> str:
    """Routes prompt to the best available brain, integrating history and logging."""
    # 1. Fetch chat history from memory
    history = memory.get_chat_history(limit=10)
    
    # Save the user message to DB
    memory.save_chat_message("user", prompt)
    
    provider = get_best_provider()
    memory.log_event("info", f"Querying AI Brain using provider: {provider}")
    
    reply = ""
    try:
        if provider == "groq":
            client = get_groq_client()
            if client:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": prompt}]
                model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=250,
                    temperature=0.7
                )
                reply = response.choices[0].message.content.strip()
                
        elif provider == "gemini":
            model = get_gemini_model()
            if model:
                # Structure history for Gemini
                contents = []
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [msg["content"]]})
                contents.append({"role": "user", "parts": [prompt]})
                
                response = model.generate_content(contents)
                reply = response.text.strip()
                
        elif provider == "openai":
            client = get_openai_client()
            if client:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": prompt}]
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=250,
                    temperature=0.7
                )
                reply = response.choices[0].message.content.strip()
                
        elif provider == "ollama":
            client = get_ollama_client()
            if client:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": prompt}]
                model = os.getenv("OLLAMA_MODEL", "llama3.2")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=250,
                    temperature=0.7
                )
                reply = response.choices[0].message.content.strip()
                
    except Exception as e:
        print(f"[!] Brain query error ({provider}): {e}. Falling back to offline brain.", file=sys.stderr)
        memory.log_event("error", f"Brain query error ({provider}): {str(e)}")
        provider = "offline"

    if not reply or provider == "offline":
        reply = get_offline_response(prompt)
        
    # Save the assistant response to DB
    memory.save_chat_message("assistant", reply)
    return reply

def get_offline_response(prompt: str) -> str:
    """Offline rule-based assistant responses."""
    p_lower = prompt.lower()
    
    if "sql injection" in p_lower:
        return ("SQL injection is a critical vulnerability where database queries are manipulated "
                "via input. Always use parameterized queries or prepared statements.")
    elif "nmap" in p_lower:
        return ("Nmap is a network scanning tool. Use 'nmap -sV [IP]' to detect service versions.")
    elif "who are you" in p_lower or "your name" in p_lower:
        return "I am ESY, your autonomous AI system assistant. Currently running in offline mode."
    elif "hello" in p_lower or "hi " in p_lower or p_lower == "hi":
        return "Hello! I am ESY. How can I help you today?"
    else:
        return ("I am currently in offline mode with no active LLM APIs or Ollama. "
                "Please check your internet connection or configure API keys in the '.env' file.")

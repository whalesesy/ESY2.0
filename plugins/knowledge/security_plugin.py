import re
import urllib.request
import json
import sys
import core.memory as memory
from core.plugin import BasePlugin

class SecurityIntelligencePlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Security Intelligence Router"
        self.description = "Queries vulnerability databases, OWASP Top 10, NIST standards, and logs completed training rooms."
        self.keywords = [
            "cve", "owasp", "nist", "vulnerability", "portswigger", "tryhackme", "htb", "hackthebox",
            "log room", "completed machine", "show progress", "lab stats"
        ]

    def execute(self, command_text: str) -> str:
        command_lower = command_text.lower().strip()

        # 1. Log completed lab room/machine
        if "log room" in command_lower or "completed machine" in command_lower:
            # Parse command: e.g. "log room HTB Archetype flags 2 notes Windows SMB exploit"
            # Regex: match "log room" or "completed machine" followed by platform, room name, optional flags, and optional notes
            pattern = r'(?:log room|completed machine)\s+(htb|hack\s*the\s*box|tryhackme|thm|portswigger)\s+(\S+)(?:\s+flags\s+(\d+))?(?:\s+notes\s+(.+))?'
            match = re.search(pattern, command_lower, re.IGNORECASE)
            
            if match:
                platform_raw = match.group(1).lower().strip()
                room_name = match.group(2).strip()
                flags_raw = match.group(3)
                notes = match.group(4).strip() if match.group(4) else ""
                
                # Standardize platform name
                if "htb" in platform_raw or "hack" in platform_raw:
                    platform = "Hack The Box"
                elif "thm" in platform_raw or "try" in platform_raw:
                    platform = "TryHackMe"
                else:
                    platform = "PortSwigger"
                    
                flags = int(flags_raw) if flags_raw else 1
                
                success = memory.log_lab_completion(platform, room_name, flags, notes)
                if success:
                    return f"🛡️ **Jarvis Logged:** {platform} room '{room_name}' ({flags} flags) has been archived into your database persistence."
                else:
                    return "❌ Error: Failed to save the room completion into memory database."
            else:
                return (
                    "⚠️ **Logging Helper:** To log a completed room, use the format:\n"
                    "`log room [HTB|TryHackMe|PortSwigger] [RoomName] flags [Count] notes [Takeaway details]`\n"
                    "Example: `log room HTB Archetype flags 2 notes Exploited SMB via misconfigured MSSQL`"
                )

        # 2. Show progress / Lab stats
        if "show progress" in command_lower or "lab stats" in command_lower:
            stats = memory.get_security_stats()
            history = memory.get_lab_history()
            
            output = (
                f"📊 **Jarvis Tactical Training Overview:**\n"
                f"• Total Rooms Compromised: {stats['total_rooms']}\n"
                f"• Total Flags Captured: {stats['total_flags']}\n\n"
                f"**Recent Activity Log:**\n"
            )
            
            if not history:
                output += "No lab completions recorded yet."
            else:
                for row in history[:5]: # Show last 5 completed rooms
                    notes_str = f" | *Note: {row['notes']}*" if row['notes'] else ""
                    output += f"• [{row['completed_at'][:10]}] {row['platform']} - **{row['room_name']}** ({row['flags_found']} flags){notes_str}\n"
                    
            return output

        # 3. NIST / CVE Dynamic Retrieval
        # e.g., "check CVE-2021-44228"
        cve_match = re.search(r'\bcve-\d{4}-\d{4,7}\b', command_lower)
        if cve_match:
            cve_id = cve_match.group(0).upper()
            cve_data = self._fetch_cve_data(cve_id)
            cisa_data = self._fetch_cisa_kev_status(cve_id)
            return cve_data + cisa_data

        # 4. OWASP Reference Handler
        if "owasp" in command_lower:
            return (
                "🛡️ **OWASP Top 10 Security Reference Matrix:**\n"
                "The Open Worldwide Application Security Project focuses on critical web application risks:\n"
                "• **A01:2021-Broken Access Control:** Critical target on PortSwigger labs & Hack The Box machines.\n"
                "• **A03:2021-Injection:** SQLi, Command Injection, and Template Injection found heavily on TryHackMe.\n"
                "• **A06:2021-Vulnerable and Outdated Components:** Common initial foothold vectors on HTB.\n\n"
                "👉 *Recommended Practice: Complete the 'Web Security Academy' paths on PortSwigger, or spin up the 'Web Requests' modules on HTB Academy.*"
            )

        # 5. Lab Training Suggestions (HTB, THM, PortSwigger)
        if any(x in command_lower for x in ["htb", "hackthebox", "tryhackme", "thm", "portswigger"]):
            return self._get_lab_guidance(command_lower)

        # 6. Fallback General Security Query Handler
        return (
            "🔍 **Jarvis Security Router:** I detected a general security query.\n"
            "- For CVE threat intelligence, query by ID (e.g. `check CVE-2021-44228`).\n"
            "- To log your training progress, say `log room [platform] [room] flags [count] notes [takeaways]`.\n"
            "- To view your training statistics, say `show progress`.\n"
            "- For learning tracks, ask `how do I learn SQLi on Hack The Box`."
        )

    def _fetch_cve_data(self, cve_id: str) -> str:
        """Queries the public CIRCL CVE API for real-time NIST/MITRE data."""
        url = f"https://cve.circl.lu/api/cve/{cve_id}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ESYAssistant/2.0'})
            with urllib.request.urlopen(req, timeout=5.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data:
                        summary = data.get("summary", "No summary details provided.")
                        cvss = data.get("cvss", "Unknown")
                        cwes = data.get("cwe", "N/A")
                        # Clean list of CWEs to string
                        if isinstance(cwes, list):
                            cwes = ", ".join(cwes)
                        return (
                            f"⚠️ **NIST/MITRE Threat Intelligence for {cve_id}**\n"
                            f"• **CVSS Score:** {cvss}\n"
                            f"• **Associated CWEs:** {cwes}\n"
                            f"• **Description:** {summary}\n"
                        )
            return f"❌ Could not find details for {cve_id} in the public threat databases."
        except Exception as e:
            return f"⚠️ Network error querying NIST/MITRE feed: {str(e)}"

    def _fetch_cisa_kev_status(self, cve_id: str) -> str:
        """Checks the live CISA database to see if the vulnerability is weaponized."""
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ESYAssistant/2.0'})
            with urllib.request.urlopen(req, timeout=5.0) as response:
                if response.status == 200:
                    catalog = json.loads(response.read().decode('utf-8'))
                    for vuln in catalog.get("vulnerabilities", []):
                        if vuln.get("cveID") == cve_id.upper():
                            return (
                                f"\n🚨 **CISA KEV WARNING:** This vulnerability is actively exploited!\n"
                                f"• **Ransomware Action:** {vuln.get('knownRansomwareCampaignUse', 'Unknown')}\n"
                                f"• **Required Action:** {vuln.get('requiredAction', 'Patch immediately.')}"
                            )
                    return "\n✅ *Not noted in the CISA Known Exploited Catalog.*"
            return ""
        except Exception as e:
            return f"\n⚠️ Could not pull CISA tracking feed: {e}"


    def _get_lab_guidance(self, command: str) -> str:
        """Maps specific vulnerabilities or concepts to hands-on learning labs."""
        guidance = "🎯 **Hands-on Lab Map Engine:**\n"
        
        if "sqli" in command or "sql injection" in command:
            guidance += (
                "• **PortSwigger:** Execute the 'SQL Injection' room path. They provide outstanding, free, progressive interactive sandboxes with labs targeting blind SQLi and out-of-band extraction.\n"
                "• **TryHackMe:** Search for the 'SQL Injection' room inside the Web Fundamentals pathway for a guided walk-through.\n"
                "• **Hack The Box:** Spin up the active machine 'Archetype' (Starting Point) or complete the HTB Academy SQL Injection module."
            )
        elif "xss" in command or "cross site scripting" in command:
            guidance += (
                "• **PortSwigger:** Use the Web Security Academy XSS dashboard to learn DOM-based, Stored, and Reflected bypass strategies.\n"
                "• **TryHackMe:** Go through the 'Cross-Site Scripting' room to grasp payload deliveries."
            )
        else:
            guidance += (
                "• **Offensive Labs (HTB / THM):** Focus on TryHackMe for guided, structural knowledge paths (Pre-Security -> JR Penetration Tester). Switch over to Hack The Box (Starting Point -> Tier 1/2) for unguided, black-box realistic challenges.\n"
                "• **Web In-Depth (PortSwigger):** Use their dedicated academy tracks alongside Burp Suite to learn server-side and client-side web flaws perfectly."
            )
        return guidance

import urllib.request
import urllib.parse
import json
import re
import sys
from core.plugin import BasePlugin

class KnowledgePlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Knowledge Search"
        self.description = "Performs online search querying DuckDuckGo and Wikipedia APIs for facts and information."
        self.keywords = [
            "search for", "search web for", "who is", "what is", "tell me about", "wikipedia"
        ]

    def _query_duckduckgo(self, query: str) -> str:
        """Queries the DuckDuckGo Instant Answer API."""
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check AbstractText
                abstract = data.get("AbstractText", "")
                if abstract:
                    return abstract
                    
                # Check Definition
                definition = data.get("Definition", "")
                if definition:
                    return definition
        except Exception:
            pass
        return ""

    def _query_wikipedia(self, query: str) -> str:
        """Queries Wikipedia's Summary API."""
        # Convert query to CamelCase or Wikipedia format (spaces to underscores)
        formatted_query = query.strip().replace(" ", "_")
        encoded_query = urllib.parse.quote(formatted_query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ESYAssistant/1.0'})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Check Extract
                extract = data.get("extract", "")
                if extract:
                    return extract
        except Exception:
            pass
        return ""

    def execute(self, command_text: str) -> str:
        # Extract query search terms
        query = ""
        # Matches: "search for [query]", "search web for [query]", "who is [query]", "what is [query]", "tell me about [query]"
        match = re.search(
            r'(?:search for|search web for|who is|what is|tell me about|wikipedia)\s+(.+)$',
            command_text,
            re.IGNORECASE
        )
        if match:
            query = match.group(1).strip()
        else:
            query = command_text.strip()
            
        if not query:
            return "What would you like me to search for?"
            
        print(f"[*] Querying DuckDuckGo and Wikipedia for: '{query}'...")
        
        # Try DuckDuckGo first
        ddg_result = self._query_duckduckgo(query)
        if ddg_result:
            return ddg_result
            
        # Try Wikipedia next
        wiki_result = self._query_wikipedia(query)
        if wiki_result:
            return wiki_result
            
        return f"I couldn't find a direct summary for '{query}' online. You can try searching in the browser."

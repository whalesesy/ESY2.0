import socket
import psutil
import time
import subprocess
from core.plugin import BasePlugin

class NetworkPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "Network Diagnostics"
        self.description = "Retrieves network configuration, IP/MAC addresses, and connection latency."
        self.keywords = [
            "network status", "ip address", "mac address", "ping latency", 
            "connection status", "dns status", "internet speed", "latency"
        ]

    def _get_local_ip(self) -> str:
        """Gets local IP address of active interface."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _ping_latency(self, host="8.8.8.8") -> float:
        """Pings a host to find latency in milliseconds. Returns -1.0 if host is unreachable."""
        try:
            start = time.time()
            socket.setdefaulttimeout(2.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, 53))
            latency = (time.time() - start) * 1000
            return latency
        except Exception:
            return -1.0

    def execute(self, command_text: str) -> str:
        cmd_lower = command_text.lower().strip()
        
        # 1. IP/MAC Address query
        if "ip" in cmd_lower or "mac" in cmd_lower or "interface" in cmd_lower:
            local_ip = self._get_local_ip()
            interfaces = psutil.net_if_addrs()
            
            # Retrieve active interface MAC address
            mac_address = "unknown"
            for interface_name, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK: # MAC address type
                        # Only pick if this interface is active
                        for ip_addr in addrs:
                            if ip_addr.address == local_ip:
                                mac_address = addr.address
                                break
            
            return f"Your active IP address is {local_ip} with physical MAC address {mac_address}."
            
        # 2. Ping / Latency / Connection query
        if "ping" in cmd_lower or "latency" in cmd_lower or "connection" in cmd_lower or "internet" in cmd_lower:
            latency = self._ping_latency()
            if latency >= 0:
                return f"Internet connection is active. Ping latency to DNS 8.8.8.8 is {latency:.1f} milliseconds."
            else:
                return "Internet connection appears to be offline. Failed to ping external services."
                
        # 3. DNS query
        if "dns" in cmd_lower:
            try:
                # Basic check by resolving a domain
                start = time.time()
                socket.gethostbyname("google.com")
                duration = (time.time() - start) * 1000
                return f"DNS configuration is operational. Google resolved in {duration:.1f} milliseconds."
            except Exception:
                return "DNS resolution failed. Please check your network configuration."
                
        # Default network summary
        local_ip = self._get_local_ip()
        latency = self._ping_latency()
        status = f"online (latency: {latency:.1f}ms)" if latency >= 0 else "offline"
        return f"Network summary: Primary IP is {local_ip}. Internet connectivity is {status}."

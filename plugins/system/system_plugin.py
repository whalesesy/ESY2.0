import psutil
from core.plugin import BasePlugin

class SystemPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "System Intelligence"
        self.description = "Provides real-time system resource metrics (CPU, RAM, Disk, Battery, Processes)."
        self.keywords = [
            "system status", "cpu load", "cpu usage", "memory usage", "ram usage", 
            "disk space", "battery status", "running processes", "system metrics"
        ]

    def execute(self, command_text: str) -> str:
        cmd_lower = command_text.lower().strip()
        
        # 1. CPU specific query
        if "cpu" in cmd_lower:
            cpu_pct = psutil.cpu_percent(interval=0.5)
            cores = psutil.cpu_count()
            return f"CPU usage is currently at {cpu_pct}% across {cores} cores."
            
        # 2. Memory / RAM query
        if "memory" in cmd_lower or "ram" in cmd_lower:
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            return f"System Memory is at {mem.percent}% utilization. Using {used_gb:.2f} GB of {total_gb:.2f} GB."
            
        # 3. Disk query
        if "disk" in cmd_lower or "storage" in cmd_lower:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            total_gb = disk.total / (1024 ** 3)
            return f"System Disk utilization is at {disk.percent}%. {free_gb:.2f} GB free of {total_gb:.2f} GB total."
            
        # 4. Battery query
        if "battery" in cmd_lower:
            bat = psutil.sensors_battery()
            if bat:
                plugged = "plugged in" if bat.power_plugged else "unplugged"
                return f"System battery is at {bat.percent}% and currently {plugged}."
            else:
                return "No battery detected (likely running on desktop power)."
                
        # 5. Top Processes query
        if "processes" in cmd_lower or "process" in cmd_lower:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            # Sort by CPU usage
            processes = sorted(processes, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:5]
            proc_strings = [f"{p['name']} (PID: {p['pid']}, CPU: {p['cpu_percent']:.1f}%)" for p in processes if p['cpu_percent'] is not None]
            return "Top running processes: " + ", ".join(proc_strings)
            
        # General Status overview
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        bat = psutil.sensors_battery()
        bat_str = f", Battery: {bat.percent}%" if bat else ""
        
        return (f"System status summary: CPU usage is {cpu_pct}%, Memory is at {mem.percent}%, "
                f"Disk space is at {disk.percent}% used{bat_str}.")

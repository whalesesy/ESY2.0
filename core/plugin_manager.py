import os
import sys
import importlib.util
from pathlib import Path
from core.plugin import BasePlugin

class PluginManager:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.plugins = []
        
    def load_plugins(self):
        """Discovers and instantiates all subclasses of BasePlugin in plugins_dir."""
        self.plugins = []
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return

        # Add plugins parent dir to sys.path to allow relative imports inside plugins
        project_dir = self.plugins_dir.parent
        if str(project_dir) not in sys.path:
            sys.path.append(str(project_dir))

        for root, _, files in os.walk(self.plugins_dir):
            for file in files:
                if file.endswith("_plugin.py") and not file.startswith("__"):
                    file_path = Path(root) / file
                    self._load_plugin_file(file_path)
                    
        print(f"[*] Loaded {len(self.plugins)} plugins.")

    def _load_plugin_file(self, file_path: Path):
        """Loads a plugin module from a file path and instantiates its plugin class."""
        try:
            # Generate a unique module name based on path
            module_name = file_path.stem
            
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec is None or spec.loader is None:
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find any class that inherits from BasePlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    plugin_instance = attr()
                    self.plugins.append(plugin_instance)
                    print(f"[+] Registered plugin: {plugin_instance.name} ({file_path.name})")
        except Exception as e:
            print(f"[!] Failed to load plugin file {file_path.name}: {e}", file=sys.stderr)

    def route_command(self, command_text: str) -> tuple[bool, str]:
        """
        Tries to route command to registered plugins.
        Returns: (handled, response)
        """
        for plugin in self.plugins:
            if plugin.can_handle(command_text):
                try:
                    response = plugin.execute(command_text)
                    return True, response
                except Exception as e:
                    return True, f"Error running plugin '{plugin.name}': {e}"
        return False, ""

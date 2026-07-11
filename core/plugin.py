class BasePlugin:
    """Base class for all ESY plugins."""
    
    def __init__(self):
        self.name = "Base Plugin"
        self.description = "Base plugin template."
        self.keywords = []

    def can_handle(self, command_text: str) -> bool:
        """Determines if this plugin can handle the user's command."""
        cmd_lower = command_text.lower().strip()
        for kw in self.keywords:
            if kw in cmd_lower:
                return True
        return False

    def execute(self, command_text: str) -> str:
        """Executes the plugin command and returns a string response."""
        raise NotImplementedError("Plugins must implement the execute method.")

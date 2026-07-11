import sys
import time
import math
from pathlib import Path
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QProgressBar, QFrame
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QBrush

import config
import voice
import core.memory as memory
import core.brain as brain
from core.plugin_manager import PluginManager

# Ensure parent directory is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Initialize plugin manager
plugin_manager = PluginManager(config.BASE_DIR / "plugins")
plugin_manager.load_plugins()

class SoundwaveWidget(QWidget):
    """Custom QWidget that draws an animated cyberpunk soundwave/pulse."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase = 0.0
        self.amplitude = 10.0
        self.state = "IDLE"  # IDLE, LISTENING, PROCESSING, SPEAKING
        
        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(30) # ~33 FPS

    def set_state(self, state: str):
        self.state = state.upper()
        if self.state == "IDLE":
            self.amplitude = 5.0
        elif self.state == "LISTENING":
            self.amplitude = 25.0
        elif self.state == "PROCESSING":
            self.amplitude = 15.0
        elif self.state == "SPEAKING":
            self.amplitude = 35.0

    def update_wave(self):
        self.phase += 0.15
        if self.state == "PROCESSING":
            self.phase += 0.25 # faster rotation when thinking
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        mid_y = height / 2
        
        # Draw background line
        painter.setPen(QPen(QColor(10, 20, 35), 2))
        painter.drawLine(0, int(mid_y), width, int(mid_y))
        
        # Base colors depending on state
        if self.state == "LISTENING":
            color = QColor(0, 255, 102) # Green for listening
        elif self.state == "PROCESSING":
            color = QColor(255, 204, 0) # Yellow for processing
        elif self.state == "SPEAKING":
            color = QColor(0, 240, 255) # Cyan for speaking
        else:
            color = QColor(0, 102, 204) # Deep Blue for idle
            
        # Draw multiple sine waves overlapping for a richer visual
        waves = 3 if self.state != "IDLE" else 1
        for w in range(waves):
            painter.setPen(QPen(color, 2 - (w * 0.5)))
            
            points = []
            for x in range(0, width, 2):
                # Calculate sine wave with phase shift, scale, and windowing to taper at edges
                window = math.sin(math.pi * x / width) # 0 at edges, 1 at center
                freq = 0.05 + (w * 0.02)
                p_shift = self.phase + (w * 1.5)
                
                y = mid_y + math.sin(x * freq + p_shift) * self.amplitude * window
                points.append((x, y))
                
            # Draw lines connecting points
            for i in range(len(points) - 1):
                painter.drawLine(
                    int(points[i][0]), int(points[i][1]),
                    int(points[i+1][0]), int(points[i+1][1])
                )


class AssistantWorker(QThread):
    """Background worker that handles speech recognition, commands, and AI routing."""
    status_changed = pyqtSignal(str) # IDLE, LISTENING, PROCESSING, SPEAKING
    message_received = pyqtSignal(str, str) # sender, message
    command_input_signal = pyqtSignal(str) # used internally to run typed command

    def __init__(self):
        super().__init__()
        self.running = True
        self.pending_command = None

    def run_command_async(self, text: str):
        """Called by UI thread to submit typed text commands."""
        self.pending_command = text

    def run(self):
        # Startup notification
        self.message_received.emit("ESY", "System initialized. online and ready.")
        self.status_changed.emit("SPEAKING")
        voice.speak("ESY system initialized. Online and ready.")
        self.status_changed.emit("IDLE")
        
        while self.running:
            # Check if there is a pending typed command
            if self.pending_command is not None:
                command = self.pending_command
                self.pending_command = None
                self._process_command(command)
                continue
                
            # If voice mic is disabled, we just sleep and wait for typed commands
            if not voice.mic_enabled:
                self.msleep(100)
                continue
                
            # Listen for voice input
            self.status_changed.emit("LISTENING")
            raw_input = voice.listen()
            self.status_changed.emit("IDLE")
            
            if not raw_input:
                self.msleep(100)
                continue
                
            # Process voice command
            # Extract wake word
            from main import extract_command
            command = extract_command(raw_input)
            
            if not command:
                continue
                
            if command == "WAKE_WORD_ONLY":
                self.status_changed.emit("SPEAKING")
                self.message_received.emit("ESY", "Yes? I am listening.")
                voice.speak("Yes? I am listening.")
                self.status_changed.emit("LISTENING")
                
                command = voice.listen()
                self.status_changed.emit("IDLE")
                if not command:
                    self.status_changed.emit("SPEAKING")
                    voice.speak("Listening timed out.")
                    self.status_changed.emit("IDLE")
                    continue
            
            self._process_command(command)

    def _process_command(self, command: str):
        self.message_received.emit("You", command)
        self.status_changed.emit("PROCESSING")
        
        # 1. Route to plugins
        is_handled, response = plugin_manager.route_command(command)
        
        # 2. Route to old static commands if not handled
        if not is_handled:
            import commands
            is_local, should_continue, local_response = commands.parse_and_execute(command)
            if is_local:
                is_handled = True
                response = local_response
                
        # 3. Route to AI Brain if still not handled
        if not is_handled:
            response = brain.query_brain(command)
            
        # Deliver response
        self.message_received.emit("ESY", response)
        self.status_changed.emit("SPEAKING")
        voice.speak(response)
        self.status_changed.emit("IDLE")


class ESYDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESY HUD Dashboard v2.0")
        self.setMinimumSize(QSize(1000, 650))
        self.init_ui()
        
        # Start Worker Thread
        self.worker = AssistantWorker()
        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.message_received.connect(self.on_message_received)
        self.worker.start()
        
        # Start Metrics Timer (update every second)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1000)
        self.update_metrics()

    def init_ui(self):
        # Apply dark cyberpunk stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #050811;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Monospace', 'Courier New', monospace;
            }
            QLabel {
                font-weight: bold;
            }
            QLineEdit {
                background-color: #0b132b;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                padding: 8px 12px;
                color: #00f0ff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00ff66;
            }
            QPushButton {
                background-color: #0b132b;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                color: #00f0ff;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00f0ff;
                color: #050811;
            }
            QProgressBar {
                border: 1px solid #1c2541;
                border-radius: 3px;
                text-align: center;
                background-color: #0b132b;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0055ff, stop:1 #00f0ff);
            }
            QTextEdit {
                background-color: #070b19;
                border: 1px solid #1c2541;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)

        # Main Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ==========================================
        # LEFT PANEL: System Metrics Sidebar
        # ==========================================
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #070c1b;
                border: 1px solid #1b2a47;
                border-radius: 6px;
            }
            QLabel {
                border: none;
            }
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(12)
        
        # Title of Sidebar
        sidebar_title = QLabel("SYSTEM INTEL")
        sidebar_title.setStyleSheet("color: #00f0ff; font-size: 16px; letter-spacing: 2px;")
        sidebar_layout.addWidget(sidebar_title)
        
        # Decorative line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #1b2a47;")
        sidebar_layout.addWidget(line)

        # CPU Progress Bar
        self.cpu_label = QLabel("CPU: 0%")
        sidebar_layout.addWidget(self.cpu_label)
        self.cpu_bar = QProgressBar()
        sidebar_layout.addWidget(self.cpu_bar)

        # RAM Progress Bar
        self.ram_label = QLabel("RAM: 0%")
        sidebar_layout.addWidget(self.ram_label)
        self.ram_bar = QProgressBar()
        sidebar_layout.addWidget(self.ram_bar)

        # Disk Progress Bar
        self.disk_label = QLabel("DISK: 0%")
        sidebar_layout.addWidget(self.disk_label)
        self.disk_bar = QProgressBar()
        sidebar_layout.addWidget(self.disk_bar)

        # Battery Progress Bar
        self.bat_label = QLabel("BATTERY: N/A")
        sidebar_layout.addWidget(self.bat_label)
        self.bat_bar = QProgressBar()
        sidebar_layout.addWidget(self.bat_bar)
        
        sidebar_layout.addStretch()
        
        # Audio / Wake word indicators
        self.mic_status_label = QLabel(f"MIC STATUS : {'ACTIVE' if voice.mic_enabled else 'FALLBACK'}")
        self.mic_status_label.setStyleSheet("color: #00ff66;" if voice.mic_enabled else "color: #ff9900;")
        sidebar_layout.addWidget(self.mic_status_label)
        
        self.tts_status_label = QLabel(f"TTS OUTPUT : {'ACTIVE' if voice.tts_enabled else 'DISABLED'}")
        self.tts_status_label.setStyleSheet("color: #00ff66;" if voice.tts_enabled else "color: #ff3300;")
        sidebar_layout.addWidget(self.tts_status_label)
        
        main_layout.addWidget(sidebar)

        # ==========================================
        # RIGHT PANEL: Terminal Chat & Input
        # ==========================================
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # Cyberpunk ASCII Banner header
        self.header_label = QLabel("ESY A.I. SYSTEM v2.0 - ACTIVE HUD")
        self.header_label.setStyleSheet("color: #00f0ff; font-size: 14px; font-weight: bold;")
        right_panel.addWidget(self.header_label)

        # Console Chat Logger
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setHtml("""
            <div style='color: #00f0ff; font-weight: bold;'>[SYSTEM STARTUP]</div>
            <div style='color: #8892b0;'>Initializing ESY cognitive frameworks...</div>
        """)
        right_panel.addWidget(self.chat_display)

        # Custom Animated Soundwave Visualizer
        self.soundwave = SoundwaveWidget()
        self.soundwave.setFixedHeight(60)
        right_panel.addWidget(self.soundwave)

        # Input Area (Layout)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter command or query (e.g. show cpu load, search for python)...")
        self.input_field.returnPressed.connect(self.submit_command)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("EXECUTE")
        self.send_btn.clicked.connect(self.submit_command)
        input_layout.addWidget(self.send_btn)
        
        right_panel.addLayout(input_layout)
        
        main_layout.addLayout(right_panel)

    def update_metrics(self):
        """Fetch system statistics and update sidebar progress bars."""
        import psutil
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.cpu_label.setText(f"CPU LOAD: {cpu}%")
            self.cpu_bar.setValue(int(cpu))
            
            self.ram_label.setText(f"RAM UTILIZATION: {mem}%")
            self.ram_bar.setValue(int(mem))
            
            self.disk_label.setText(f"DISK USAGE: {disk}%")
            self.disk_bar.setValue(int(disk))
            
            bat = psutil.sensors_battery()
            if bat:
                self.bat_label.setText(f"BATTERY STATUS: {bat.percent}%")
                self.bat_bar.setValue(int(bat.percent))
            else:
                self.bat_label.setText("BATTERY STATUS: N/A")
                self.bat_bar.setValue(0)
        except Exception:
            pass

    def submit_command(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        
        # Submit command to worker thread asynchronously
        self.worker.run_command_async(text)

    def on_status_changed(self, state: str):
        self.soundwave.set_state(state)
        # Update header status
        self.header_label.setText(f"ESY A.I. SYSTEM v2.0 - [STATE: {state.upper()}]")

    def on_message_received(self, sender: str, message: str):
        # Format HTML bubbles
        current_html = self.chat_display.toHtml()
        
        # Clear some text if it gets too large
        if len(current_html) > 60000:
            current_html = current_html[-30000:]
            
        timestamp = time.strftime("%H:%M:%S")
        
        if sender == "You":
            new_msg = f"<div style='margin-bottom: 8px;'><span style='color: #00ff66;'>[{timestamp}] User:</span> <span style='color: #ffffff;'>{message}</span></div>"
        elif sender == "ESY":
            new_msg = f"<div style='margin-bottom: 8px;'><span style='color: #00f0ff;'>[{timestamp}] ESY:</span> <span style='color: #00f0ff; font-weight: 500;'>{message}</span></div>"
        else:
            new_msg = f"<div style='margin-bottom: 8px;'><span style='color: #ff3300;'>[{timestamp}] {sender}:</span> <span style='color: #ff9999;'>{message}</span></div>"
            
        self.chat_display.setHtml(current_html + new_msg)
        
        # Auto scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        # Clean shutdown of worker thread
        self.worker.running = False
        self.worker.quit()
        self.worker.wait()
        event.accept()

def run_gui():
    app = QApplication(sys.argv)
    dashboard = ESYDashboard()
    dashboard.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_gui()

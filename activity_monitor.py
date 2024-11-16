from pynput import mouse, keyboard
import pyautogui
import win32gui
import win32process
import psutil
import time


class ActivityMonitor:
    def __init__(self, config, database):
        self.config = config
        self.database = database
        self.last_activity = datetime.now()
        self.window_switches = []
        self.mouse_positions = []
        self.keyboard_events = []

    def start_monitoring(self):
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def on_mouse_move(self, x, y):
        current_time = datetime.now()
        self.mouse_positions.append((x, y, current_time))
        self.last_activity = current_time

        # Clean old positions
        self.mouse_positions = [pos for pos in self.mouse_positions
                                if (current_time - pos[2]).seconds < 3600]

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.database.log_activity("mouse_click", 0, f"x={x}, y={y}")

    def on_key_press(self, key):
        current_time = datetime.now()
        self.keyboard_events.append(current_time)
        self.last_activity = current_time

        # Clean old events
        self.keyboard_events = [evt for evt in self.keyboard_events
                                if (current_time - evt).seconds < 3600]

    def get_active_window_info(self):
        try:
            window = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
            return {
                'title': win32gui.GetWindowText(window),
                'process': process.name(),
                'start_time': process.create_time()
            }
        except:
            return None

    def analyze_activity(self):
        current_time = datetime.now()

        # Check for rapid window switching
        window_switches_last_minute = len([sw for sw in self.window_switches
                                           if (current_time - sw).seconds < 60])

        # Calculate typing speed
        recent_keys = len([evt for evt in self.keyboard_events
                           if (current_time - evt).seconds < 60])

        # Calculate mouse movement patterns
        if len(self.mouse_positions) >= 2:
            recent_positions = [pos for pos in self.mouse_positions
                                if (current_time - pos[2]).seconds < 60]
            total_distance = sum(distance.euclidean(p1[:2], p2[:2])
                                 for p1, p2 in zip(recent_positions, recent_positions[1:]))
        else:
            total_distance = 0

        return {
            'window_switches': window_switches_last_minute,
            'typing_speed': recent_keys,
            'mouse_movement': total_distance,
            'idle_time': (current_time - self.last_activity).seconds
        }
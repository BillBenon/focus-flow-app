import sys
import os
from datetime import datetime
import threading
import cv2
import win32gui
import win32con
import pystray
from PIL import Image
import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager


class WellnessMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WellnessMonitor"
    _svc_display_name_ = "Wellness Monitor Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        try:
            app = WellnessMonitorApp()
            app.run()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {str(e)}")


class WellnessMonitorApp:
    def __init__(self):
        self.config = Config()
        self.database = Database(self.config.stats_file)
        self.fatigue_detector = FatigueDetector(self.config)
        self.activity_monitor = ActivityMonitor(self.config, self.database)
        self.gui = None
        self.system_tray = None
        self.camera_release_event = threading.Event()

    def create_system_tray(self):
        image = Image.open("icon.ico")
        menu = pystray.Menu(
            pystray.MenuItem("Show Dashboard", self.show_dashboard),
            pystray.MenuItem("Pause Monitoring", self.toggle_monitoring),
            pystray.MenuItem("Exit", self.exit_app)
        )
        self.system_tray = pystray.Icon("WellnessMonitor", image, "Wellness Monitor", menu)

    def show_dashboard(self):
        if not self.gui:
            self.gui = WellnessMonitorGUI(self.config, self.database)
        self.gui.show()

    def toggle_monitoring(self):
        # Implementation for pausing/resuming monitoring
        pass

    def exit_app(self):
        self.running = False
        if self.system_tray:
            self.system_tray.stop()
        if self.gui:
            self.gui.root.quit()

    def check_camera_access(self):
        try:
            # Check if camera is being used by another application
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                if self.fatigue_detector.camera_in_use:
                    return

                # Show notification about camera being used
                if self.config.settings['camera_priority']:
                    self.show_camera_notification()
                    self.fatigue_detector.camera_in_use = True
                    self.camera_release_event.clear()
            else:
                if self.fatigue_detector.camera_in_use:
                    self.fatigue_detector.camera_in_use = False
                    self.camera_release_event.set()
                cap.release()
        except Exception as e:
            self.database.log_activity("camera_error", 0, str(e))

    def show_camera_notification(self):
        # Create popup window
        notification = tk.Tk()
        notification.withdraw()
        response = messagebox.askyesno(
            "Camera Access",
            "Another application is requesting camera access. Allow?"
        )
        if response:
            self.fatigue_detector.camera_in_use = True
            self.camera_release_event.clear()
        notification.destroy()

    def run(self):
        self.running = True
        self.create_system_tray()

        # Start monitoring threads
        activity_thread = threading.Thread(target=self.activity_monitor.start_monitoring)
        camera_thread = threading.Thread(target=self.monitor_camera)
        analysis_thread = threading.Thread(target=self.analyze_state)

        activity_thread.start()
        camera_thread.start()
        analysis_thread.start()

        # Start system tray
        self.system_tray.run()

    def monitor_camera(self):
        while self.running:
            if not self.fatigue_detector.camera_in_use:
                frame = self.get_camera_frame()
                if frame is not None:
                    blink_detected = self.fatigue_detector.detect_blink(frame)
                    yawn_detected = self.fatigue_detector.detect_yawn(frame)

                    if blink_detected or yawn_detected:
                        self.database.log_fatigue_event(
                            "blink" if blink_detected else "yawn",
                            1.0,
                            "detected"
                        )
            else:
                self.camera_release_event.wait(timeout=1.0)

    def analyze_state(self):
        while self.running:
            activity_data = self.activity_monitor.analyze_activity()

            # Check for fatigue indicators
            if self.should_suggest_break(activity_data):
                self.suggest_break(activity_data)

            time.sleep(1)

    def should_suggest_break(self, activity_data):
        return (
                activity_data['idle_time'] > self.config.settings['detection_settings']['idle_threshold'] or
                activity_data['window_switches'] > self.config.settings['detection_settings']['rapid_switch_threshold']
        )

    def suggest_break(self, activity_data):
        suggestion_type = self.determine_break_type(activity_data)
        self.show_break_notification(suggestion_type)

    def determine_break_type(self, activity_data):
        if activity_data['idle_time'] > 3600:  # 1 hour
            return 'long_break'
        elif activity_data['window_switches'] > 10:
            return 'focus_break'
        else:
            return 'short_break'

    def show_break_notification(self, break_type):
        suggestions = {
            'short_break': "Would you take a 5 minutes breath out of your computer, please!",
            'long_break': "You've been working for so long. Would you mind taking an hour nap and come back, please!",
            'focus_break': "Would you stand up and stretch so that you can focus, please!",
            'water_break': "Would you take a water break, please!"
        }

        if self.config.settings['notifications']['enable_popup']:
            notification = tk.Tk()
            notification.withdraw()
            messagebox.showinfo("Break Suggestion", suggestions[break_type])
            notification.destroy()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        app = WellnessMonitorApp()
        app.run()
    else:
        win32serviceutil.HandleCommandLine(WellnessMonitorService)
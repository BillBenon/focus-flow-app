import os
import json
from pathlib import Path


class Config:
    def __init__(self):
        self.app_data_dir = Path.home() / '.wellnessmonitor'
        self.config_file = self.app_data_dir / 'config.json'
        self.stats_file = self.app_data_dir / 'stats.db'

        self.default_settings = {
            'break_intervals': {
                'short_break': 1800,  # 30 minutes
                'long_break': 3600,  # 1 hour
                'water_break': 2700  # 45 minutes
            },
            'detection_settings': {
                'blink_threshold': 0.3,
                'yawn_threshold': 0.6,
                'idle_threshold': 300,
                'rapid_switch_threshold': 5
            },
            'notifications': {
                'enable_sound': True,
                'enable_popup': True
            },
            'camera_priority': True  # Give priority to external apps
        }

        self.create_app_directory()
        self.load_settings()

    def create_app_directory(self):
        self.app_data_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self.save_settings(self.default_settings)

    def load_settings(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = self.default_settings

    def save_settings(self, settings):
        with open(self.config_file, 'w') as f:
            json.dump(settings, f, indent=4)
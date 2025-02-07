# screenshot.py
from PIL import Image, ImageGrab
import os
import time
import io
import json
import pygetwindow as gw

WINDOW_CACHE_FILE = 'window_cache.json'

class WindowCapture:
    def __init__(self, logs_output_dir="./logs"):
        self.logs_output_dir = logs_output_dir
        self.cached_window = self.load_cached_window()  # Load on init

    def load_cached_window(self):
        """Load previously selected window title from cache"""
        try:
            with open(WINDOW_CACHE_FILE, 'r') as f:
                return json.load(f)['window_title']
        except Exception:
            return None

    def save_window_to_cache(self, window_title):
        """Save selected window title to cache"""
        with open(WINDOW_CACHE_FILE, 'w') as f:
            json.dump({'window_title': window_title}, f)

    def get_window_list(self):
        """Get list of all visible windows using pygetwindow"""
        try:
            windows = gw.getAllWindows()  # Returns list of Window objects
            result = []
            for win in windows:
                # Only include windows that have a non-empty title.
                if win.title:
                    result.append({
                        'title': win.title,
                        'owner': 'N/A',
                        'bounds': {
                            'X': win.left,
                            'Y': win.top,
                            'Width': win.width,
                            'Height': win.height
                        },
                        'id': win._hWnd  # Windows handle
                    })
            return result
        except Exception as e:
            print(f"Error in get_window_list: {e}")
            return []


    def capture_window(self, window_title):
        """
        Capture a specific window by title.
        The method searches for a window whose title contains the given text.
        """
        try:
            windows = self.get_window_list()
            if not windows:
                print("No windows found!")
                return None

            target_window = None
            # Allow selecting by index if a number is passed
            try:
                idx = int(window_title)
                if 0 <= idx < len(windows):
                    target_window = windows[idx]
            except ValueError:
                # Otherwise search by title (case-insensitive)
                for win in windows:
                    if window_title.lower() in win['title'].lower():
                        target_window = win
                        break

            if not target_window:
                print(f"No window found matching: {window_title}")
                return None

            self.save_window_to_cache(target_window['title'])

            bounds = target_window['bounds']
            left = bounds['X']
            top = bounds['Y']
            right = left + bounds['Width']
            bottom = top + bounds['Height']

            # Capture the region using PIL's ImageGrab
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
            return img

        except Exception as e:
            print(f"Error in capture_window: {e}")
            return None

    def capture_and_save(self, window_title):
        """
        Captures the window and saves the image to the logs directory.
        """
        img = self.capture_window(window_title)
        if img:
            os.makedirs(self.logs_output_dir, exist_ok=True)
            # Create a safe filename using only alphanumerics and a few symbols
            safe_title = ''.join(
                c for c in window_title if c.isalnum() or c in (' ', '-', '_')
            ).strip().replace(' ', '_')
            filename = f"{self.logs_output_dir}/{safe_title}_{int(time.time())}.png"
            img.save(filename)
            print(f"Screenshot saved as {filename}")
            return img
        else:
            return None

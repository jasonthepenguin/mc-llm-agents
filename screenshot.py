# screenshot.py
from PIL import Image
import os
import time
import io
# --- Quartz and Cocoa imports ---
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    kCGWindowBounds,
    kCGWindowName,
    kCGWindowOwnerName,
    kCGWindowNumber,
    kCGWindowListOptionIncludingWindow,
    CGWindowListCreateImage,
    CGRectMake,
    kCGWindowImageBoundsIgnoreFraming
)
import Cocoa
import json  # Import the json module
from PIL import ImageDraw, ImageFont

# --- Constants and Cache File ---
WINDOW_CACHE_FILE = 'window_cache.json'

class WindowCapture:
    def __init__(self, logs_output_dir="./logs"):
        self.logs_output_dir = logs_output_dir
        self.cached_window = self.load_cached_window() # Load on init

    def load_cached_window(self):
        """Load previously selected window title from cache"""
        try:
            with open(WINDOW_CACHE_FILE, 'r') as f:
                return json.load(f)['window_title']
        except:
            return None

    def save_window_to_cache(self, window_title):
        """Save selected window title to cache"""
        with open(WINDOW_CACHE_FILE, 'w') as f:
            json.dump({'window_title': window_title}, f)

    def get_window_list(self):
        """Get list of all windows (Quartz)"""
        try:
            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            windows = []
            for window in window_list:
                title = window.get(kCGWindowName, '')
                owner = window.get(kCGWindowOwnerName, '')
                if title:  # Only include windows with titles
                    windows.append({
                        'title': title,
                        'owner': owner,
                        'bounds': window.get(kCGWindowBounds, {}),
                        'id': window.get(kCGWindowNumber, 0)
                    })
            return windows
        except Exception as e:
            print(f"Error in get_window_list: {e}")  # Error handling
            return []

    def cgimage_to_png(self, cgimage):
        """Convert a CGImage to PNG data (Cocoa)"""
        try:
            bitmapRep = Cocoa.NSBitmapImageRep.alloc().initWithCGImage_(cgimage)
            png_data = bitmapRep.representationUsingType_properties_(Cocoa.NSPNGFileType, None)
            bytes_data = png_data.bytes().tobytes()
            return bytes_data
        except Exception as e:
            print(f"Error in cgimage_to_png: {e}") # Error handling
            return None

    def draw_center_line(self, img):
        """Draw a yellow horizontal line through the center of the image with numbered notches."""
        # Create a copy of the image to avoid modifying the original
        img_with_line = img.copy()
        draw = ImageDraw.Draw(img_with_line)
        
        # Calculate center coordinates
        center_x = img.width // 2
        center_y = img.height // 2
        
        # Draw main yellow line from left to right edge
        line_color = (255, 255, 0)  # Yellow color
        line_thickness = max(1, img.height // 100)  # Scale thickness with image height
        draw.line([(0, center_y), (img.width, center_y)], fill=line_color, width=line_thickness)
        
        # Calculate notch parameters
        notch_length = line_thickness * 3  # Length of notch marks
        small_notch_length = notch_length // 2  # Smaller notches for .5 increments
        spacing = img.width // 40  # Double the number of segments for .5 increments
        
        try:
            # Try to load Arial font with slightly larger size
            font = ImageFont.truetype("arial.ttf", size=max(12, line_thickness * 2.5))
        except:
            font = ImageFont.load_default()
        
        # Text position is now always above the line
        text_y = center_y - notch_length - 20
        
        # Draw notches and numbers
        for i in range(-20, 21):  # -20 to +20 for .5 increments
            x = center_x + (i * spacing)
            if x >= 0 and x <= img.width:  # Only draw if within image bounds
                # Determine if this is a whole number or .5 increment
                is_whole_number = i % 2 == 0
                current_value = i / 2 * 7.5  # Increased multiplier to make numbers larger per notch
                
                # Draw notch (full length for whole numbers, half length for .5)
                current_notch_length = notch_length if is_whole_number else small_notch_length
                draw.line([(x, center_y - current_notch_length), (x, center_y + current_notch_length)], 
                         fill=line_color, width=line_thickness)
                
                # Draw numbers at intervals of 15 (including -60, -45, -30, -15, 0, 15, 30, 45, 60)
                if is_whole_number and int(current_value) % 15 == 0:
                    text = str(int(current_value))  # Use actual value (including negative)
                    # Calculate text width for centering
                    text_width = font.getsize(text)[0] if hasattr(font, 'getsize') else 6
                    text_x = x - (text_width // 2)
                    
                    # Draw text in black without outline
                    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)
        
        return img_with_line

    def capture_window(self, window_title):
        """Capture a specific window by title (Quartz)"""
        try:
            windows = self.get_window_list()
            if not windows:
                print("No windows found!")
                return None

            window = None
            # Try to find window by index first (if a number is provided)
            try:
                idx = int(window_title)
                if 0 <= idx < len(windows):
                    window = windows[idx]
            except ValueError:
                # If not a number, search by title
                for win in windows:
                    if window_title.lower() in win['title'].lower():
                        window = win
                        break

            if not window:
                print(f"No window found matching: {window_title}")
                return None

            self.save_window_to_cache(window['title']) # Save to cache

            bounds = window['bounds']
            x, y = int(bounds['X']), int(bounds['Y'])
            width, height = int(bounds['Width']), int(bounds['Height'])
            rect = CGRectMake(x, y, width, height)
            windowid = window['id']

            # --- CRITICAL: This part is most likely to cause issues ---
            try:
                windowimg = CGWindowListCreateImage(
                    rect,
                    kCGWindowListOptionIncludingWindow,
                    windowid,
                    kCGWindowImageBoundsIgnoreFraming
                )
            except Exception as e:
                print(f"Error capturing window with Quartz: {e}")
                return None
            # --------------------------------------------------------

            if not windowimg:
                print("Failed to capture window")
                return None

            png_data = self.cgimage_to_png(windowimg)
            if not png_data:
                print("Failed to convert image to PNG")
                return None

            img = Image.open(io.BytesIO(png_data))
            img = self.draw_center_line(img)  # Add the center line
            return img

        except Exception as e:
            print(f"Error in capture_window: {e}")
            return None

    def capture_and_save(self, window_title):
        """Captures, saves, and returns the image."""
        img = self.capture_window(window_title)
        if img:
            os.makedirs(self.logs_output_dir, exist_ok=True)
            safe_title = ''.join(c for c in window_title if c.isalnum() or c in (' ', '-', '_'))
            filename = f'{self.logs_output_dir}/{safe_title}_{int(time.time())}.png'
            img.save(filename)
            print(f"Screenshot saved as {filename}")
            return img
        else:
            return None
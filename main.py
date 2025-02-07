import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab
import os
import platform
import time
import pyautogui
import datetime
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

# --- Constants and Cache File ---
WINDOW_CACHE_FILE = 'window_cache.json'

# --- Functions from screenshot.py, adapted for integration ---

def load_cached_window():
    """Load previously selected window title from cache"""
    try:
        with open(WINDOW_CACHE_FILE, 'r') as f:
            return json.load(f)['window_title']
    except:
        return None

def save_window_to_cache(window_title):
    """Save selected window title to cache"""
    with open(WINDOW_CACHE_FILE, 'w') as f:
        json.dump({'window_title': window_title}, f)

def get_window_list():
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

def cgimage_to_png(cgimage):
    """Convert a CGImage to PNG data (Cocoa)"""
    try:
        bitmapRep = Cocoa.NSBitmapImageRep.alloc().initWithCGImage_(cgimage)
        png_data = bitmapRep.representationUsingType_properties_(Cocoa.NSPNGFileType, None)
        bytes_data = png_data.bytes().tobytes()
        return bytes_data
    except Exception as e:
        print(f"Error in cgimage_to_png: {e}") # Error handling
        return None


def capture_window(window_title):
    """Capture a specific window by title (Quartz)"""
    try:
        windows = get_window_list()
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

        save_window_to_cache(window['title']) # Save to cache

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

        png_data = cgimage_to_png(windowimg)
        if not png_data:
            print("Failed to convert image to PNG")
            return None

        img = Image.open(io.BytesIO(png_data))
        return img

    except Exception as e:
        print(f"Error in capture_window: {e}")
        return None


# --- Tkinter GUI Code ---

root = tk.Tk()
root.title("FlowersBench MC Eval")
root.geometry("800x600")

# Load the logo image from PNG instead of SVG
try:
    logo_image_pil = Image.open("flowers.png")  # Change to your PNG file name
    # Resize the image to be smaller (adjust dimensions as needed)
    logo_image_pil = logo_image_pil.resize((140, 100), Image.Resampling.LANCZOS)  # Increased width to 120 while keeping height at 100
    logo_photo = ImageTk.PhotoImage(logo_image_pil)
except Exception as e:
    print("Error loading logo image:", e)
    logo_photo = None

# -------------------------
# Create Top Frame
# -------------------------
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=15)  # Increased overall padding

# Left: Logo image (top left)
if logo_photo:
    logo_label = tk.Label(top_frame, image=logo_photo)
    logo_label.grid(row=0, column=0, sticky="w")
else:
    logo_label = tk.Label(top_frame, text="Logo")
    logo_label.grid(row=0, column=0, sticky="w")

# Middle: Model Selector drop-down inline with label
model_frame = tk.Frame(top_frame)
model_frame.grid(row=0, column=1, sticky="e", padx=30)
model_label = tk.Label(model_frame, text="Model Selector:")
model_label.pack(side=tk.LEFT, padx=(0, 10))
model_options = ["Sonnet 3.5 (Anthropic)", "Gpt-4o (OpenAI)"]
model_var = tk.StringVar(value="Sonnet 3.5 (Anthropic)")  # Updated default value
model_combobox = ttk.Combobox(model_frame, textvariable=model_var, values=model_options, state="readonly", width=15)
model_combobox.pack(side=tk.LEFT)

# Right: Openrouter API key text field inline with label
api_frame = tk.Frame(top_frame)
api_frame.grid(row=0, column=2, sticky="e", padx=(0, 20))  # Added right padding
api_label = tk.Label(api_frame, text="Openrouter API key:")
api_label.pack(side=tk.LEFT, padx=(0, 10))  # Added padding between label and entry
api_key_var = tk.StringVar()
api_entry = tk.Entry(api_frame, textvariable=api_key_var, width=25, show="•")  # Added show parameter
api_entry.pack(side=tk.LEFT)

# Configure column weights for better distribution
top_frame.grid_columnconfigure(0, weight=1)  # Logo area
top_frame.grid_columnconfigure(1, weight=2)  # Model selector area
top_frame.grid_columnconfigure(2, weight=2)  # API key area

# -------------------------
# Create Center Frame (for screenshot display and action areas)
# -------------------------
center_frame = tk.Frame(root)
center_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

# Create left panel for actions
actions_frame = tk.Frame(center_frame, width=180)  # Made slightly narrower
actions_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
actions_frame.pack_propagate(False)  # Prevent frame from shrinking

# Current Action section
current_action_label = tk.Label(actions_frame, text="Current Action", font=('Arial', 12, 'bold'))
current_action_label.pack(anchor='w', pady=(0, 5))
current_action_text = tk.Text(actions_frame, height=3, width=20, wrap=tk.WORD, state='normal', font=('Arial', 14))
current_action_text.pack(fill=tk.X, pady=(0, 15))
current_action_text.tag_configure('red', foreground='red', justify='center')
current_action_text.tag_configure('center', justify='center')
current_action_text.config(state='disabled')

# Next Action section
next_action_label = tk.Label(actions_frame, text="Next Action", font=('Arial', 12, 'bold'))
next_action_label.pack(anchor='w', pady=(0, 5))
next_action_text = tk.Text(actions_frame, height=3, width=20, wrap=tk.WORD, state='normal', font=('Arial', 14))
next_action_text.pack(fill=tk.X, pady=(0, 15))
next_action_text.tag_configure('blue', foreground='blue', justify='center')
next_action_text.tag_configure('center', justify='center')
next_action_text.config(state='disabled')

# Action Log section
action_log_label = tk.Label(actions_frame, text="Action Log", font=('Arial', 12, 'bold'))
action_log_label.pack(anchor='w', pady=(0, 5))
action_log_text = tk.Text(actions_frame, height=8, width=20, wrap=tk.WORD, state='normal', font=('Arial', 11))
action_log_text.pack(fill=tk.X)
action_log_text.tag_configure('gray', foreground='gray')
action_log_text.config(state='disabled')

# Add example log entries
log_entries = [
    "Jump(forward)",
    "look(90, 0)",
    "move(3 blocks)",
    "interact()"
]

for entry in log_entries:
    action_log_text.insert(tk.END, f"{entry}\n", 'gray')
action_log_text.config(state='disabled')

# Add logs output directory selector
logs_output_frame = tk.Frame(actions_frame)
logs_output_frame.pack(fill=tk.X, pady=(10, 0))

logs_output_var = tk.StringVar(value="./logs")
logs_output_button = tk.Button(logs_output_frame, text="Select Logs Directory", command=lambda: browse_directory(logs_output_var))
logs_output_button.pack(fill=tk.X)

def browse_directory(var):
    from tkinter import filedialog
    directory = filedialog.askdirectory(initialdir=var.get())
    if directory:
        var.set(directory)

# --- Integrated Window Selection and Capture ---
selected_window_var = tk.StringVar()

def select_window():
    """Lists available windows and allows selection (integrated)."""
    windows = get_window_list()
    if not windows:
        tk.messagebox.showerror("Error", "No windows found!")
        return

    window_titles = [f"{win['owner']} - {win['title']}" for win in windows]

    popup = tk.Toplevel(root)
    popup.title("Select Window")

    if window_titles:
        selected_window_var.set(window_titles[0])
        window_menu = tk.OptionMenu(popup, selected_window_var, *window_titles)
        window_menu.pack(pady=10)
    else:
        tk.Label(popup, text="No windows found.").pack(pady=10)

    def confirm_selection():
        print(f"Selected window: {selected_window_var.get()}")
        # Extract just the title.  We stored "Owner - Title".
        selected_title = selected_window_var.get().split(" - ", 1)[1]  # Get part after " - "
        save_window_to_cache(selected_title) # Save the actual title
        popup.destroy()

    confirm_button = tk.Button(popup, text="Confirm", command=confirm_selection)
    confirm_button.pack()

def take_screenshot():
    """Captures and displays the screenshot (integrated)."""
    window_title = selected_window_var.get()
    if not window_title:
        tk.messagebox.showwarning("Warning", "No window selected.")
        return

    # Extract just the title.  We stored "Owner - Title".
    selected_title = window_title.split(" - ", 1)[1]

    img = capture_window(selected_title)
    if img:
        # --- File Saving ---
        os.makedirs(logs_output_var.get(), exist_ok=True)
        safe_title = ''.join(c for c in selected_title if c.isalnum() or c in (' ', '-', '_'))
        filename = f'{logs_output_var.get()}/{safe_title}_{int(time.time())}.png'
        img.save(filename)
        print(f"Screenshot saved as {filename}")
        # ------------------

        img = img.resize((580, 380), Image.Resampling.LANCZOS)
        screenshot_tk = ImageTk.PhotoImage(img)
        screenshot_canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_tk)
        screenshot_canvas.image = screenshot_tk  # Keep a reference!
    else:
        tk.messagebox.showerror("Error", "Failed to capture screenshot.")

# Create right panel for screenshot
screenshot_frame = tk.Frame(center_frame)
screenshot_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

# Create a canvas with a border that will act as the screenshot display area
screenshot_canvas = tk.Canvas(screenshot_frame, bg="white", borderwidth=2, relief="groove")
screenshot_canvas.pack(expand=True, fill=tk.BOTH)

# Add placeholder text
screenshot_canvas.create_text(300, 200, text="Screenshot display area", fill="gray")

# -------------------------
# Create Bottom Frame (for goal entry and Start button)
# -------------------------
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

# Create goal entry frame
goal_var = tk.StringVar(value="Enter goal for LLM to accomplish")
goal_entry = tk.Entry(bottom_frame, textvariable=goal_var)
goal_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

def start_action():
    # Placeholder function for now
    print("Starting action with:")
    print(f"Goal: {goal_var.get()}")
    print(f"Model: {model_var.get()}")
    print(f"API Key: {api_key_var.get()}")
    print(f"Log Directory: {logs_output_var.get()}")

    # Take a screenshot
    take_screenshot()

# Clear the placeholder text on focus
def on_entry_click(event):
    if goal_var.get() == "Enter goal for LLM to accomplish":
        goal_entry.delete(0, tk.END)

goal_entry.bind('<FocusIn>', on_entry_click)

# Create Start button
start_button = tk.Button(bottom_frame, text="Start", command=start_action)
start_button.pack(side=tk.RIGHT)

# Create Take Screenshot button
screenshot_button = tk.Button(bottom_frame, text="Take Screenshot", command=take_screenshot)
screenshot_button.pack(side=tk.RIGHT, padx=(0, 10))  # Add padding to separate from Start button

# --- Add Select Window Button ---
select_window_button = tk.Button(bottom_frame, text="Select Window", command=select_window)
select_window_button.pack(side=tk.RIGHT, padx=(0, 10))  # Add padding


# Start the main event loop
root.mainloop()

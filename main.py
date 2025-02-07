import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageGrab
import os
import platform
import time
import datetime
import io
# --- Import the new screenshot module ---
from screenshot import WindowCapture
# --- Import move.py ---
import MCPI_Scripts.move as move
# --- Import mcpi ---
import mcpi.minecraft
from tkinter import messagebox


# --- Tkinter GUI Code ---

root = tk.Tk()
root.title("FlowersBench MC Eval")
root.geometry("800x600")


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

# Middle: Model Selector drop-down, stacked layout
model_frame = tk.Frame(top_frame)
model_frame.grid(row=0, column=1, sticky="ew", padx=30)  # Use "ew" for horizontal expansion
model_label = tk.Label(model_frame, text="Model Selector:")
model_label.pack(side=tk.TOP, anchor="w")  # Align label to top-left
model_options = ["Sonnet 3.5 (Anthropic)", "Gpt-4o (OpenAI)"]
model_var = tk.StringVar(value="Sonnet 3.5 (Anthropic)")
model_combobox = ttk.Combobox(model_frame, textvariable=model_var, values=model_options, state="readonly", width=15)
model_combobox.pack(side=tk.TOP, anchor="w") # Align combobox to top-left

# Right: Openrouter API key text field, stacked layout
api_frame = tk.Frame(top_frame)
api_frame.grid(row=0, column=2, sticky="ew", padx=(0, 20))  # Use "ew", added left padding
api_label = tk.Label(api_frame, text="Openrouter API key:")
api_label.pack(side=tk.TOP, anchor="w") # Align label to top-left
api_key_var = tk.StringVar()
api_entry = tk.Entry(api_frame, textvariable=api_key_var, width=25, show="•")
api_entry.pack(side=tk.TOP, anchor="w")  # Align entry to top-left

# Max Turns field, stacked layout
max_turns_label = tk.Label(api_frame, text="Max Turns:")
max_turns_label.pack(side=tk.TOP, anchor="w")
max_turns_var = tk.IntVar(value=5)

def validate_max_turns(P):
    if P == "":
        return True
    try:
        value = int(P)
        if 0 <= value <= 50:
            return True  # Accept the change
        else:
            return False # Reject the change
    except ValueError:
        return False

max_turns_entry = tk.Entry(api_frame, textvariable=max_turns_var, width=5)
max_turns_entry.pack(side=tk.TOP, anchor="w")
vcmd = (max_turns_entry.register(validate_max_turns), '%P')
max_turns_entry.config(validate='key', validatecommand=vcmd)
max_turns_var.trace_add("write", lambda *args: None)

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

# --- Create a sub-frame for the action buttons ---
actions_button_frame = tk.Frame(logs_output_frame)
actions_button_frame.pack(fill=tk.X)  # Fill horizontally

# --- Add Move Button ---
def move_player():
    """Moves the player in Minecraft."""
    try:
        move.move_forward(mc, 10)
        take_screenshot()
    except Exception as e:
        messagebox.showerror("Error", f"Could not connect to Minecraft: {e}")

#move_button = tk.Button(actions_button_frame, text="Move", command=move_player, width=8)
#move_button.grid(row=0, column=0, padx=2, pady=2)

def open_action_panel():
    """Opens a popup for interacting with movement functions."""
    popup = tk.Toplevel(root)
    popup.title("Action Panel")

    # --- Move Forward ---
    tk.Label(popup, text="Move Forward").grid(row=0, column=0, sticky="w")
    distance_var = tk.IntVar(value=1)
    distance_entry = tk.Entry(popup, textvariable=distance_var, width=5)
    distance_entry.grid(row=0, column=1, padx=5)
    move_forward_button = tk.Button(popup, text="Go", command=lambda: move.move_forward(mc, distance_var.get()))
    move_forward_button.grid(row=0, column=2)

    # --- Look Left ---
    tk.Label(popup, text="Look Left (degrees)").grid(row=1, column=0, sticky="w")
    look_left_var = tk.IntVar(value=90)
    look_left_entry = tk.Entry(popup, textvariable=look_left_var, width=5)
    look_left_entry.grid(row=1, column=1, padx=5)
    look_left_button = tk.Button(popup, text="Go", command=lambda: move.look_left(mc, look_left_var.get()))
    look_left_button.grid(row=1, column=2)

    # --- Look Right ---
    tk.Label(popup, text="Look Right (degrees)").grid(row=2, column=0, sticky="w")
    look_right_var = tk.IntVar(value=90)
    look_right_entry = tk.Entry(popup, textvariable=look_right_var, width=5)
    look_right_entry.grid(row=2, column=1, padx=5)
    look_right_button = tk.Button(popup, text="Go", command=lambda: move.look_right(mc, look_right_var.get()))
    look_right_button.grid(row=2, column=2)

     # --- Look Up ---
    tk.Label(popup, text="Look Up (degrees)").grid(row=3, column=0, sticky="w")
    look_up_var = tk.IntVar(value=90)
    look_up_entry = tk.Entry(popup, textvariable=look_up_var, width=5)
    look_up_entry.grid(row=3, column=1, padx=5)
    look_up_button = tk.Button(popup, text="Go", command=lambda: move.look_up(mc, look_up_var.get()))
    look_up_button.grid(row=3, column=2)

     # --- Look Down ---
    tk.Label(popup, text="Look Down (degrees)").grid(row=4, column=0, sticky="w")
    look_down_var = tk.IntVar(value=90)
    look_down_entry = tk.Entry(popup, textvariable=look_down_var, width=5)
    look_down_entry.grid(row=4, column=1, padx=5)
    look_down_button = tk.Button(popup, text="Go", command=lambda: move.look_down(mc, look_down_var.get()))
    look_down_button.grid(row=4, column=2)



action_panel_button = tk.Button(actions_button_frame, text="Action Panel", command=open_action_panel, width=12)
action_panel_button.grid(row=0, column=0, padx=2, pady=2)

def browse_directory(var):
    from tkinter import filedialog
    directory = filedialog.askdirectory(initialdir=var.get())
    if directory:
        var.set(directory)

# --- Integrated Window Selection and Capture ---
# Use the class!
window_capture = WindowCapture(logs_output_var.get())  # Initialize
selected_window_var = tk.StringVar()

def select_window():
    windows = window_capture.get_window_list()  # Use class method
    if not windows:
        messagebox.showerror("Error", "No windows found!")
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
        # Extract the title (after " - ")
        selected_title = selected_window_var.get().split(" - ", 1)[1]
        window_capture.save_window_to_cache(selected_title)
        popup.destroy()

    confirm_button = tk.Button(popup, text="Confirm", command=confirm_selection)
    confirm_button.pack()

def take_screenshot():
    """Captures and displays the screenshot (integrated)."""
    window_title = selected_window_var.get()
    if not window_title:
        messagebox.showwarning("Warning", "No window selected.")
        return

    # Extract just the title.  We stored "Owner - Title".
    selected_title = window_title.split(" - ", 1)[1]

    # --- Use capture_and_save ---
    img = window_capture.capture_and_save(selected_title)
    if img:
        img = img.resize((580, 380), Image.Resampling.LANCZOS)
        screenshot_tk = ImageTk.PhotoImage(img)
        screenshot_canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_tk)
        screenshot_canvas.image = screenshot_tk  # Keep a reference!
    else:
        messagebox.showerror("Error", "Failed to capture screenshot.")

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
start_button.pack(side=tk.LEFT, padx=(0, 10))  # Moved to left, added padding

# --- Add Select Window Button ---
select_window_button = tk.Button(bottom_frame, text="Select Window", command=select_window)
select_window_button.pack(side=tk.RIGHT, padx=(0, 10))  # Add padding

# --- Update logs_output_dir when changed ---
def update_logs_output_dir(*args):
    window_capture.logs_output_dir = logs_output_var.get()

logs_output_var.trace_add("write", update_logs_output_dir)

# --- Create Minecraft Connection ---
try:
    mc = mcpi.minecraft.Minecraft.create()
    mc.postToChat("Connected to Minecraft")
except Exception as e:
    messagebox.showerror("Error", f"Could not connect to Minecraft: {e}")
    mc = None  # Set mc to None if connection fails

# Start the main event loop
root.mainloop()

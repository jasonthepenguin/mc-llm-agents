import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Create main window
root = tk.Tk()
root.title("LLM Benchmark GUI")
root.geometry("800x600")  # Adjust window size as needed

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
api_entry = tk.Entry(api_frame, textvariable=api_key_var, width=25)  # Set fixed width
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
current_action_text = tk.Text(actions_frame, height=3, width=20, wrap=tk.WORD, state='normal', font=('Arial', 14))  # Increased font size
current_action_text.pack(fill=tk.X, pady=(0, 15))
current_action_text.tag_configure('red', foreground='red', justify='center')
current_action_text.tag_configure('center', justify='center')
current_action_text.insert('1.0', "\n", 'center')
current_action_text.insert('2.0', "move(5 blocks)", ('red', 'center'))
current_action_text.config(state='disabled')

# Next Action section
next_action_label = tk.Label(actions_frame, text="Next Action", font=('Arial', 12, 'bold'))
next_action_label.pack(anchor='w', pady=(0, 5))
next_action_text = tk.Text(actions_frame, height=3, width=20, wrap=tk.WORD, state='normal', font=('Arial', 14))  # Increased font size
next_action_text.pack(fill=tk.X, pady=(0, 15))
next_action_text.tag_configure('blue', foreground='blue', justify='center')
next_action_text.tag_configure('center', justify='center')
next_action_text.insert('1.0', "\n", 'center')
next_action_text.insert('2.0', "interact()", ('blue', 'center'))
next_action_text.config(state='disabled')

# Action Log section
action_log_label = tk.Label(actions_frame, text="Action Log", font=('Arial', 12, 'bold'))
action_log_label.pack(anchor='w', pady=(0, 5))
action_log_text = tk.Text(actions_frame, height=8, width=20, wrap=tk.WORD, state='normal', font=('Arial', 11))
action_log_text.pack(fill=tk.X)
action_log_text.tag_configure('gray', foreground='gray')

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

# Create right panel for screenshot
screenshot_frame = tk.Frame(center_frame)
screenshot_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

# Create a canvas with a border that will act as the screenshot display area
screenshot_canvas = tk.Canvas(screenshot_frame, bg="white", borderwidth=2, relief="groove")
screenshot_canvas.pack(expand=True, fill=tk.BOTH)

# Optionally, add placeholder text inside the canvas
screenshot_canvas.create_text(300, 200, text="Screenshot Display Area", fill="gray")

# -------------------------
# Create Bottom Frame (for goal entry and Start button)
# -------------------------
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# Create Entry widget prepopulated with prompt
goal_var = tk.StringVar(value="Enter goal for LLM to accomplish")
goal_entry = tk.Entry(bottom_frame, textvariable=goal_var, width=50)
goal_entry.grid(row=0, column=0, padx=5)

# Clear the placeholder text on focus if it hasn't been changed yet.
def on_entry_click(event):
    if goal_var.get() == "Enter goal for LLM to accomplish":
        goal_entry.delete(0, tk.END)

goal_entry.bind('<FocusIn>', on_entry_click)

# Create Start button to the right of the goal entry
def start_action():
    # For now, simply print the entered goal
    print("Start clicked. Goal:", goal_var.get())

start_button = tk.Button(bottom_frame, text="Start", command=start_action)
start_button.grid(row=0, column=1, padx=0)

# Optional: Allow the goal entry column to expand
bottom_frame.grid_columnconfigure(0, weight=1)

# Start the main event loop
root.mainloop()

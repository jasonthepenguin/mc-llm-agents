import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk, ImageGrab, Image
import os
import platform
import time
import datetime
import io
import base64
import threading
import json

# --- Import OpenRouter/OpenAI client ---
from openai import OpenAI, APIError

# --- Import the new screenshot module ---
from screenshot import WindowCapture
# --- Import move.py ---
import MCPI_Scripts.move as move
# --- Import door module ---
from MCPI_Scripts.door import check_for_door  # This should now just import the function without executing it
from MCPI_Scripts.move import mc_socket

# Global variable to store the most recent screenshot (PIL Image)
current_screenshot = None

def center_window(window):
    """Center a tkinter window on the screen"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f'{width}x{height}+{x}+{y}')

# -------------------------
# Main GUI (top, center & bottom frames)
# -------------------------
root = tk.Tk()
root.title("FlowersBench MC Eval")
root.withdraw()  # Hide the window initially
root.geometry("800x600")
center_window(root)
root.deiconify()  # Show the window in its final position

try:
    logo_image_pil = Image.open("flowers.png")  # Change to your PNG file name
    # Resize the image
    logo_image_pil = logo_image_pil.resize((140, 100), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image_pil)
except Exception as e:
    print("Error loading logo image:", e)
    logo_photo = None

# -------------------------
# Create Top Frame
# -------------------------
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=15)

# Left: Logo image
if logo_photo:
    logo_label = tk.Label(top_frame, image=logo_photo)
    logo_label.grid(row=0, column=0, sticky="w")
else:
    logo_label = tk.Label(top_frame, text="Logo")
    logo_label.grid(row=0, column=0, sticky="w")

# Middle: Model Selector drop-down (using models from openrouter.py)
model_frame = tk.Frame(top_frame)
model_frame.grid(row=0, column=1, sticky="ew", padx=30)
model_label = tk.Label(model_frame, text="Model Selector:")
model_label.pack(side=tk.TOP, anchor="w")
model_options = [
    "openai/chatgpt-4o-latest",  
    "openai/gpt-4o-mini", 
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.0-pro-exp-02-05:free"
]
model_var = tk.StringVar(value="openai/chatgpt-4o-latest")
model_combobox = ttk.Combobox(model_frame, textvariable=model_var, values=model_options, state="readonly", width=25)
model_combobox.pack(side=tk.TOP, anchor="w")

# Right: Openrouter API key text field
api_frame = tk.Frame(top_frame)
api_frame.grid(row=0, column=2, sticky="ew", padx=(0, 20))
api_label = tk.Label(api_frame, text="Openrouter API key:")
api_label.pack(side=tk.TOP, anchor="w")
api_key_var = tk.StringVar()
api_entry = tk.Entry(api_frame, textvariable=api_key_var, width=25, show="•")
api_entry.pack(side=tk.TOP, anchor="w")

# Max Turns field
max_turns_label = tk.Label(api_frame, text="Max Turns:")
max_turns_label.pack(side=tk.TOP, anchor="w")
max_turns_var = tk.IntVar(value=5)

def validate_max_turns(P):
    if P == "":
        return True
    try:
        value = int(P)
        if 0 <= value <= 50:
            return True
        else:
            return False
    except ValueError:
        return False

max_turns_entry = tk.Entry(api_frame, textvariable=max_turns_var, width=5)
max_turns_entry.pack(side=tk.TOP, anchor="w")
vcmd = (max_turns_entry.register(validate_max_turns), '%P')
max_turns_entry.config(validate='key', validatecommand=vcmd)
max_turns_var.trace_add("write", lambda *args: None)

# Configure column weights
top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_columnconfigure(1, weight=2)
top_frame.grid_columnconfigure(2, weight=2)

# -------------------------
# Create Center Frame (for screenshot display and actions)
# -------------------------
center_frame = tk.Frame(root)
center_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)

# Left panel for actions
actions_frame = tk.Frame(center_frame, width=180)
actions_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
actions_frame.pack_propagate(False)

current_action_label = tk.Label(actions_frame, text="Current Action", font=('Arial', 12, 'bold'))
current_action_label.pack(anchor='w', pady=(0, 5))
current_action_text = tk.Text(actions_frame, height=3, width=20, wrap=tk.WORD, font=('Arial', 14))
current_action_text.pack(fill=tk.X, pady=(0, 15))
current_action_text.tag_configure('red', foreground='red', justify='center')
current_action_text.config(state='disabled')

next_action_label = tk.Label(actions_frame, text="Next Action", font=('Arial', 12, 'bold'))
next_action_label.pack(anchor='w', pady=(0, 5))
next_action_text = tk.Text(actions_frame, height=3, width=20, wrap=tk.WORD, font=('Arial', 14))
next_action_text.pack(fill=tk.X, pady=(0, 15))
next_action_text.tag_configure('blue', foreground='blue', justify='center')
next_action_text.config(state='disabled')

action_log_label = tk.Label(actions_frame, text="Action Log", font=('Arial', 12, 'bold'))
action_log_label.pack(anchor='w', pady=(0, 5))
action_log_text = tk.Text(actions_frame, height=8, width=20, wrap=tk.WORD, font=('Arial', 11))
action_log_text.pack(fill=tk.X)
action_log_text.tag_configure('gray', foreground='gray')
action_log_text.config(state='disabled')

logs_output_frame = tk.Frame(actions_frame)
logs_output_frame.pack(fill=tk.X, pady=(10, 0))
logs_output_var = tk.StringVar(value="./logs")
logs_output_button = tk.Button(logs_output_frame, text="Select Logs Directory", command=lambda: browse_directory(logs_output_var))
logs_output_button.pack(fill=tk.X)

# Action Panel button (unchanged)
def open_action_panel():
    popup = tk.Toplevel(root)
    popup.title("Action Panel")
    popup.geometry("400x350")  # Made taller to accommodate new field
    
    # Add padding and spacing
    padding = {'padx': 10, 'pady': 5}
    
    tk.Label(popup, text="Move Forward").grid(row=0, column=0, sticky="w", **padding)
    distance_var = tk.IntVar(value=1)
    distance_entry = tk.Entry(popup, textvariable=distance_var, width=5)
    distance_entry.grid(row=0, column=1, padx=5)
    move_forward_button = tk.Button(popup, text="Go", command=lambda: move.move_forward(distance_var.get()))
    move_forward_button.grid(row=0, column=2)

    tk.Label(popup, text="Look Left (degrees)").grid(row=1, column=0, sticky="w", **padding)
    look_left_var = tk.IntVar(value=90)
    look_left_entry = tk.Entry(popup, textvariable=look_left_var, width=5)
    look_left_entry.grid(row=1, column=1, padx=5)
    look_left_button = tk.Button(popup, text="Go", command=lambda: move.look_left(look_left_var.get()))
    look_left_button.grid(row=1, column=2)

    tk.Label(popup, text="Look Right (degrees)").grid(row=2, column=0, sticky="w", **padding)
    look_right_var = tk.IntVar(value=90)
    look_right_entry = tk.Entry(popup, textvariable=look_right_var, width=5)
    look_right_entry.grid(row=2, column=1, padx=5)
    look_right_button = tk.Button(popup, text="Go", command=lambda: move.look_right(look_right_var.get()))
    look_right_button.grid(row=2, column=2)

    tk.Label(popup, text="Look Up (degrees)").grid(row=3, column=0, sticky="w", **padding)
    look_up_var = tk.IntVar(value=90)
    look_up_entry = tk.Entry(popup, textvariable=look_up_var, width=5)
    look_up_entry.grid(row=3, column=1, padx=5)
    look_up_button = tk.Button(popup, text="Go", command=lambda: move.look_up(look_up_var.get()))
    look_up_button.grid(row=3, column=2)

    tk.Label(popup, text="Look Down (degrees)").grid(row=4, column=0, sticky="w", **padding)
    look_down_var = tk.IntVar(value=90)
    look_down_entry = tk.Entry(popup, textvariable=look_down_var, width=5)
    look_down_entry.grid(row=4, column=1, padx=5)
    look_down_button = tk.Button(popup, text="Go", command=lambda: move.look_down(look_down_var.get()))
    look_down_button.grid(row=4, column=2)

    # Add Center View button (after the Look Down section)
    tk.Label(popup, text="Center View").grid(row=5, column=0, sticky="w", **padding)
    center_view_button = tk.Button(popup, text="Go", command=lambda: move.center_view())
    center_view_button.grid(row=5, column=2)

    # Move Open Door button to row 6
    tk.Label(popup, text="Open Door").grid(row=6, column=0, sticky="w", **padding)
    open_door_button = tk.Button(popup, text="Go", command=lambda: check_for_door())
    open_door_button.grid(row=6, column=2)

    # Add Message section (after the other controls)
    tk.Label(popup, text="Send Message").grid(row=7, column=0, sticky="w", **padding)
    message_var = tk.StringVar()
    message_entry = tk.Entry(popup, textvariable=message_var, width=20)
    message_entry.grid(row=7, column=1, padx=5)
    message_button = tk.Button(popup, text="Send", command=lambda: move.post_to_chat(message_var.get()))
    message_button.grid(row=7, column=2)

    # Configure column weights to make the window more responsive
    popup.grid_columnconfigure(0, weight=1)
    popup.grid_columnconfigure(1, weight=1)
    popup.grid_columnconfigure(2, weight=1)

# Add action panel button beneath logs button
action_panel_button = tk.Button(logs_output_frame, text="Action Panel", command=open_action_panel)
action_panel_button.pack(fill=tk.X, pady=(5, 0))

actions_button_frame = tk.Frame(logs_output_frame)
actions_button_frame.pack(fill=tk.X)

def browse_directory(var):
    from tkinter import filedialog
    directory = filedialog.askdirectory(initialdir=var.get())
    if directory:
        var.set(directory)

# --- Integrated Window Selection and Capture (for screenshots) ---
window_capture = WindowCapture(logs_output_var.get())
selected_window_var = tk.StringVar()

def select_window():
    windows = window_capture.get_window_list()
    if not windows:
        messagebox.showerror("Error", "No windows found!")
        return
    window_titles = [f"{win['owner']} - {win['title']}" for win in windows]
    popup = tk.Toplevel(root)
    popup.title("Select Window")
    popup.geometry("300x150")
    center_window(popup)
    if window_titles:
        selected_window_var.set(window_titles[0])
        window_menu = tk.OptionMenu(popup, selected_window_var, *window_titles)
        window_menu.pack(pady=10)
    else:
        tk.Label(popup, text="No windows found.").pack(pady=10)
    def confirm_selection():
        print(f"Selected window: {selected_window_var.get()}")
        selected_title = selected_window_var.get().split(" - ", 1)[1]
        window_capture.save_window_to_cache(selected_title)
        popup.destroy()
    confirm_button = tk.Button(popup, text="Confirm", command=confirm_selection)
    confirm_button.pack()

def take_screenshot():
    """Capture the screenshot using the selected window and display it in the main GUI.
       Also store the PIL image globally (so the chat window can use it)."""
    window_title = selected_window_var.get()
    if not window_title:
        messagebox.showwarning("Warning", "No window selected.")
        return
    selected_title = window_title.split(" - ", 1)[1]
    img = window_capture.capture_and_save(selected_title)
    if img:
        # For display on the main GUI, resize the image (if desired)
        display_img = img.resize((580, 380), Image.Resampling.LANCZOS)
        screenshot_tk = ImageTk.PhotoImage(display_img)
        screenshot_canvas.create_image(0, 0, anchor=tk.NW, image=screenshot_tk)
        screenshot_canvas.image = screenshot_tk
        global current_screenshot
        current_screenshot = img  # store the PIL screenshot for use in the ChatWindow
    else:
        messagebox.showerror("Error", "Failed to capture screenshot.")

# Create right panel for screenshot display
screenshot_frame = tk.Frame(center_frame)
screenshot_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

screenshot_canvas = tk.Canvas(screenshot_frame, bg="white", borderwidth=2, relief="groove")
screenshot_canvas.pack(expand=True, fill=tk.BOTH)
screenshot_canvas.create_text(300, 200, text="Screenshot display area", fill="gray")

# -------------------------
# Create Bottom Frame (for goal entry and Start button)
# -------------------------
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

def start_action():
    # Use the API key and model from the GUI, and pass the shared window/screenshot values to the chat window.
    provided_api_key = api_key_var.get().strip()
    if not provided_api_key:
        messagebox.showwarning("Warning", "Please provide an Openrouter API key.")
        return
    print("Starting action with:")
    print(f"Model: {model_var.get()}")
    print(f"API Key: {api_key_var.get()}")
    print(f"Log Directory: {logs_output_var.get()}")
    # Retrieve the selected window title from the main GUI (if any)
    selected_title = None
    if selected_window_var.get():
        selected_title = selected_window_var.get().split(" - ", 1)[1]
    chat_top = tk.Toplevel(root)
    chat_top.title("OpenRouter Chat")
    chat_top.geometry("800x600")
    # Pass the shared window_capture, selected window title and current screenshot to the ChatWindow.
    ChatWindow(chat_top, provided_api_key, model=model_var.get(), 
               window_capture=window_capture, 
               selected_window_title=selected_title,
               initial_screenshot=current_screenshot)

start_button = tk.Button(bottom_frame, text="Start", command=start_action)
start_button.pack(side=tk.LEFT, padx=(0, 10))
# Remove screenshot button from main GUI
select_window_button = tk.Button(bottom_frame, text="Select Window", command=select_window)
select_window_button.pack(side=tk.RIGHT, padx=(0, 10))

# --- Update logs_output_dir when changed ---
def update_logs_output_dir(*args):
    window_capture.logs_output_dir = logs_output_var.get()
logs_output_var.trace_add("write", update_logs_output_dir)

# --- Create Minecraft Connection ---
try:
    mc = None  # We'll pass this as a dummy parameter since our functions expect it
    mc_socket.send_command("chat", {"message": "Connected to Minecraft"})
except Exception as e:
    messagebox.showerror("Error", f"Could not connect to Minecraft: {e}")
    mc = None

# ----------------------------------------------------------------
# Helper function for image encoding (used in ChatWindow)
def encode_image_to_base64(image):
    """Encodes a PIL Image object to base64."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

# ----------------------------------------------------------------
# ChatWindow class (integrated chat functionality from openrouter.py)
class ChatWindow:
    # Class variable for system prompt
    SYSTEM_PROMPT = """You are a Minecraft assistant. When you want to execute an action, 
    output it in the following format (only one command at a time):
    <<COMMAND>>
    action_name(parameter)
    <<END>>

    Available commands:
    - move_forward(distance)
    - look_left(degrees)
    - look_right(degrees)
    - look_up(degrees)
    - look_down(degrees)
    - open_door()

    Important: 
    - Only issue one command at a time. Wait for feedback before issuing another command.
    - When making degree adjustments, always compare the current viewpoint's centered position to the target's position.
    - Always reassess the current view position when a new screenshot is provided, as it indicates a change in perspective, as the degrees on the axis are relative to the new screenshot.

    Always provide a reason for the action, then output the command in the specified format.
    Example:
    I'll move forward 10 blocks to reach the house.
    <<COMMAND>>
    move_forward(10)
    <<END>>
    """

    def __init__(self, master, api_key, model, window_capture, selected_window_title, initial_screenshot=None):
        self.master = master
        self.api_key = api_key
        self.model_name = model
        # Add references to the main GUI variables
        self.model_var = model_var  # Add reference to model_var
        self.selected_window_var = selected_window_var  # Add reference to selected_window_var
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=os.environ.get("OPENROUTER_BASE_URL")
        )
        
        # Initialize messages with system prompt using class variable
        self.messages = [{
            "role": "system",
            "content": self.SYSTEM_PROMPT  # Using the class variable here
        }]
        # Use the shared WindowCapture and selected window title passed from main GUI.
        self.window_capture = window_capture
        self.selected_window_title = selected_window_title
        
        # Use the shared screenshot if provided
        self.screenshot_history = []
        self.screenshot_image = initial_screenshot  if initial_screenshot is not None else None
        self.screenshot_tk = None

        # Add reference to main GUI's screenshot canvas
        self.main_screenshot_canvas = screenshot_canvas

        # --- UI Elements ---
        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled', height=15, width=60)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_display.tag_configure('user', foreground='blue', font=('TkDefaultFont', 14))
        self.chat_display.tag_configure('assistant', foreground='green', font=('TkDefaultFont', 14))
        self.chat_display.tag_configure('center', justify='center')
        self.chat_display.configure(font=('TkDefaultFont', 14))
        
        # Message Entry
        self.message_entry = ttk.Entry(master, width=60, font=('TkDefaultFont', 12))
        self.message_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.message_entry.bind("<Return>", self.send_message)
        
        # Button Frame
        button_frame = tk.Frame(master)
        button_frame.pack(pady=(0,10))
        self.send_button = ttk.Button(button_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)
        self.screenshot_button = ttk.Button(button_frame, text="Capture Screenshot", command=self.capture_and_display_screenshot)
        self.screenshot_button.pack(side=tk.LEFT, padx=5)
        self.clear_chat_button = ttk.Button(button_frame, text="Clear Chat", command=self.clear_chat)
        self.clear_chat_button.pack(side=tk.LEFT, padx=5)
        
        # Loading indicator
        self.loading_label = tk.Label(master, text="")
        self.loading_label.pack()
        
        # Display the selected model - store the label as instance variable
        self.model_label = tk.Label(master, text=f"Model: {self.model_name}", font=('TkDefaultFont', 10, 'italic'))
        self.model_label.pack(pady=(0,5))
        
        # Add logo at bottom right
        try:
            logo_img = Image.open("flowers.png")
            logo_img = logo_img.resize((140, 100), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(logo_img)
            logo_frame = tk.Frame(master)
            logo_frame.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)
            logo_label = tk.Label(logo_frame, image=self.logo_tk)
            logo_label.pack()
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Add trace to model_var to update when changed
        self.model_var.trace_add("write", self.update_model)
        # Add trace to selected_window_var to update when changed
        self.selected_window_var.trace_add("write", self.update_selected_window)
    
    def update_model(self, *args):
        """Update the model when changed in main GUI"""
        self.model_name = self.model_var.get()
        # Now this will work since model_label is an instance variable
        self.model_label.config(text=f"Model: {self.model_name}")

    def update_selected_window(self, *args):
        """Update the selected window when changed in main GUI"""
        if self.selected_window_var.get():
            self.selected_window_title = self.selected_window_var.get().split(" - ", 1)[1]
            self.add_message("System", "Window selection updated.")

    def capture_and_display_screenshot(self):
        # Remove the initial check for selected_window_title
        # Instead, get the current selection from selected_window_var
        if not self.selected_window_var.get():
            messagebox.showerror("Error", "No window selected. Please select a window from the main interface.")
            return
        
        selected_title = self.selected_window_var.get().split(" - ", 1)[1]
        img = self.window_capture.capture_and_save(selected_title)
        
        if img:
            # Store the original image
            self.screenshot_image = img
            global current_screenshot
            current_screenshot = img

            # Create thumbnail for chat window
            max_width = 300
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            chat_thumbnail = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            self.screenshot_tk = ImageTk.PhotoImage(chat_thumbnail)

            # Create display version for main GUI
            display_img = img.resize((580, 380), Image.Resampling.LANCZOS)
            main_screenshot_tk = ImageTk.PhotoImage(display_img)
            self.main_screenshot_canvas.create_image(0, 0, anchor=tk.NW, image=main_screenshot_tk)
            self.main_screenshot_canvas.image = main_screenshot_tk

            self.add_message("System", "Screenshot captured and ready to attach.")
        else:
            messagebox.showerror("Error", "Failed to capture screenshot.")
    
    def add_message(self, role, content, tag=None):
        self.chat_display.config(state='normal')
        if tag:
            self.chat_display.insert(tk.END, f"{role}: {content}\n", tag)
        else:
            self.chat_display.insert(tk.END, f"{role}: {content}\n")
        if role == "You" and self.screenshot_image:
            thumbnail_size = (200, 150)
            thumbnail = self.screenshot_image.copy()
            thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(thumbnail)
            self.screenshot_history.append(photo)
            self.chat_display.insert(tk.END, '\n', 'center')
            self.chat_display.image_create(tk.END, image=photo)
            self.chat_display.insert(tk.END, '\n\n', 'center')
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
    
    def show_loading(self, show=True):
        if show:
            self.loading_label.config(text="Sending message...")
            self.send_button.config(state='disabled')
            self.message_entry.config(state='disabled')
        else:
            self.loading_label.config(text="")
            self.send_button.config(state='normal')
            self.message_entry.config(state='normal')
    
    def chat_with_model(self, messages):
        try:
            # Add debug logging
            print(f"Sending message to {self.model_name}")
            print(f"Number of messages in context: {len(messages)}")
            print(f"Latest message type: {type(messages[-1]['content'])}")
            
            chat_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                top_p=1,
                seed=12345,
                user="my-test-user",
            )
            
            if not chat_completion or not chat_completion.choices:
                print("Debug: Received empty response from API")
                print(f"Full API response: {chat_completion}")
                raise Exception("No response received from the API")
            
            response = chat_completion.choices[0].message.content
            return response
        except APIError as e:
            print(f"API Error details: {str(e)}")
            messagebox.showerror("API Error", f"OpenAI API Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error details: {str(e)}")
            print(f"Last message content: {messages[-1]['content'] if messages else 'No messages'}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            return None
    
    def send_message_thread(self, user_input, message_content):
        self.messages.append({"role": "user", "content": message_content})
        try:
            response = self.chat_with_model(self.messages)
            self.master.after(0, lambda: self.handle_response(response))
        finally:
            self.master.after(0, lambda: self.show_loading(False))
    
    def handle_response(self, response):
        if response:
            self.add_message("Model", response, 'assistant')
            self.messages.append({"role": "assistant", "content": response})
            # Try to execute any commands in the response
            execute_command(response)
    
    def clear_chat(self):
        self.messages = [{
            "role": "system",
            "content": self.SYSTEM_PROMPT
        }]
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
        self.screenshot_image = None
        self.screenshot_tk = None
        self.screenshot_history = []
    
    def send_message(self, event=None):
        user_input = self.message_entry.get()
        if not user_input:
            return
        self.add_message("You", user_input, 'user')
        self.message_entry.delete(0, tk.END)
        message_content = [{"type": "text", "text": user_input}]
        # If a screenshot is available, attach it without clearing it.
        if self.screenshot_image:
            base64_image = encode_image_to_base64(self.screenshot_image)
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        self.show_loading(True)
        thread = threading.Thread(
            target=self.send_message_thread,
            args=(user_input, message_content),
            daemon=True
        )
        thread.start()

def execute_command(command_str):
    """Execute a command from the LLM."""
    try:
        # Extract command between markers
        if "<<COMMAND>>" not in command_str or "<<END>>" not in command_str:
            return False
            
        command = command_str.split("<<COMMAND>>")[1].split("<<END>>")[0].strip()
        
        # Parse the command
        parts = command.split("(")
        if len(parts) != 2:
            return False
            
        action = parts[0].strip()
        args = [arg.strip() for arg in parts[1].rstrip(")").split(",")]
        
        # Execute the appropriate function
        if action == "move_forward":
            move.move_forward(mc, int(args[0]))
        elif action == "look_left":
            move.look_left(mc, int(args[0]))
        elif action == "look_right":
            move.look_right(mc, int(args[0]))
        elif action == "look_up":
            move.look_up(mc, int(args[0]))
        elif action == "look_down":
            move.look_down(mc, int(args[0]))
        elif action == "open_door":
            check_for_door(mc)  # Pass the mc connection
        return True
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

# ----------------------------------------------------------------
# Start the main event loop
root.mainloop()
import os
import base64
import io
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from openai import OpenAI, APIError
from dotenv import load_dotenv
from PIL import Image, ImageTk
import threading

# Assuming screenshot.py is in the same directory
from screenshot import WindowCapture

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url=os.environ.get("OPENROUTER_BASE_URL"),
)

def encode_image_to_base64(image):
    """Encodes a PIL Image object to base64."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Save as PNG to preserve quality
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def chat_with_model(model_name, messages):
    """Sends messages to the model and returns the response."""
    try:
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            seed=12345,
            user="my-test-user",
        )
        response = chat_completion.choices[0].message.content
        return response
    except APIError as e:
        messagebox.showerror("API Error", f"OpenAI API Error: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        return None

class ChatApp:
    def __init__(self, master):
        self.master = master
        master.title("OpenRouter Chat")

        self.model_name = "openai/chatgpt-4o-latest"  # Changed default model
        # --- Initialize messages with system prompt ---
        self.messages = [{
            "role": "system",
            "content": "You are a Minecraft assistant. Always provide precise, actionable answers based on the given options. When analyzing images, answer questions directly with detailed and accurate information—no unnecessary explanations or moral lectures. If given a choice, always pick one based on the provided details—no avoiding decisions or offering neutral responses."
        }]
        self.window_capture = WindowCapture() # Initialize WindowCapture
        self.selected_window_title = None  # Store selected window title

        # Add a list to store screenshot history
        self.screenshot_history = []
        
        # --- UI Elements ---

        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled', height=15, width=60)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_display.tag_configure('user', foreground='blue')
        self.chat_display.tag_configure('assistant', foreground='green')
        self.chat_display.tag_configure('center', justify='center')  # For centering images

        # Message Entry
        self.message_entry = ttk.Entry(master, width=60)
        self.message_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.message_entry.bind("<Return>", self.send_message)

        # Button Frame (for Send and Screenshot)
        button_frame = tk.Frame(master)
        button_frame.pack(pady=(0,10))

        # Send Button
        self.send_button = ttk.Button(button_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)

        # Select Window Button
        self.select_window_button = ttk.Button(button_frame, text="Select Window", command=self.select_window)
        self.select_window_button.pack(side=tk.LEFT, padx=5)

        # Capture Screenshot Button
        self.screenshot_button = ttk.Button(button_frame, text="Capture Screenshot", command=self.capture_and_display_screenshot)
        self.screenshot_button.pack(side=tk.LEFT, padx=5)

        # Model Selection (Combobox)
        model_frame = tk.Frame(master)
        model_frame.pack(pady=(0, 10))

        model_label = tk.Label(model_frame, text="Select Model:")
        model_label.pack(side=tk.LEFT, padx=5)

        self.model_var = tk.StringVar()
        model_options = [
            "openai/chatgpt-4o-latest",  # Added as first option
            "mistralai/mistral-medium", 
            "openai/gpt-4o-mini", 
            "google/gemini-1.5-pro-002"
        ] # Add more as needed
        self.model_combobox = ttk.Combobox(model_frame, textvariable=self.model_var, values=model_options, state="readonly")
        self.model_combobox.pack(side=tk.LEFT)
        self.model_combobox.set(self.model_name)  # Set default value
        self.model_combobox.bind("<<ComboboxSelected>>", self.change_model)

        # --- Screenshot Preview ---
        self.screenshot_label = tk.Label(master, text="No Screenshot Selected")
        self.screenshot_label.pack()
        self.screenshot_image = None  # Store the PIL Image
        self.screenshot_tk = None     # Store the PhotoImage for display

        # Add loading indicator
        self.loading_label = tk.Label(master, text="")
        self.loading_label.pack()

        # Add logo at bottom right
        try:
            # Create a frame for the logo
            logo_frame = tk.Frame(master)
            logo_frame.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)
            
            # Load and resize the logo
            logo_img = Image.open("flowers.png")
            # Resize the logo to be 50x50 pixels (adjust size as needed)
            logo_img = logo_img.resize((140, 100), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(logo_img)
            
            # Create and pack the logo label
            logo_label = tk.Label(logo_frame, image=self.logo_tk)
            logo_label.pack()
        except Exception as e:
            print(f"Could not load logo: {e}")

    def center_window(self, window, width=300, height=150):
        """Centers any window on the screen."""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def change_model(self, event=None):
        self.model_name = self.model_var.get()
        self.add_message("System", f"Model changed to {self.model_name}", tag='assistant')


    def select_window(self):
        """Opens a window to select the window to capture."""
        windows = self.window_capture.get_window_list()
        if not windows:
            messagebox.showerror("Error", "No windows found!")
            return

        window_titles = [f"{win['owner']} - {win['title']}" for win in windows]

        popup = tk.Toplevel(self.master)
        popup.title("Select Window")
        # Center the popup window
        self.center_window(popup)
        
        selected_window_var = tk.StringVar()

        if window_titles:
            selected_window_var.set(window_titles[0])
            window_menu = tk.OptionMenu(popup, selected_window_var, *window_titles)
            window_menu.pack(pady=10)
        else:
            tk.Label(popup, text="No windows found.").pack(pady=10)

        def confirm_selection():
            selected_title = selected_window_var.get().split(" - ", 1)[1]
            self.window_capture.save_window_to_cache(selected_title)
            self.selected_window_title = selected_title
            popup.destroy()

        confirm_button = tk.Button(popup, text="Confirm", command=confirm_selection)
        confirm_button.pack()
        
        # Prevent interaction with main window while popup is open
        popup.transient(self.master)
        popup.grab_set()

    def capture_and_display_screenshot(self):
        """Captures, saves, and displays the screenshot."""
        # Check if a window has been selected
        if self.selected_window_title is None:
            messagebox.showerror("Error", "Please select a window first.")
            return

        # Use the stored window title
        img = self.window_capture.capture_and_save(self.selected_window_title)
        if img:
            # Resize for display (optional, but recommended)
            max_width = 300  # Or whatever size you want
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            self.screenshot_image = img  # Store the PIL Image
            self.screenshot_tk = ImageTk.PhotoImage(self.screenshot_image)
            self.screenshot_label.config(image=self.screenshot_tk, text="")  # Update label
        else:
            messagebox.showerror("Error", "Failed to capture screenshot.")


    def add_message(self, role, content, tag=None):
        """Adds a message to the chat display with optional screenshot."""
        self.chat_display.config(state='normal')
        
        # Add the message text
        if tag:
            self.chat_display.insert(tk.END, f"{role}: {content}\n", tag)
        else:
            self.chat_display.insert(tk.END, f"{role}: {content}\n")
            
        # If this is a user message and we have a screenshot, add it
        if role == "You" and self.screenshot_image:
            # Create thumbnail
            thumbnail_size = (200, 150)  # Adjust size as needed
            thumbnail = self.screenshot_image.copy()
            thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and store it to prevent garbage collection
            photo = ImageTk.PhotoImage(thumbnail)
            self.screenshot_history.append(photo)  # Keep reference to prevent garbage collection
            
            # Insert thumbnail
            self.chat_display.insert(tk.END, '\n', 'center')
            self.chat_display.image_create(tk.END, image=photo)
            self.chat_display.insert(tk.END, '\n\n', 'center')
            
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def show_loading(self, show=True):
        """Shows or hides the loading indicator."""
        if show:
            self.loading_label.config(text="Sending message...")
            self.send_button.config(state='disabled')
            self.message_entry.config(state='disabled')
        else:
            self.loading_label.config(text="")
            self.send_button.config(state='normal')
            self.message_entry.config(state='normal')

    def send_message_thread(self, user_input, message_content):
        """Handles the message sending in a separate thread."""
        self.messages.append({"role": "user", "content": message_content})
        
        try:
            response = chat_with_model(self.model_name, self.messages)
            
            # Update UI in the main thread
            self.master.after(0, lambda: self.handle_response(response))
        finally:
            # Always re-enable UI elements
            self.master.after(0, lambda: self.show_loading(False))

    def handle_response(self, response):
        """Handles the model's response in the main thread."""
        if response:
            self.add_message("Model", response, 'assistant')
            self.messages.append({"role": "assistant", "content": response})

    def send_message(self, event=None):
        """Sends the user's message and gets the model's response."""
        user_input = self.message_entry.get()
        if not user_input:
            return  # Do nothing if the entry is empty

        # Add the user message once
        self.add_message("You", user_input, 'user')
        self.message_entry.delete(0, tk.END)

        # Prepare the message content, including the image if available
        message_content = [{"type": "text", "text": user_input}]
        if self.screenshot_image:
            base64_image = encode_image_to_base64(self.screenshot_image)
            message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
            # Store screenshot temporarily and clear the display
            temp_screenshot = self.screenshot_image
            self.screenshot_image = None
            self.screenshot_label.config(image="", text="No Screenshot Selected")
            # Restore screenshot temporarily for the message content
            self.screenshot_image = temp_screenshot

        # Show loading indicator and disable input
        self.show_loading(True)

        # Start message sending in a separate thread
        thread = threading.Thread(
            target=self.send_message_thread,
            args=(user_input, message_content),
            daemon=True
        )
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    
    # Center the main window using the new method
    app.center_window(root, width=800, height=600)
    
    root.mainloop()

import websocket
import json
import time

class MinecraftWebSocket:
    def __init__(self):
        self.ws = None
        self.connect()
        self.max_retries = 3  # Add max retries for commands

    def connect(self):
        try:
            if self.ws:
                self.ws.close()
            self.ws = websocket.WebSocket()
            self.ws.connect("ws://localhost:8765")
            print("Successfully connected to Minecraft server")
        except Exception as e:
            print(f"Failed to connect to Minecraft server: {e}")
            self.ws = None

    def send_command(self, command, params=None):
        for attempt in range(self.max_retries):
            if self.ws is None:
                print(f"Attempting to reconnect (attempt {attempt + 1}/{self.max_retries})")
                self.connect()
                if self.ws is None:
                    time.sleep(1)  # Wait before retry
                    continue

            message = {
                "command": command,
                "params": params or {}
            }
            
            try:
                self.ws.send(json.dumps(message))
                response = self.ws.recv()
                return response
            except websocket.WebSocketConnectionClosedException:
                print("Connection lost, attempting to reconnect...")
                self.connect()
            except Exception as e:
                print(f"Error sending command: {e}")
                self.connect()  # Try to reconnect
                time.sleep(0.5)  # Add delay between retries
        
        print(f"Failed to send command '{command}' after {self.max_retries} attempts")
        return None

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

# Create a global instance
mc_socket = MinecraftWebSocket()

def move_forward(distance):
    """Moves the player forward by the specified distance."""
    mc_socket.send_command("move_forward", {"distance": distance})
    time.sleep(0.2)

def look_left(degrees):
    """Rotates the player's view to the left by the specified degrees."""
    mc_socket.send_command("look_left", {"degrees": degrees})

def look_right(degrees):
    """Rotates the player's view to the right by the specified degrees."""
    mc_socket.send_command("look_right", {"degrees": degrees})

def look_up(degrees):
    """Changes the player's pitch upwards."""
    mc_socket.send_command("look_up", {"degrees": degrees})

def look_down(degrees):
    """Changes the player's pitch downwards."""
    mc_socket.send_command("look_down", {"degrees": degrees})

def center_view():
    """Centers the player's view."""
    mc_socket.send_command("center_view")

def post_to_chat(msg):
    """Posts a message to the Minecraft chat."""
    mc_socket.send_command("chat", {"message": msg})

def attack():
    mc_socket.send_command("attack", {})
import websocket
import json
import time

class MinecraftWebSocket:
    def __init__(self):
        self.ws = None
        self.connect()

    def connect(self):
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect("ws://localhost:8765")
        except Exception as e:
            print(f"Failed to connect to Minecraft server: {e}")
            self.ws = None

    def send_command(self, command, params=None):
        if self.ws is None:
            print("Not connected to Minecraft server")
            return

        message = {
            "command": command,
            "params": params or {}
        }
        
        try:
            self.ws.send(json.dumps(message))
            response = self.ws.recv()
            return response
        except Exception as e:
            print(f"Error sending command: {e}")
            self.connect()  # Try to reconnect
            return None

    def close(self):
        if self.ws:
            self.ws.close()

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
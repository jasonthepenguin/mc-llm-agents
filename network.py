import websocket

def on_message(ws, message):
    print(f"Received from server: {message}")

ws = websocket.WebSocket()
ws.connect("ws://localhost:8765")
ws.send("Hello, Minecraft!")
ws.close()
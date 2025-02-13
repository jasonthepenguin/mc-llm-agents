from MCPI_Scripts.move import mc_socket

def check_for_door():
    """Check for a door and interact with it"""
    mc_socket.send_command("interact")
    return True


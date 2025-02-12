import mcpi.minecraft as minecraft
import mcpi.block as block
import time


def move_forward(mc, distance):
    """Moves the player forward, handling obstacles one block high and doors."""

    PLAYER_HEIGHT = 1.62  # Approximate player height in blocks

    pos = mc.player.getPos()
    direction = mc.player.getDirection()

    # --- Restrict movement to the XZ plane ---
    magnitude_xz = (direction.x**2 + direction.z**2)**0.5
    if magnitude_xz > 0:
        direction_xz = minecraft.Vec3(direction.x / magnitude_xz, 0, direction.z / magnitude_xz)
    else:
        mc.postToChat("Cannot move: No horizontal direction.")
        return

    for _ in range(distance):
        new_x = pos.x + direction_xz.x
        new_y = pos.y  # Don't initially change y
        new_z = pos.z + direction_xz.z
        new_pos = minecraft.Vec3(new_x, new_y, new_z)

        # --- Obstacle Detection and Handling ---
        block_below = mc.getBlock(new_pos.x, new_pos.y - 1, new_pos.z)
        block_at_feet_data = mc.getBlockWithData(new_pos.x, new_pos.y, new_pos.z)
        block_at_head_data = mc.getBlockWithData(new_pos.x, new_pos.y + PLAYER_HEIGHT - 0.1, new_pos.z) #check just below head
        block_above = mc.getBlock(new_pos.x, new_pos.y + 1, new_pos.z) #still need for door logic

        


        # --- Step-up Logic ---
        if (block_at_feet_data.id != block.AIR.id and
            block_at_head_data.id == block.AIR.id and
            block_below != block.AIR.id):

            # Calculate the *exact* Y level of the top of the obstacle
            next_block_y = int(new_pos.y) + 1

            # Step up.
            new_pos.y = float(next_block_y)
            print(f"Stepping up to: {new_pos}")

            # We don't need to re-check block_above here, as block_at_head_data covers it

        elif block_at_feet_data.id != block.AIR.id:
            # --- Door Handling (Simplified) ---
            if block_at_feet_data.id == block.DOOR_WOOD.id:
                if (block_at_feet_data.data & 0x4) == 0x4:  # Door open
                    pass # proceed
                elif block_above == block.AIR.id: #closed but can step up
                    new_pos.y = float(int(new_pos.y + 1))
                    print(f"Stepping up (door) to: {new_pos}")
                else:
                    mc.postToChat("Cannot move: Door closed.")
                    return
            else:
                mc.postToChat("Cannot move: Blocked.")
                return

        # --- End Obstacle Detection ---

        mc.player.setTilePos(new_pos)
        pos = new_pos
        time.sleep(0.2)


def look_left(mc, degrees):
    """Rotates the player's view to the left by the specified degrees."""
    current_rotation = mc.player.getRotation()
    new_rotation = (current_rotation - degrees) % 360  # Changed from + to -
    mc.player.setRotation(new_rotation)

def look_right(mc, degrees):
    """Rotates the player's view to the right by the specified degrees."""
    current_rotation = mc.player.getRotation()
    new_rotation = (current_rotation + degrees) % 360  # Changed from - to +
    mc.player.setRotation(new_rotation)

def look_up(mc, degrees):
    """Changes the player's pitch (up/down angle) upwards, limited to -90 to 90."""
    current_pitch = mc.player.getPitch()
    new_pitch = current_pitch - degrees  # Changed to subtract for consistent behavior
    # Clamp the pitch to the valid range
    new_pitch = max(-90, min(90, new_pitch))
    mc.player.setPitch(new_pitch)

def look_down(mc, degrees):
    """Changes the player's pitch (up/down angle) downwards, limited to -90 to 90."""
    current_pitch = mc.player.getPitch()
    new_pitch = current_pitch + degrees  # Changed to add for consistent behavior
    # Clamp the pitch to the valid range
    new_pitch = max(-90, min(90, new_pitch))
    mc.player.setPitch(new_pitch)

def center_view(mc):
    """Centers the player's view by setting rotation to 0 and pitch to 0."""
    mc.player.setRotation(0)  # Face North
    mc.player.setPitch(0)     # Look straight ahead


def post_to_chat(mc, msg):
    """Posts a message to the Minecraft chat."""
    mc.postToChat(msg)
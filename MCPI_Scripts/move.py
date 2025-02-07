import mcpi.minecraft as minecraft
import mcpi.block as block
import time

# Connect to the Minecraft server
mc = minecraft.Minecraft.create()

def move_forward(distance):
    """Moves the player forward, handling obstacles one block high."""

    pos = mc.player.getTilePos()
    direction = mc.player.getDirection()

    magnitude = (direction.x**2 + direction.y**2 + direction.z**2)**0.5
    if magnitude > 0:
        direction = minecraft.Vec3(direction.x / magnitude, direction.y / magnitude, direction.z / magnitude)
    else:
        mc.postToChat("Cannot move: Looking straight up/down.")
        return

    for _ in range(distance):
        # Use floats for new position calculation
        new_x = pos.x + direction.x
        new_y = pos.y + direction.y
        new_z = pos.z + direction.z
        new_pos = minecraft.Vec3(new_x, new_y, new_z)

        # --- Obstacle Detection and Handling ---
        # Get blocks *once* and store in variables
        block_below = mc.getBlock(new_pos.x, new_pos.y - 1, new_pos.z)
        block_at = mc.getBlock(new_pos.x, new_pos.y, new_pos.z)
        block_above = mc.getBlock(new_pos.x, new_pos.y + 1, new_pos.z)

        if block_at != block.AIR.id:  # Something is blocking the way
            if block_above == block.AIR.id and block_below != block.AIR.id:
                # Try to step up one block.  No need to recalculate new_pos
                new_pos = minecraft.Vec3(new_x, new_y + 1, new_z)
                # Check block above *after* moving up.
                block_above_new = mc.getBlock(new_pos.x, new_pos.y + 1, new_pos.z)
                if block_above_new != block.AIR.id:
                    mc.postToChat("Cannot move: No space to step up.")
                    return
            else:
                mc.postToChat("Cannot move: Blocked.")
                return  # Cant move here, blocked

        # --- End Obstacle Detection ---

        mc.player.setTilePos(new_pos)  # setTilePos *can* take floats
        pos = new_pos  # Update current position with the (potentially) floating-point values.
        time.sleep(0.2)


# --- Main program ---
mc.postToChat("Moving forward 10 blocks!")
mc.postToChat("NicDunz i am near.")
move_forward(10)
mc.postToChat("Action Done! Sending next screenshot to LLM")
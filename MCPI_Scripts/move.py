import mcpi.minecraft as minecraft
import mcpi.block as block
import time

# Connect to the Minecraft server
mc = minecraft.Minecraft.create()

def move_forward(distance):
    """Moves the player forward, handling obstacles one block high and doors."""

    pos = mc.player.getPos()
    direction = mc.player.getDirection()

    magnitude = (direction.x**2 + direction.y**2 + direction.z**2)**0.5
    if magnitude > 0:
        direction = minecraft.Vec3(direction.x / magnitude, direction.y / magnitude, direction.z / magnitude)
    else:
        mc.postToChat("Cannot move: Looking straight up/down.")
        return

    for _ in range(distance):
        new_x = pos.x + direction.x
        new_y = pos.y + direction.y
        new_z = pos.z + direction.z
        new_pos = minecraft.Vec3(new_x, new_y, new_z)

        # --- Obstacle Detection and Handling ---
        block_below = mc.getBlock(new_pos.x, new_pos.y - 1, new_pos.z)
        block_at_data = mc.getBlockWithData(new_pos.x, new_pos.y, new_pos.z)  # Use getBlockWithData
        block_above = mc.getBlock(new_pos.x, new_pos.y + 1, new_pos.z)

        if block_at_data.id != block.AIR.id:
            # Check if it's a door
            if block_at_data.id == block.DOOR_WOOD.id:
                # Check if the door is open (top or bottom half)
                if (block_at_data.data & 0x4) == 0x4:  # Check bit 2 (0x4) for open state
                    pass  # Door is open, proceed
                elif block_above == block.AIR.id: #closed door but we can step up
                    # Step up one block
                    new_pos.y += 1
                    # Recheck block_above *after* moving up.
                    block_above_new = mc.getBlock(new_pos.x, new_pos.y + 1, new_pos.z)
                    if block_above_new != block.AIR.id:
                        mc.postToChat("Cannot move: No space to step up.")
                        return
                else:
                    mc.postToChat("Cannot move: Door closed.")
                    return
            elif block_above == block.AIR.id and block_below != block.AIR.id:
                # Step up one block
                new_pos.y += 1
                block_above_new = mc.getBlock(new_pos.x, new_pos.y + 1, new_pos.z)
                if block_above_new != block.AIR.id:
                    mc.postToChat("Cannot move: No space to step up.")
                    return
            else:
                mc.postToChat("Cannot move: Blocked.")
                return

        # --- End Obstacle Detection ---

        mc.player.setTilePos(new_pos)
        pos = new_pos
        time.sleep(0.2)


# --- Main program ---
mc.postToChat("Moving forward 10 blocks!")
mc.postToChat("NicDunz i am near.")
move_forward(10)
mc.postToChat("Action Done! Sending next screenshot to LLM")
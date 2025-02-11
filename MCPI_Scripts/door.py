import mcpi.minecraft as minecraft
import mcpi.block as block

# Connect to Minecraft
mc = minecraft.Minecraft.create()

def check_for_door(mc):
    # Get the player's position
    pos = mc.player.getPos()
    
    # Check blocks in front of the player (larger area to ensure we catch the door)
    for dx in range(-2, 3):
        for dy in range(0, 2):  # Only check ground level and one block up
            for dz in range(-2, 3):
                # Get the block at each position
                block_pos = (int(pos.x + dx), int(pos.y + dy), int(pos.z + dz))
                block_with_data = mc.getBlockWithData(block_pos[0], block_pos[1], block_pos[2])
                
                # If it's a wooden door (block ID 64)
                if block_with_data.id == 64:
                    # Check if the door is closed (data values 0-3 indicate closed states)
                    if block_with_data.data in [0, 1, 2, 3]:
                        # Open the door.  The open state depends on the hinge and direction.
                        # A door's data value will be 0-3 when closed, and 4-7 when open.
                        # We can calculate the opened state by adding 4.
                        new_data = block_with_data.data + 4
                        mc.setBlock(block_pos[0], block_pos[1], block_pos[2], 64, new_data)
                        return True
    return False


# Just check once and exit
#if check_for_door():
#    print("Door opened - script ending")
#    mc.postToChat("Action Done! Sending next screenshot to LLM")
#else:
#    print("No door found")
#    mc.postToChat("Action Done! Sending next screenshot to LLM")


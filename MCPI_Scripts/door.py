import mcpi.minecraft as minecraft
import mcpi.block as block

# Connect to Minecraft
mc = minecraft.Minecraft.create()

def check_for_door():
    # Get the player's position
    pos = mc.player.getPos()
    
    # Check blocks in front of the player (larger area to ensure we catch the door)
    for dx in range(-2, 3):
        for dy in range(0, 2):  # Only check ground level and one block up
            for dz in range(-2, 3):
                # Get the block at each position
                block_pos = (int(pos.x + dx), int(pos.y + dy), int(pos.z + dz))
                block_type = mc.getBlock(block_pos[0], block_pos[1], block_pos[2])
                
                # If it's a wooden door (block ID 64)
                if block_type == 64:
                    # Simply try to open the door
                    # Try a few common door states that represent "open"
                    for state in [4, 5, 6, 7]:
                        mc.setBlock(block_pos[0], block_pos[1], block_pos[2], 64, state)
                    return True
    return False

# Just check once and exit
if check_for_door():
    print("Door opened - script ending")
else:
    print("No door found")

import os
import time
import subprocess
from PIL import Image
import cv2
import numpy as np

# ADB Configuration
ADB_PATH = "adb"  # Make sure adb is in your PATH or use full path
BLUESTACKS_PORT = "5555"

# Game Configuration
CHECK_INTERVAL = 40  # seconds
RESOURCE_CHECK_INTERVAL = 0  # seconds
BUILDING_CHECK_INTERVAL = 0  # seconds

# Image templates path (you need to create these screenshots)
TEMPLATES = {
    "training_complete": "templates/training_complete.png",
    "march_queue": "templates/march_queue.png",
    "building_complete": "templates/building_complete.png",
    "furnace": "templates/furnace.png",
    "embassy": "templates/embassy.png",
    "collect_resources": "templates/collect_resources.png",
    "help_button": "templates/help_button.png",
    "online_rewards": "templates/online_rewards.png",
    "Tree_of_life": "templates/Tree_of_life.png"
}

def connect_adb():
    """Ensure ADB is connected to BlueStacks"""
    subprocess.run([ADB_PATH, "connect", f"127.0.0.1:{BLUESTACKS_PORT}"])
    
def tap(x, y):
    """Send tap command via ADB"""
    subprocess.run([ADB_PATH, "shell", "input", "tap", str(x), str(y)])
    time.sleep(2)  # Delay for game response

def swipe(x1, y1, x2, y2, duration=300):
    """Send swipe command via ADB"""
    subprocess.run([ADB_PATH, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
    time.sleep(1)

from datetime import datetime
import os

#implemented
def generate_timestamped_filename(prefix="capture", suffix="png", folder="screenshots"):
    """
    Generates a filename with timestamp: {prefix}_{YYYYMMDD_HHMMSS}.{suffix}
    
    Args:
        prefix (str): File description (e.g. "troops", "resources")
        suffix (str): File extension (e.g. "png", "jpg")
        folder (str): Target directory (will be created if missing)
    
    Returns:
        str: Full file path like "screenshots/troops_20230815_143022.png"
    """
    # Create directory if needed
    os.makedirs(folder, exist_ok=True)
    
    # Generate timestamp (ISO format without special characters)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Construct full path
    filename = f"{prefix}_{timestamp}.{suffix}"
    full_path = os.path.join(folder, filename)
    
    return full_path

#implemented
def capture_screen():
    """Capture current screen via ADB"""
    subprocess.run([ADB_PATH, "exec-out", "screencap", "-p"], stdout=open("screen.png", "wb"))
    return cv2.imread("screen.png")

#implemented
def find_template(template_name, threshold=0.8):
    """Find template on screen using OpenCV"""
    template = cv2.imread(TEMPLATES[template_name])
    if template is None:
        print(f"Template {template_name} not found!")
        return None
    
    screen = capture_screen()
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    if max_val > threshold:
        return {
            "x": max_loc[0] + template.shape[1] // 2,
            "y": max_loc[1] + template.shape[0] // 2,
            "confidence": max_val
        }
    return None

#implemented
def find_in_region(template_name, region, threshold=0.8):
    """Search only within a defined region (x,y,w,h)"""
    # Capture and crop the region
    screen = capture_screen()
    x, y, w, h = region
    search_area = screen[y:y+h, x:x+w]

    # For debugging purposes and template generation
    cv2.imwrite(generate_timestamped_filename(), search_area)  

    # Load template
    template = cv2.imread(TEMPLATES[template_name])
    if template is None:
        print(f"Template {template_name} not found!")
        return None

    # Perform matching
    res = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    
    if max_val > threshold:
        # Return GLOBAL coordinates
        return {
            "x": x + max_loc[0] + template.shape[1]//2,
            "y": y + max_loc[1] + template.shape[0]//2,
            "confidence": max_val
        }
    return None

#implemented
def train_troops():
    """Train troops if training is complete"""
    tap(20, 1061) # SidePanel Location
    training_complete = find_in_region("training_complete", (48, 1075, 800, 100))
    if training_complete:
        print("Training complete detected - starting new training")
        tap(424, 1075) # Infantry Button
        # Infantry training
        tap(700, 1300)  # Centre of building
        tap(1050, 1635)  # Train Button outside 
        tap(714, 938)  # Random Space
        tap(1073, 2380) # Train Button Inside
        tap(93, 80) # Back Button

        # Lancer training
        tap(20, 1061) # SidePanel Location
        tap(424, 1203) # Lancer Button
        tap(700, 1300)  # Centre of building
        tap(1050, 1635)  # Train Button outside 
        tap(714, 938)  # Random Space
        tap(1073, 2380) # Train Button Inside
        tap(93, 80) # Back Button  

        # Marksman training
        tap(20, 1061) # SidePanel Location
        tap(424, 1382) # Marksman Button
        tap(700, 1300)  # Centre of building
        tap(1050, 1635)  # Train Button outside 
        tap(714, 938)  # Random Space
        tap(1073, 2380) # Train Button Inside
        tap(93, 80) # Back Button  

        # return to world map
        tap(1292, 2440) # World Map Button
        time.sleep(2)
        return True
    else: 
        print("Training not complete - checking again")
        tap( 927, 1098) # Closing the Sidebar
        return False

def manage_marching():
    """Manage resource gathering marches"""
    march_queue = find_template("march_queue")
    if march_queue:
        # Analyze queue count (this needs custom implementation based on your UI)
        # For now, we'll assume we can detect available march slots
        available_slots = 3 - get_current_marches()  # Implement get_current_marches() based on your UI
        
        if available_slots > 0:
            print(f"Found {available_slots} available march slots - sending gatherers")
            # Open world map
            tap(100, 100)  # Adjust to your world map button
            time.sleep(2)
            
            # Find and tap resource tiles
            resource = find_template("collect_resources")
            if resource:
                tap(resource["x"], resource["y"])
                tap(1400, 800)  # March button
                tap(1400, 900)  # Confirm button
                return True
    return False

#implemented
def click_help():
    """Click help button"""
    help_button = find_in_region("help_button",(1004, 2230, 140, 90))
    if help_button:
        print("Help button detected - clicking")
        tap(help_button["x"], help_button["y"])
        return True
    else:
        print("Help button not detected")
        return False

#implemented
def click_onine_rewards():
    """Click onine rewards button"""
    tap(20, 1061) # SidePanel Location
    time.sleep(2)
    swipe(338,1629, 338, 50, 600) 
    online_rewards = find_in_region("online_rewards",(48, 1380, 800, 100))
    if online_rewards:
        print("Online rewards button detected - clicking")
        tap(100, 1400) # click the button
        time.sleep(5)
        tap(100, 1400) # click to quit
        time.sleep(5)
        return True
    else:
        print("Online rewards button not detected")
        tap( 927, 1098) # Closing the Sidebar
        return False

def click_tree_of_life():
    """Click tree_of_life button"""
    tap(20, 1061) # SidePanel Location
    time.sleep(2)
    swipe(338,1629, 338, 50, 600) 
    tree_of_life = find_in_region("Tree_of_life",(48, 1380, 800, 50))
    if tree_of_life:
        print("tree_of_life button detected - clicking")
        tap(tree_of_life["x"], tree_of_life["y"])
        return True
    else:
        print("tree_of_life button not detected")
        tap( 927, 1098) # Closing the Sidebar
        return False

def manage_buildings():
    """Manage building construction"""
    building_complete = find_template("building_complete")
    if building_complete:
        print("Building complete detected - starting new construction")
        tap(building_complete["x"], building_complete["y"])
        
        # Check for priority buildings first
        furnace = find_template("furnace")
        if furnace:
            tap(furnace["x"], furnace["y"])
            tap(1400, 800)  # Upgrade button
            return True
        
        embassy = find_template("embassy")
        if embassy:
            tap(embassy["x"], embassy["y"])
            tap(1400, 800)  # Upgrade button
            return True
        
        # If no priority buildings, upgrade any available building
        # This would need to be customized for your base layout
        tap(600, 400)  # Example building position
        if find_template("upgrade_available"):  # You'd need this template
            tap(1400, 800)  # Upgrade button
            return True
    
    return False

def main():
    connect_adb()
    
    # Main automation loop
    while True:
        # Check troops training
        if train_troops():
            
            continue

        if click_help():
            time.sleep(2)
            continue
            
        if click_onine_rewards():
            time.sleep(2)
            continue

        if click_tree_of_life():
            time.sleep(2)
            continue
        # # Check resource gathering
        # if manage_marching():
        #     time.sleep(RESOURCE_CHECK_INTERVAL)
        #     continue
            
        # # Check building construction
        # if manage_buildings():
        #     time.sleep(BUILDING_CHECK_INTERVAL)
        #     continue
        # Uncomment the above lines to enable the checks
        # tap(80, 82) # Profile Pic and back location
        
        # tap(335, 1109) #Infantry Location
        # If nothing to do, wait before checking again
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
import os
import time
import subprocess
from PIL import Image, ImageGrab 
import cv2
import numpy as np
import random
import re
import pyautogui
from typing import Tuple, Optional
from datetime import datetime


# ADB Configuration
ADB_PATH = "adb"  # Make sure adb is in your PATH or use full path
BLUESTACKS_PORT = "5555"
NUMBER_OF_RALLIES = 2
# Game Configuration
CHECK_INTERVAL = 3  # seconds
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
    "Tree_of_life": "templates/Tree_of_life.png",
    "red_2": "templates/red_2.png",
    "cancel": "templates/cancel.png",
    "heal_troops_button_1": "templates/heal_troops_button_1.png",
    "heal_troops_button_2": "templates/heal_troops_button_2.png",
    "heal_troops_button_3": "templates/heal_troops_button_3.png",
    "heal_troops_button_4": "templates/heal_troops_button_4.png",
    "heal_troops_button_5": "templates/heal_troops_button_5.png",
    "heal_troops_button_6": "templates/heal_troops_button_6.png",
    "heal_troops_button_7": "templates/heal_troops_button_7.png",
    "heal_troops_button_8": "templates/heal_troops_button_8.png",
    "heal_troops_button_9": "templates/heal_troops_button_9.png",
    "chat_label": "templates/chat_label.png"
}

def connect_adb():
    """Ensure ADB is connected to BlueStacks"""
    subprocess.run([ADB_PATH, "connect", f"127.0.0.1:{BLUESTACKS_PORT}"])
    
def tap(x, y):
    """Send tap command via ADB"""
    subprocess.run([ADB_PATH, "shell", "input", "tap", str(x), str(y)])
    human_sleep(2,3)  # Delay for game response

def swipe(x1, y1, x2, y2, duration=300):
    """Send swipe command via ADB"""
    subprocess.run([ADB_PATH, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
    human_sleep(1,2)

def input_text(text: str):
    """Type text using ADB keyboard input"""
    subprocess.run(["adb", "shell", "input", "text", text.replace(" ", "%s")])
    human_sleep(1,2)  # Delay for game response

def human_sleep(min_s: float, max_s: float):
    """Sleep with bell-curve distribution around midpoint"""
    midpoint = (min_s + max_s) / 2
    std_dev = (max_s - min_s) / 4  # 95% within min-max
    
    while True:
        sleep_time = random.normalvariate(midpoint, std_dev)
        if min_s <= sleep_time <= max_s:
            time.sleep(sleep_time)
            return


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
    # cv2.imwrite(generate_timestamped_filename(), search_area)  

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
def has_red_in_region(region, threshold=0.003, debug=False):
    x, y, w, h = region
    
    screenshot = capture_screen()
    search_area = screenshot[y:y+h, x:x+w]
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(search_area, cv2.COLOR_RGB2HSV)
    
    lower_red1 = np.array([0, 50, 50]) # Adjust as needed
    upper_red1 = np.array([10, 255, 255]) # Adjust as needed
    # Handle the special case of red that wraps around the Hue circle
    lower_red2 = np.array([170, 50, 50])  # Red wraps from 170 to 179 in HSV
    upper_red2 = np.array([180, 255, 255])
    
    # Create masks
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Calculate red percentage
    red_pixels = cv2.countNonZero(mask)
    total_pixels = w * h
    red_ratio = red_pixels / total_pixels
    
    if debug:
        # Visualize detection
        debug_img = search_area.copy()
        debug_img[mask != 0] = [255, 0, 0]  # Mark red pixels
        cv2.imshow('Red Detection', cv2.cvtColor(debug_img, cv2.COLOR_RGB2BGR))
        cv2.waitKey(500)
        cv2.destroyAllWindows()
        print(f"Red coverage: {red_ratio:.2%}")
        print(f"threshold: {threshold:.2%}")
    return red_ratio > threshold

#implemented
def start_new_polarTerror():
    i = 0
    while i < NUMBER_OF_RALLIES:
        tap(106,1736) #Search button
        tap(471,1831) #Polar Terror button
        tap(702,2441) #Search button
        human_sleep(1,2)
        tap(758,992) #Rally button
        tap(717,1668) #Hold a Rally button
        tap(417,2355) # Equalise button
        not_enough_energy_button = has_red_in_region((1087,2438, 44, 45))
        if not_enough_energy_button:
            print("Not enough energy to start a new Polar Terror")
            tap(1087, 2438) # Deploy button
            tap(1140, 1051) # Use Button
            tap( 758, 1040) # Button next to use button
            tap(1333, 272) # Close button
        tap(1087, 2438) # Deploy button
        cancel_button = find_in_region("cancel", (207,1525, 397, 50))
        if cancel_button:
                print("Cancel button detected - clicking")
                tap(207,1525) # Cancel button
                tap(83,71) # back button
        else: 
            i += 1
    tap(361, 1517) #tap space
    tap(361, 1517) #tap space again
    return True

#implemented
def train_troops():
    """Train troops if training is complete"""
    tap(8, 1061) # SidePanel Location
    training_complete = find_in_region("training_complete", (48, 1075, 800, 100))
    if training_complete:
        print("Training complete detected - starting new training")
        # time.sleep(60)
        tap(424, 1075) # Infantry Button
        # Infantry training
        tap(700, 1300)  # Centre of building
        tap(700, 1300)  # tap one more time
        tap(1050, 1635)  # Train Button outside
        tap(714, 938)  # Random Space
        tap(1073, 2380) # Train Button Inside
        tap(93, 80) # Back Button

        # Lancer training
        tap(8, 1061) # SidePanel Location
        tap(424, 1203) # Lancer Button
        tap(700, 1300)  # Centre of building
        tap(700, 1300)  # tap one more time        
        tap(1050, 1635)  # Train Button outside 
        tap(714, 938)  # Random Space
        tap(1073, 2380) # Train Button Inside
        tap(93, 80) # Back Button  

        # Marksman training
        tap(8, 1061) # SidePanel Location
        tap(424, 1382) # Marksman Button
        tap(700, 1300)  # Centre of building
        tap(700, 1300)  # tap one more time
        tap(1050, 1635)  # Train Button outside 
        tap(714, 938)  # Random Space
        tap(1073, 2380) # Train Button Inside
        tap(93, 80) # Back Button  

        # return to world map
        tap(1318, 2440) # World Map Button
        human_sleep(2,3)
        return True
    else: 
        print("Training not complete - checking again")
        tap( 927, 1098) # Closing the Sidebar
        return False


#implemented
def click_help():
    """Click help button"""
    help_button = find_in_region("help_button",(1004, 2230, 140, 90))
    if help_button:
        print("Help button detected - clicking")
        tap(help_button["x"], help_button["y"])
        chat_label = find_in_region("chat_label", (0, 0, 800, 200))
        if chat_label:
            print("Chat label detected - clicking back button")
            tap(80,68) # Back button
        return True
    else:
        print("Help button not detected")
        return False

#implemented
def click_onine_rewards():
    """Click onine rewards button"""
    tap(8, 1061) # SidePanel Location
    human_sleep(2,3)
    swipe(338,1629, 338, 50, 600) 
    online_rewards = find_in_region("online_rewards",(48, 1380, 800, 100))
    if online_rewards:
        print("Online rewards button detected - clicking")
        tap(100, 1400) # click the button
        human_sleep(4,6)
        tap(100, 1400) # click to quit
        human_sleep(4,6)
        return True
    else:
        print("Online rewards button not detected")
        tap( 927, 1098) # Closing the Sidebar
        return False

def click_tree_of_life():
    """Click tree_of_life button"""
    tap(8, 1061) # SidePanel Location
    human_sleep(2,4)
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

def find_animated_element(base_name: str, region: tuple, threshold=0.6, variants=9):
    """Check multiple animation frames of the same element"""
    for i in range(1, variants+1):
        if result := find_in_region(f"{base_name}_{i}", region, threshold):
            return result
    return None

def heal_troops():
    """Heal troops if needed"""
    heal_troops = find_animated_element("heal_troops_button", (1072, 2083, 90, 90))
    if heal_troops:
        print("Heal troops button detected - clicking")
        tap(1072,2083) # Heal troops button
        # tap (269,1878) # Quick select button
        # tap(1066,803) # troop number cell
        # input_text("175")
        tap(1010,1848)
        tap(1010,1848)
        return True
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
        # if train_troops():
        #     human_sleep(2,4)
        #     continue
        if click_help():            
            continue
            
        # if click_onine_rewards():
        #     continue

        # if start_new_polarTerror():
        #     human_sleep(540,600) # wait 9-10 minutes for the Polar Terror to finish
        #     continue

        if heal_troops():
            continue

        # if click_tree_of_life():
        #     time.sleep(2)
        #     continue
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
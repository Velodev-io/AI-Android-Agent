import argparse
import datetime
import json
import os
import sys
import time
import re

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

from config import load_config
from and_controller import list_all_devices, AndroidController
from model import GeminiModel, parse_expert_rsp
from utils import print_with_color

def main():
    arg_desc = "AppAgent Expert Mode"
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
    parser.add_argument("--app", help="Name of the app")
    parser.add_argument("--task", help="Task description")
    args = vars(parser.parse_args())

    configs = load_config()
    
    if configs["MODEL"] != "Gemini":
        print_with_color("Expert mode currently only supports Gemini models.", "red")
        sys.exit()

    mllm = GeminiModel(api_key=configs["GEMINI_API_KEY"],
                       model=configs["GEMINI_MODEL"],
                       temperature=configs["TEMPERATURE"],
                       max_tokens=configs["MAX_TOKENS"])

    app = args["app"]
    if not app:
        print_with_color("What is the name of the app?", "blue")
        app = input().replace(" ", "")

    task_desc = args["task"]
    if not task_desc:
        print_with_color("Please enter the task you want me to complete:", "blue")
        task_desc = input()

    device_list = list_all_devices()
    if not device_list:
        print_with_color("ERROR: No device found!", "red")
        sys.exit()
    
    device = device_list[0]
    print_with_color(f"Using device: {device}", "yellow")
    controller = AndroidController(device)
    
    work_dir = "tasks"
    if not os.path.exists(work_dir):
        os.mkdir(work_dir)
    
    task_timestamp = int(time.time())
    dir_name = datetime.datetime.fromtimestamp(task_timestamp).strftime(f"expert_{app}_%Y-%m-%d_%H-%M-%S")
    task_dir = os.path.join(work_dir, dir_name)
    os.mkdir(task_dir)

    round_count = 0
    while round_count < configs["MAX_ROUNDS"]:
        round_count += 1
        print_with_color(f"--- Round {round_count} ---", "yellow")
        
        screenshot_path = controller.get_screenshot(f"step_{round_count}", task_dir)
        xml_path = controller.get_xml(f"step_{round_count}", task_dir)
        
        if screenshot_path == "ERROR" or xml_path == "ERROR":
            print_with_color("Failed to get screen data. Retrying...", "red")
            continue

        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        print_with_color("Analysing screen with Expert Gemini...", "yellow")
        rsp = mllm.ask_gemini(task_desc, screenshot_path, xml_content)
        
        if rsp.startswith("ERROR:"):
            print_with_color(rsp, "red")
            break

        res = parse_expert_rsp(rsp)
        if not res or res[0] == "ERROR":
            print_with_color("Failed to parse response. Ending task.", "red")
            break
            
        act_name = res[0]
        if act_name == "FINISH":
            print_with_color("TASK COMPLETE", "green")
            break
            
        if act_name == "tap":
            try:
                coords = res[1].split(',')
                x, y = int(coords[0]), int(coords[1])
                controller.tap(x, y)
            except:
                print_with_color("Invalid coordinates for tap", "red")
        elif act_name == "type":
            try:
                text = res[2] if len(res) > 2 else ""
                controller.text(text)
            except:
                print_with_color("Failed to enter text", "red")
        elif act_name == "swipe":
            # Simplistic swipe from coords for now
            print_with_color("Swipe not fully implemented in expert mode yet", "red")
        elif act_name == "wait":
            time.sleep(5)
            
        time.sleep(configs["REQUEST_INTERVAL"])

if __name__ == "__main__":
    main()

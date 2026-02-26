import google.generativeai as genai
import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from config import load_config
from prompts import ADVANCED_SYSTEM_PROMPT

configs = load_config()
genai.configure(api_key=configs["GEMINI_API_KEY"])
model = genai.GenerativeModel(configs["GEMINI_MODEL"])

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

prompt = f"""{ADVANCED_SYSTEM_PROMPT}

TASK: Open Axio app.
IMAGE: [Attached]
XML: <node index="0" text="axio" resource-id="com.axio:id/icon" class="android.widget.TextView" bounds="[100,100][200,200]" />

Please respond in the required format."""

# Find a sample image
img_path = "assets/teaser.png" # Just for testing

print("Testing Gemini response length and content...")
try:
    response = model.generate_content([prompt, {"mime_type": "image/png", "data": open(img_path, "rb").read()}], 
                                     generation_config={"max_output_tokens": 1000},
                                     safety_settings=safety_settings)
    print(f"Finish Reason: {response.candidates[0].finish_reason}")
    print(f"Response:\n{response.text}")
except Exception as e:
    print(f"Error: {e}")

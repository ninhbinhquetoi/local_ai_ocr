import sys
import os
import io

# Add "src/" into Python's search path
sys.path.append(os.path.abspath("src"))

import config
from ollama import Client
import file_handler

def main():
    print("Testing OCR environment...")

    # Load Config to get OLLAMA_HOST and MODEL
    config.reload_config()
    print(f"Ollama Host: {config.OLLAMA_HOST}")
    print(f"Model ID: {config.OLLAMA_MODEL}")

    # Check connection
    try:
        client = Client(host=config.OLLAMA_HOST)
        client.ps()
        print("Connected to Ollama successfully.")
    except Exception as e:
        print(f"Failed to connect to Ollama: {e}")
        return

    # Prepare Image
    demo_image = "demo/demo1.png"
    if not os.path.exists(demo_image):
        print(f"Demo image not found at {demo_image}")
        return
    
    print(f"Processing image: {demo_image}")
    try:
        img_bytes = file_handler.get_image_bytes(demo_image) 
    except Exception as e:
        print(f"Failed to load image: {e}")
        return
    
    # Run OCR
    print("Sending request to AI model (this may take a minute)...")
    prompt = config.PROMPTS["p_markdown"]
    
    try:
        response = client.chat(
            model=config.OLLAMA_MODEL,
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [img_bytes] 
            }],
            stream=False # No streaming for simple test
        )
        
        content = response.get('message', {}).get('content', '')
        print("\n--- OCR Result ---\n")
        print(content[:500] + ("\n..." if len(content) > 500 else ""))
        print("\n--- End of Result ---\n")
        print("Test passed!")
        
    except Exception as e:
        print(f"OCR failed: {e}")

if __name__ == "__main__":
    main()

# streamlit_app.py

import streamlit as st
from typing import List, Tuple
from dotenv import load_dotenv # type: ignore
import os
import io
from PIL import Image
import requests
import time

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Debug check for token
if not HF_TOKEN:
    st.error("❌ HF_TOKEN not found in environment variables. Please check your .env file.")
elif not HF_TOKEN.startswith("hf_"):
    st.error("❌ HF_TOKEN appears to be invalid. It should start with 'hf_'")

# Streamlit page setup
st.set_page_config(page_title="Children's Book Blurb Generator", page_icon="📚")
st.title("📚 Children's Book Blurb Generator")

# Hugging Face model options
TEXT_MODELS = [
    "google/flan-t5-base",
    "facebook/opt-125m",
    "distilgpt2"
]

# Update the IMAGE_MODELS list to use more reliable models
IMAGE_MODELS = [
    "stabilityai/stable-diffusion-v1-5",  # More reliable model
    "CompVis/stable-diffusion-v1-4",    # Alternative stable model
    "stabilityai/stable-diffusion-2-1"  # Another reliable option
]

# Inputs
selected_text_model = st.selectbox("🧠 Choose a text generation model", TEXT_MODELS)
selected_image_model = st.selectbox("🎨 Choose an image generation model", IMAGE_MODELS)

char_input = st.text_area(
    "👧🧒 Enter characters as a list of (Name, Age) pairs — one per line, e.g.,\nAlice, 7\nBob, 10"
)

book_title = st.text_input("📖 Book Title")
genre = st.text_input("✨ Genre (optional)")
setting = st.text_input("🌍 Setting (optional)")

# Parse character input
def parse_characters(text: str) -> List[Tuple[str, int]]:
    lines = text.strip().split("\n")
    characters = []
    for line in lines:
        try:
            name, age = line.split(",")
            characters.append((name.strip(), int(age.strip())))
        except ValueError:
            st.error(f"Invalid format in line: '{line}'. Use format: Name, Age")
            return []
    return characters

# Build prompt for text generation
def build_prompt(characters, title, genre, setting):
    char_str = ", ".join([f"{name} ({age})" for name, age in characters])
    genre_str = genre if genre else "Use your best guess based on the title"
    setting_str = setting if setting else "Use your best guess based on the title and character names"

    return f"""
ROLE: You are a marketing copywriter who is an expert at writing attractive blurbs for children's books.
CONTEXT: I am a children's book author. I have come up with a list of characters and a title for a book, and I need help coming up with a blurb for the book that will excite children to read it.
TASK: Generate a short blurb (<100 words) for the children's book based on the following inputs:
* Characters: {char_str}
* Title of book: {title}
* Genre of book: {genre_str}
* Setting of story: {setting_str}
Your blurb must be attractive and exciting. It must also be child-appropriate.
""".strip()

# Generate text using Hugging Face API
def get_blurb(prompt: str, model_id: str, token: str) -> str:
    try:
        headers = {"Authorization": f"Bearer {token}"}
        api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        
        # Add parameters to get a longer, complete response
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 150,
                "min_length": 50,
                "temperature": 0.8,
                "top_p": 0.9,
                "do_sample": True
            }
        }
        
        # Add retry logic
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                # Debug the response
                st.write("Debug - API Response:", result)
                
                # Handle different response formats
                generated_text = ""
                if isinstance(result, list):
                    if len(result) > 0:
                        if isinstance(result[0], str):
                            generated_text = result[0]
                        elif isinstance(result[0], dict):
                            generated_text = result[0].get('generated_text', '')
                elif isinstance(result, dict):
                    generated_text = result.get('generated_text', '')
                
                if generated_text:
                    # Clean up the response
                    blurb = generated_text.replace(prompt, "").strip()
                    # Make sure it ends with a complete sentence
                    if not any(blurb.endswith(end) for end in ['.', '!', '?']):
                        blurb = blurb[:blurb.rfind('.')+1] if '.' in blurb else blurb
                    return blurb
                else:
                    st.error(f"❌ No generated text in response: {result}")
                    return ""
            elif response.status_code == 503:
                if attempt < max_retries - 1:
                    st.warning(f"Service temporarily unavailable. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    st.error("❌ Service is currently unavailable. Please try again later.")
                    return ""
            else:
                st.error(f"❌ Text generation failed. Status code: {response.status_code}")
                st.error(f"Response: {response.text}")
                return ""
                
    except Exception as e:
        st.error(f"❌ Text generation failed: {str(e)}")
        return ""

# Generate image using Hugging Face API
def generate_image(blurb: str, title: str, genre: str, hf_token: str) -> Image.Image | None:
    try:
        genre_str = genre if genre else "the story"
        prompt = f"""
ROLE: You are an expert illustrator of children's books.
TASK:
Generate a cover image for a children's book based on the blurb below. The image must be attractive and child-friendly. 
Use a style and mood that reflects the tone and themes of the book, as suggested by the title, genre, and blurb. Watercolor is preferred, but adapt stylistically if it better fits the story.

TITLE: {title}
GENRE: {genre_str}
BLURB: {blurb}
""".strip()
        
        url = f"https://api-inference.huggingface.co/models/{selected_image_model}"
        headers = {"Authorization": f"Bearer {hf_token}"}
        response = requests.post(url, headers=headers, json={"inputs": prompt})
        
         # Add retry logic
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, json={
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": "text, words, letters, watermark",
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5
                }
            })
            
            if response.status_code == 200:
                try:
                    return Image.open(io.BytesIO(response.content))
                except Exception as e:
                    st.error(f"❌ Failed to process image data: {str(e)}")
            elif response.status_code == 503:
                if attempt < max_retries - 1:
                    st.warning(f"Image generation temporarily unavailable. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
            
            # Show the actual error response
            st.error(f"❌ Image generation failed (Status {response.status_code})")
            st.error(f"Response: {response.text}")
            
            if attempt < max_retries - 1:
                st.info(f"Retrying... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            
        return None
    except Exception as e:
        st.error(f"❌ Failed to generate image: {e}")
        return None

# Generate blurb and image
if st.button("✨ Generate Blurb"):
    if not all([char_input, book_title]):
        st.warning("Please fill in the characters and book title.")
    else:
        characters = parse_characters(char_input)
        if characters:
            prompt = build_prompt(characters, book_title, genre, setting)
            blurb = get_blurb(prompt, selected_text_model, HF_TOKEN)
            if blurb:
                st.subheader("📝 Your Book Blurb:")
                st.success(blurb)

                # Image generation
                with st.spinner("🖼️ Generating image..."):
                    image = generate_image(blurb, book_title, genre, HF_TOKEN)

                if image:
                    st.image(image, caption="🎨 AI-Generated Cover Image", use_column_width=True)

                    # Download button
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    st.download_button(
                        label="💾 Download Cover Image",
                        data=buffered.getvalue(),
                        file_name="cover_image.png",
                        mime="image/png"
                    )

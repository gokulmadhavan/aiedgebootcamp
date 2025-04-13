# streamlit_app.py

import streamlit as st
import logging
from typing import List, Tuple
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from transformers import pipeline
from diffusers import StableDiffusionPipeline
import torch
from io import BytesIO
from PIL import Image

# Load Hugging Face token
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Children's Book Blurb Generator", page_icon="📚")
st.title("📚 Children's Book Blurb Generator")

# Dropdowns for model selection
text_models = [
    "google/flan-t5-large",
    "tiiuae/falcon-7b-instruct",
    "mistralai/Mistral-7B-Instruct-v0.1",
]

image_models = [
    "CompVis/stable-diffusion-v1-4",
    "stabilityai/stable-diffusion-2",
]

selected_text_model = st.selectbox("🧠 Choose a text generation model:", text_models)
selected_image_model = st.selectbox("🎨 Choose an image generation model:", image_models)

# Input fields
char_input = st.text_area(
    "👧🧒 Enter characters as a list of (Name, Age) pairs — one per line, e.g.,\nAlice, 7\nBob, 10"
)
book_title = st.text_input("📖 Book Title")
genre = st.text_input("✨ Genre (optional)")
setting = st.text_input("🌍 Setting (optional)")
temperature = st.slider("🎨 Creativity (Temperature)", 0.0, 1.0, 0.8)

# Parse characters
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

# Build prompt
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

# Generate blurb using HuggingFace model
def generate_blurb(prompt: str, model_name: str, token: str):
    try:
        client = InferenceClient(model=model_name, token=token)
        response = client.text_generation(prompt, max_new_tokens=100, temperature=temperature)
        return response.strip()
    except Exception as e:
        logger.error(f"Text generation failed: {e}")
        st.error("❌ Failed to generate blurb.")
        return ""

# Generate image using HuggingFace model
def generate_image(blurb: str, title: str, genre: str, model_id: str, token: str) -> Image.Image:
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

        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            use_auth_token=token,
        ).to("cuda" if torch.cuda.is_available() else "cpu")

        image = pipe(prompt).images[0]
        return image
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        st.error("❌ Failed to generate image.")
        return None

# Run app
if st.button("✨ Generate Blurb and Image"):
    if not HF_TOKEN or not all([char_input, book_title]):
        st.warning("Please fill in all required fields and make sure your Hugging Face token is set.")
    else:
        characters = parse_characters(char_input)
        if characters:
            prompt = build_prompt(characters, book_title, genre, setting)
            blurb = generate_blurb(prompt, selected_text_model, HF_TOKEN)
            if blurb:
                st.subheader("📝 Your Book Blurb:")
                st.success(blurb)

                st.subheader("🖼️ Generated Cover Image:")
                image = generate_image(blurb, book_title, genre, selected_image_model, HF_TOKEN)
                if image:
                    st.image(image, caption="Generated Book Image", use_column_width=True)
                    img_buffer = BytesIO()
                    image.save(img_buffer, format="PNG")
                    st.download_button(
                        label="📥 Download Image",
                        data=img_buffer.getvalue(),
                        file_name="book_cover.png",
                        mime="image/png",
                    )

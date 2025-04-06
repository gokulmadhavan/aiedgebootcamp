# streamlit_app.py

import streamlit as st
import logging
from typing import List, Tuple
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Children's Book Blurb Generator", page_icon="📚")
st.title("📚 Children's Book Blurb Generator")

# Input: API key
api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")

# Input: Characters
char_input = st.text_area(
    "👧🧒 Enter characters as a list of (Name, Age) pairs — one per line, e.g.,\nAlice, 7\nBob, 10"
)

# Input: Book title
book_title = st.text_input("📖 Book Title")

# Optional Inputs
genre = st.text_input("✨ Genre (optional)")
setting = st.text_input("🌍 Setting (optional)")

# Creativity control
temperature = st.slider("🎨 Creativity (Temperature)", 0.0, 1.0, 0.8)

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

# Call OpenAI API (new SDK format)
def get_blurb(prompt: str, api_key: str) -> str:
    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API call failed:\n{e}")
        st.error("❌ OpenAI API call failed. Check the logs or your API key.")
        return ""

# Run the app
if st.button("✨ Generate Blurb"):
    if not all([api_key, char_input, book_title]):
        st.warning("Please fill in the API key, characters, and book title.")
    else:
        characters = parse_characters(char_input)
        if characters:
            prompt = build_prompt(characters, book_title, genre, setting)
            blurb = get_blurb(prompt, api_key)
            if blurb:
                st.subheader("📝 Your Book Blurb:")
                st.success(blurb)

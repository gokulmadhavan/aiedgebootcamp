import streamlit as st
import requests
from dotenv import load_dotenv
import os
from io import BytesIO
from PIL import Image

# Load environment variables
load_dotenv()
API_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Mapping of model display names to HuggingFace model repo names
model_options = {
    "Flux-Midjourney-Mix2-LoRA": "Flux-Midjourney-Mix2-LoRA",
    "black-forest-labs/FLUX.1-dev": "black-forest-labs/FLUX.1-dev",
    "Stable Diffusion": "CompVis/stable-diffusion-v1-4"
}

st.set_page_config(page_title="Image Generator", layout="centered")
st.title("🖼️ HuggingFace Image Generator")

# Prompt input
prompt = st.text_input("Enter a prompt to generate an image:")

# Model selection
selected_model_label = st.selectbox("Choose a model:", list(model_options.keys()))
selected_model = model_options[selected_model_label]

# Generate button
if st.button("Generate Image") and prompt:
    with st.spinner("Generating image..."):
        # Request to HuggingFace Inference API
        headers = {"Authorization": f"Bearer {API_TOKEN}"}
        payload = {"inputs": prompt}
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{selected_model}",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            st.image(image, caption="Generated Image", use_column_width=True)

            # Download button
            img_buffer = BytesIO()
            image.save(img_buffer, format="PNG")
            st.download_button("Download Image", img_buffer.getvalue(), "generated_image.png", "image/png")
        else:
            st.error("Failed to generate image. Please check the model and prompt.")

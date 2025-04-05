import streamlit as st
import openai
import sys

# --- Version Check ---
required_openai_version = "1.3.8"

def version_warning(installed, required):
    st.warning(
        f"⚠️ Your installed OpenAI version is `{installed}`, but this app needs at least `{required}`.\n"
        f"Please update `requirements.txt` to use `openai>={required}` and redeploy."
    )

if openai.__version__ < required_openai_version:
    version_warning(openai.__version__, required_openai_version)
    st.stop()  # Stop app from continuing if version is too old
# -----------------------------
# Prompt Enhancer Logic
# -----------------------------
def enhance_prompt(role, context, task):
    return f"""
ROLE: {role}
CONTEXT: {context}
TASK: {task}

You must clarify any assumptions before starting. Once clarified, respond using the following format:

- Assumptions: [list them]
- Response: [your answer based on clarified assumptions]
""".strip()

# -----------------------------
# GPT Call (OpenAI ≥ 1.0.0)
# -----------------------------
def get_gpt_response(api_key, enhanced_prompt):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error: {str(e)}"

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🧠 Prompt Enhancer (Role, Context, Task)")

# Inputs
with st.form("prompt_form"):
    role = st.text_input("Enter the Role")
    context = st.text_area("Enter the Context")
    task = st.text_area("Enter the Task")
    api_key = st.text_input("Enter your OpenAI API Key", type="password")
    submitted = st.form_submit_button("Enhance Prompt")

# Initialize outputs
enhanced = None
response = None

# Process after form submit
if submitted:
    if not api_key:
        st.error("⚠️ Please enter your OpenAI API key.")
    elif not (role and context and task):
        st.warning("📝 Please fill out Role, Context, and Task.")
    else:
        enhanced = enhance_prompt(role, context, task)
        st.session_state["enhanced_prompt"] = enhanced
        st.session_state["api_key"] = api_key

# Display enhanced prompt (either from this session or prior)
if "enhanced_prompt" in st.session_state:
    st.subheader("🔧 Enhanced Prompt")
    st.code(st.session_state["enhanced_prompt"], language="markdown")

    if st.button("Ask GPT"):
        with st.spinner("Calling GPT..."):
            response = get_gpt_response(
                st.session_state["api_key"],
                st.session_state["enhanced_prompt"]
            )
        st.subheader("💡 GPT Response")
        st.write(response)

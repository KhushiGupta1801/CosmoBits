"""CosmoBits — Aerospace AI Assistant & Knowledge Chat Page."""
from __future__ import annotations

import os
import streamlit as st
from services.ai_service import get_configured_ai_provider, query_ai_assistant


def render_ai_assistant() -> None:
    """Render the AI aerospace mission control chat interface."""
    st.markdown("## 🤖 CosmoBits Mission Assistant")
    st.caption("Consult your AI specialist on orbital mechanics, satellite telemetry, Kessler Syndrome, and space weather.")

    provider, api_key = get_configured_ai_provider()

    # Provider & Setup Banner
    if provider:
        st.success(f"🟢 **Online AI Connected**: Active Engine: **{provider.upper()}** (API Key loaded from environment).")
    else:
        with st.expander("ℹ️ **AI API Configuration Guide (Optional)**", expanded=False):
            st.markdown(
                """
                CosmoBits is currently running in **Educational Offline Knowledge Mode**.
                You can ask questions about orbital mechanics, Keplerian elements, TLE formats, space weather, and the ISS.

                #### How to Enable Live Google Gemini AI:
                1. Get a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
                2. Set the environment variable in your terminal or in `.env`:
                   ```bash
                   export GEMINI_API_KEY="your_api_key_here"
                   ```
                   *Or create a `.env` file in the project folder with `GEMINI_API_KEY=your_key`.*
                3. Restart the Streamlit application.
                """
            )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Greetings! I am **CosmoBits**, your aerospace mission assistant. "
                    "Ask me anything about orbital mechanics, satellite constellations, "
                    "solar weather impacts, or space debris mitigation."
                ),
            }
        ]

    # Quick suggestion buttons
    st.markdown("##### 💡 Suggested Questions:")
    q_cols = st.columns(4)
    suggested = [
        "What is a Sun-Synchronous Orbit (SSO)?",
        "Explain Keplerian orbital elements.",
        "How do solar storms affect satellite drag?",
        "What is the Kessler Syndrome & debris risk?",
    ]

    selected_prompt = None
    for i, q in enumerate(suggested):
        with q_cols[i]:
            if st.button(q, key=f"sug_{i}"):
                selected_prompt = q

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    user_input = st.chat_input("Ask a question about space, orbits, or satellites...") or selected_prompt

    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing telemetry & orbital principles..."):
                response_text, provider_label = query_ai_assistant(user_input, st.session_state.messages)
                st.markdown(response_text)
                st.caption(f"Engine: *{provider_label}*")

        st.session_state.messages.append({"role": "assistant", "content": response_text})

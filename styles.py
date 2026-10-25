"""Cosmo Bites — CSS Injection & UI Theming Utility."""
from __future__ import annotations

from pathlib import Path
import streamlit as st


def inject_custom_css() -> None:
    """Inject the custom cyber-space glassmorphism CSS into the Streamlit session."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
    if css_path.exists():
        css_content = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp { background-color: #050811; color: #F1F5F9; }</style>", unsafe_allow_html=True)

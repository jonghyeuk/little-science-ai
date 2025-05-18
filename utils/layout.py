# utils/layout.py

import streamlit as st

def render_title(title: str):
    st.markdown(f"""
    <div style='margin: 40px 60px; font-family: "Nanum Gothic", sans-serif;'>
    <h2 style='font-size: 26px; font-weight: bold;'>🔬 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_paragraph(text: str):
    st.markdown(f"""
    <div style='margin: 0px 60px; font-family: "Nanum Gothic", sans-serif; line-height: 1.8; font-size: 16px;'>
    {text}
    </div>
    """, unsafe_allow_html=True)

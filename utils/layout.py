# utils/layout.py

import streamlit as st

def load_css():
    """커스텀 CSS 불러오기"""
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("❗ CSS 파일을 찾을 수 없습니다.")

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

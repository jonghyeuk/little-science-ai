import streamlit as st
import os

def load_css():
    css_path = os.path.join("assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_title(title: str):
    st.markdown(f"""
    <div class="title-section">
        <h2>🔬 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_paragraph(text: str):
    st.markdown(f"""
    <div class="text-block">{text}</div>
    """, unsafe_allow_html=True)

def render_paper_card(title: str, meta: str, summary: str, link: str = None):
    link_html = f"<div class='paper-link'>🔗 <a href='{link}' target='_blank'>논문 링크 보기</a></div>" if link else ""
    st.markdown(f"""
    <div class="paper-card">
        <div class="paper-title">{title}</div>
        <div class="paper-meta">{meta}</div>
        <div class="paper-summary">{summary}</div>
        {link_html}
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
import os

# ✅ 1. CSS 파일 로딩 함수
def load_css():
    """assets/styles.css 파일을 읽어 Streamlit에 삽입"""
    css_path = os.path.join("assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"❗ CSS 파일을 찾을 수 없습니다: {css_path}")

# ✅ 2. 페이지 제목 렌더링
def render_title(title: str):
    """페이지 상단 제목 블록"""
    st.markdown(f"""
    <div class="title-section">
        <h2>🔬 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

# ✅ 3. 일반 문단 출력
def render_paragraph(text: str):
    """문단 블록 출력"""
    st.markdown(f"""
    <div class="text-block">
        {text}
    </div>
    """, unsafe_allow_html=True)

# ✅ 4. 논문 카드 출력 (내부 DB / arXiv 공통)
def render_paper_card(title: str, meta: str, summary: str, link: str = None):
    """논문 스타일 카드 렌더링"""
    link_html = f"<div class='paper-link'>🔗 <a href='{link}' target='_blank'>논문 링크 보기</a></div>" if link else ""
    st.markdown(f"""
    <div class="paper-card">
        <div class="paper-title">{title}</div>
        <div class="paper-meta">{meta}</div>
        <div class="paper-summary">{summary}</div>
        {link_html}
    </div>
    """, unsafe_allow_html=True)


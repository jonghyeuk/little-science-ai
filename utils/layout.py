import streamlit as st
import os

def load_css():
    """assets/styles.css 파일에서 커스텀 CSS 불러오기"""
    css_path = os.path.join("assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    else:
        st.warning(f"❗ CSS 파일을 찾을 수 없습니다: {css_path}")

def render_title(title: str):
    """페이지 메인 타이틀 (가운데 정렬, 강조 스타일 적용됨)"""
    st.markdown(f"""
    <div class="title-section">
        <h2>🔬 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_paragraph(text: str):
    """일반 텍스트 문단 출력"""
    st.markdown(f"""
    <div class="text-block">
        {text}
    </div>
    """, unsafe_allow_html=True)

def render_paper_card(title: str, meta: str, summary: str, link: str = None):
    """논문 카드형 UI 렌더링 (내부 논문 / arXiv 통합 포맷)"""
    link_html = f"<div class='paper-link'>🔗 <a href='{link}' target='_blank'>논문 링크 보기</a></div>" if link else ""
    
    st.markdown(f"""
    <div class="paper-card">
        <div class="paper-title">{title}</div>
        <div class="paper-meta">{meta}</div>
        <div class="paper-summary">{summary}</div>
        {link_html}
    </div>
    """, unsafe_allow_html=True)


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

def render_paper_card(title, meta, summary, link=None):
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

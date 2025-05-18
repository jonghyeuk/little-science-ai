import streamlit as st

def load_css():
    """커스텀 CSS 불러오기"""
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("❗ CSS 파일을 찾을 수 없습니다.")
        st.markdown("<style>body { font-family: sans-serif; }</style>", unsafe_allow_html=True)

def render_title(title: str):
    """중앙 정렬 타이틀"""
    st.markdown(f"""
    <div style='max-width:800px; margin: 40px auto 20px auto; font-family: "Nanum Gothic", sans-serif; text-align: center;'>
        <h2 style='font-size: 26px; font-weight: bold;'>🔬 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_paragraph(text: str):
    """본문 문단 렌더링 (A4 폭 안 맞추면 한쪽으로 쏠림)"""
    st.markdown(f"""
    <div style='max-width:800px; margin: 0 auto 1.5rem auto; font-family: "Nanum Gothic", sans-serif; line-height: 1.8; font-size: 16px; text-align: justify;'>
        {text}
    </div>
    """, unsafe_allow_html=True)

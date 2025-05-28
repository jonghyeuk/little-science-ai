import anthropic
import streamlit as st
import re

# DOI 링크 변환 함수 추가 (app.py에서도 사용 가능하도록)
def convert_doi_to_links(text):
    """DOI 패턴을 감지하여 클릭 가능한 링크로 변환"""
    # 다양한 DOI 패턴 인식
    doi_pattern = r'(?:DOI\s*:?\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
    
    # HTML 링크로 변환
    def replace_doi(match):
        doi = match.group(1)
        return f'<a href="https://doi.org/{doi}" target="_blank" style="color: #0969da; text-decoration: underline;">{doi}</a>'
    
    # 텍스트 내 DOI 패턴을 링크로 변환
    linked_text = re.sub(doi_pattern, replace_doi, text)
    
    return linked_text

@st.cache_data(show_spinner="🤖 AI 설명을 생성 중입니다...", ttl=3600)
def explain_topic(topic: str) -> list:
    """Claude 기반 주제 설명 생성 (문단 단위 리스트 반환)"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
    except KeyError:
        st.error("❌ Claude API 키가 설정되지 않았습니다.")
        st.stop()
    
    system_prompt = """
    너는 'LittleScienceAI 도우미'로, 고등학생에게 과학 주제를 쉽고 재미있게 설명하는 친근한 전문가야.
    각 섹션을 자연스러운 문장으로 풍부하게 설명하되, 읽으면서 "아, 이해됐다!"라는 느낌이 들도록 써줘.
    **다음 구조로 작성하되, 각 섹션은 자연스러운 문단 형태로 풍부하게 설명해:**
    ## 🔬 **개념 정의**
    주제가 무엇인지 쉽고 명확하게 설명해줘. 마치 친구에게 설명하듯이 친근하게 시작하고, 전문 용어가 나오면 바로 쉬운 말로 풀어서 설명해. 일상생활에서 볼 수 있는 비유나 예시를 들어서 "아, 그런 거구나!"라

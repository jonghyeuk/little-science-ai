from openai import OpenAI
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
    """GPT-4 기반 주제 설명 생성 (문단 단위 리스트 반환)"""
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
    except KeyError:
        st.error("❌ OpenAI API 키가 설정되지 않았습니다.")
        st.stop()
    system_prompt = """
    너는 'LittleScienceAI 도우미'라는 AI로,
    고등학생 또는 청소년 연구자에게 과학 주제를 친절하고 정확하게 설명하는 역할을 해.
    아래의 형식과 원칙을 따라 설명해줘:
    1. 개념 정의
    2. 작동 원리
    3. 현재 과학적/사회적 배경
    4. 응용 사례 및 분야
    5. 관련 논문 제목과 출처(가능한 DOI 또는 링크 포함)
    6. 확장 가능한 탐구 아이디어 제안
    ✅ 반드시 지킬 것:
    - 설명은 중립적이고 교육적 톤으로, 고등학생 눈높이에 맞게
    - 문단별로 구분하고, 각 섹션의 제목은 굵은 글씨로
    - 논문 인용은 절대 금지이며, 생성된 내용은 'AI의 추론'임을 명시
    - 설명은 한국어로
    """
    user_prompt = f"주제: {topic}"
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        full_text = response.choices[0].message.content
        paragraphs = full_text.strip().split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    except Exception as e:
        st.error(f"❌ GPT 설명 중 오류 발생: {e}")
        return ["AI 설명을 생성할 수 없습니다."]

# 직접 링크가 포함된 설명 생성 (앱에서 선택적 사용 가능)
def explain_topic_with_links(topic: str) -> str:
    """DOI 링크가 자동 변환된 주제 설명 생성"""
    explanation_lines = explain_topic(topic)
    explanation_text = "\n\n".join(explanation_lines)
    return convert_doi_to_links(explanation_text)

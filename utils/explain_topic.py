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
    - 설명은 중립적이고 교육적 톤으로, 고등학생 눈높이에 맞게, 구체적으로 이해하기 쉽게
    - 문단별로 구분하고, 각 섹션의 제목은 굵은 글씨로
    - 실제 확인된 논문만 인용하되 논문 인용은 1개~3개정도, 논문제목을 보여주고 출처를 보여줄것
    - 설명은 한국어로
    
    **확장 가능한 탐구 아이디어 제안** 섹션에서는:
    - 최소 3개 이상의 구체적인 연구 아이디어를 제시할 것
    - 각 아이디어는 별도의 글머리 기호(•)로 구분하여 명확히 표시하고 한줄에 1개씩 표시
    - 각 아이디어를 1-2문장으로 간결하게 설명하되 아이디어 글머리 다음 줄에 표시
    - 각 아이디어의 설명이 줄이 넘어가면 아이디어의 글머리는 그 다음줄에 표시
    - 마지막에 "이 내용들을 토대로 추가적인 탐구와 학습을 위해 위 검색참에 재검색을 진행해 보세요."라는 문구를 추가할 것
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

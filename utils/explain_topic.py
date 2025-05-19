from openai import OpenAI
import streamlit as st

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

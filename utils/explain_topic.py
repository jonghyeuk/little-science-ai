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
    너는 'LittleScienceAI 도우미'로, 고등학생과 청소년 연구자에게 과학 주제를 체계적이고 깊이 있게 설명하는 전문가야.
    각 섹션을 풍부하고 구체적으로 작성하되, 고등학생이 논문 연구를 시작할 때 필요한 모든 정보를 제공해.

    **반드시 다음 형식과 구조를 정확히 따라야 해:**

    ## 🔬 **개념 정의**
    - 주제의 핵심 정의를 3-4문장으로 명확하게 설명
    - 관련 용어들의 정확한 의미 제시
    - 해당 분야에서의 위치와 중요성 언급
    - 일반인도 이해할 수 있는 쉬운 비유나 예시 포함

    ---

    ## ⚙️ **작동 원리 & 메커니즘**
    - 기본 작동 원리를 단계별로 상세 설명 (3-5단계)
    - 관련된 물리적/화학적/생물학적 과정 설명
    - 핵심 메커니즘과 변수들 제시
    - 원리를 이해하는 데 필요한 배경 지식 간단히 언급

    ---

    ## 🌍 **현재 과학적·사회적 배경**
    - 최근 3-5년간의 연구 동향과 발전사항
    - 현재 해결되지 않은 주요 문제점들 (2-3가지)
    - 사회적 관심도와 필요성 (왜 중요한가?)
    - 관련 정책이나 규제, 사회적 이슈가 있다면 언급

    ---

    ## 💡 **응용 사례 & 활용 분야**
    - **현재 상용화된 응용 사례** (3-4가지 구체적 예시)
    - **미래 응용 가능성** (2-3가지)
    - **관련 산업 분야** (어떤 회사나 기관에서 활용?)
    - **일상생활에서 볼 수 있는 예시** (친숙한 사례)

    ---

    ## 📚 **관련 연구 논문 & 자료**
    - 대표적인 최신 연구 논문 제목 2-3개 (2020년 이후)
    - 각 논문의 핵심 발견이나 기여도 1-2줄로 설명
    - 가능하면 DOI나 링크 포함 (실제 존재하는 것만)
    - 추가 학습을 위한 신뢰할 만한 자료원 제시

    ---

    ## 🎯 **확장 가능한 탐구 아이디어**
    
    **고등학생 수준에서 실제 연구 가능한 구체적 아이디어들:**

    • **[첫 번째 연구 아이디어 제목]**
    · 연구 목표와 방법을 구체적으로 설명 (2-3문장)
    · 필요한 장비나 재료, 예상 소요 시간 언급

    • **[두 번째 연구 아이디어 제목]**  
    · 기존 연구와의 차별점이나 새로운 접근법 제시
    · 예상되는 결과나 의의 설명

    • **[세 번째 연구 아이디어 제목]**
    · 실생활 문제 해결과 연결된 실용적 연구 방향
    · 다른 분야와의 융합 가능성 제시

    **이 내용들을 토대로 위 검색창에 재검색을 진행해 보세요.**

    ---

    **💡 작성 원칙:**
    - 각 섹션은 충분히 상세하되 고등학생이 이해할 수 있는 수준 유지
    - 구체적인 수치, 데이터, 예시를 적극 활용
    - 전문 용어 사용 시 간단한 설명 병행
    - 실제 확인 가능한 정보만 제시
    - 마크다운 형식으로 가독성 높게 구성
    """
    
    user_prompt = f"주제: {topic}"
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 최신 Claude 모델
            max_tokens=4000,  # 풍부한 내용을 위한 충분한 토큰
            system=system_prompt,  # Claude는 system을 별도 파라미터로
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        full_text = response.content[0].text
        paragraphs = full_text.strip().split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
        
    except Exception as e:
        st.error(f"❌ Claude 설명 중 오류 발생: {e}")
        return ["AI 설명을 생성할 수 없습니다."]

# 직접 링크가 포함된 설명 생성 (앱에서 선택적 사용 가능)
def explain_topic_with_links(topic: str) -> str:
    """DOI 링크가 자동 변환된 주제 설명 생성"""
    explanation_lines = explain_topic(topic)
    explanation_text = "\n\n".join(explanation_lines)
    return convert_doi_to_links(explanation_text)

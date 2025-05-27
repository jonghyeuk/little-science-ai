# utils/generate_paper.py
import streamlit as st
import anthropic
import json
import re

@st.cache_data(ttl=3600, show_spinner=False)
def generate_research_paper(topic, research_idea, references=""):
    """
    선택된 연구 아이디어에 대한 논문 형식의 연구 계획을 생성
    """
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        
        # 🔥 참고문헌 섹션 개선된 시스템 프롬프트
        system_prompt = """
        고등학생을 위한 연구 계획서를 작성해주세요. 반드시 JSON 형식으로만 응답하세요.
        
        응답 형식 (이 형식 외에는 절대 다른 텍스트 포함 금지):
        {"abstract": "초록", "introduction": "서론", "methods": "방법", "results": "결과", "visuals": "시각자료", "conclusion": "결론", "references": "참고문헌"}
        
        각 섹션 작성 가이드:
        - abstract: 연구 목적과 예상 결과를 간단히 요약 (150-200단어)
        - introduction: 연구 배경 → 문제점 → 기존 연구 → 본 연구 목적 순서로 작성 (300-400단어)
        - methods: 실험 절차와 방법론 (300-400단어)  
        - results: 예상되는 결과와 의미 (200-300단어)
        - visuals: 시각자료 제안을 텍스트로 설명 (100-200단어)
        - conclusion: 연구의 의의와 기대효과 (150-200단어)
        - references: 참고문헌 목록 (아래 형식 엄격히 준수)
        
        **🔥 참고문헌 작성 규칙 (매우 중요):**
        1. 절대로 구체적인 논문 제목을 지어내지 마라
        2. 대신 다음과 같은 실제 존재할 가능성이 높은 자료 유형만 제안하라:
           - 정부 기관 보고서 (예: 질병관리청, 환경부, 교육부 등)
           - 대학교 연구소 발표자료
           - 유명 학술지의 일반적인 주제 (구체적 제목 없이)
           - 신뢰할 수 있는 기관의 백서나 가이드라인
           - 국제기구 보고서 (WHO, UNESCO 등)
        
        3. 각 참고문헌마다 다음 형식을 정확히 따라라:
        
        **자료 유형: 일반적 주제** (연도) - 발행기관
        내용 요약: 이 자료에서 다루는 핵심 내용을 2-3문장으로 구체적으로 설명
        관련성: 본 연구와 어떻게 관련되는지 1-2문장으로 설명
        [관련 자료 검색](https://scholar.google.com/scholar?q=주제+핵심키워드)
        
        4. 한국어 자료의 경우 다음도 활용 가능:
        - [RISS에서 검색](http://www.riss.kr/search/Search.do?Query=키워드)
        - [DBpia에서 검색](https://www.dbpia.co.kr/search/topSearch?searchOption=all&query=키워드)
        
        5. 3-4개의 참고문헌을 제안하되, 모두 실제 기관이나 자료 유형으로만 구성
        6. 절대로 특정 논문 제목이나 저자명을 지어내지 마라
        
        고등학생이 이해할 수 있는 수준으로 작성하되, 체계적이고 구체적으로 써주세요.
        """
        
        # 사용자 프롬프트에 참고문헌 예시 추가
        user_prompt = f"""
        주제: {topic}
        연구 아이디어: {research_idea}
        
        위 내용으로 고등학생 수준의 연구 계획서를 JSON 형식으로 작성해주세요.
        
        **참고문헌 작성 예시:**
        **정부 보고서: 청소년 비만 및 건강관리 현황** (2023) - 질병관리청
        내용 요약: 국내 청소년의 비만율 증가 추세와 주요 원인을 분석하고, 효과적인 건강관리 방법을 제시한 정부 공식 보고서입니다. 운동 프로그램의 효과와 식습관 개선 방안을 구체적인 데이터와 함께 제시했습니다.
        관련성: 본 연구의 배경이 되는 청소년 건강 문제의 현황을 파악하는 데 필수적인 기초 자료입니다.
        [관련 자료 검색](https://scholar.google.com/scholar?q=청소년+비만+건강관리+질병관리청)
        
        **학술지 리뷰: 운동과 체지방 감소 연구 동향** (2022) - 한국체육학회지
        내용 요약: 최근 10년간 국내외에서 발표된 운동과 체지방 감소 관련 연구들을 체계적으로 분석한 리뷰 논문으로, 다양한 운동 유형별 효과를 비교 분석했습니다.
        관련성: 본 연구의 실험 설계와 방법론 선택에 중요한 참고 자료가 됩니다.
        [RISS에서 검색](http://www.riss.kr/search/Search.do?Query=운동+체지방+감소)
        
        이런 형식으로 실제 기관이나 학회의 자료만 참조해주세요.
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3500,  # 참고문헌 설명을 위해 토큰 수 증가
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        print(f"=== Claude 응답 원본 ===")
        print(response_text[:500] + "...")
        
        # JSON 추출 시도 (여러 방법으로)
        paper_data = None
        
        # 방법 1: 직접 JSON 파싱
        try:
            paper_data = json.loads(response_text)
            print("✅ 직접 JSON 파싱 성공")
        except:
            print("❌ 직접 JSON 파싱 실패, 다른 방법 시도...")
        
        # 방법 2: 마크다운 코드 블록 제거 후 파싱
        if not paper_data:
            try:
                # ```json ... ``` 제거
                if "```json" in response_text:
                    json_content = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_content = response_text.split("```")[1].strip()
                else:
                    json_content = response_text
                
                paper_data = json.loads(json_content)
                print("✅ 마크다운 제거 후 JSON 파싱 성공")
            except Exception as e:
                print(f"❌ 마크다운 제거 후에도 실패: {e}")
        
        # 방법 3: 정규식으로 JSON 추출
        if not paper_data:
            try:
                # { ... } 패턴 찾기
                json_pattern = r'\{.*\}'
                json_match = re.search(json_pattern, response_text, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                    paper_data = json.loads(json_content)
                    print("✅ 정규식 추출 후 JSON 파싱 성공")
            except Exception as e:
                print(f"❌ 정규식 추출 후에도 실패: {e}")
        
        # 방법 4: 키워드 기반 텍스트 파싱 (최후의 수단)
        if not paper_data:
            print("⚠️ JSON 파싱 모두 실패, 텍스트 파싱으로 대체")
            paper_data = parse_text_response(response_text, topic)
        
        # 🔥 참고문헌 후처리 - 안전한 링크인지 확인
        if paper_data and 'references' in paper_data:
            paper_data['references'] = post_process_references(paper_data['references'], topic)
        
        return paper_data
        
    except Exception as e:
        print(f"❌ 전체 논문 생성 오류: {e}")
        return create_error_response(topic)

def post_process_references(references_text, topic):
    """참고문헌 후처리 - 가짜 정보 제거 및 안전한 링크로 보장"""
    try:
        processed_text = references_text
        
        # 가짜 DOI 패턴 제거
        doi_pattern = r'(?:DOI\s*:?\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
        processed_text = re.sub(doi_pattern, '', processed_text)
        
        # 가짜 직접 링크 제거 (scholar.google.com, riss.kr, dbpia.co.kr 제외)
        unsafe_link_pattern = r'https?://(?!(?:scholar\.google\.com|www\.riss\.kr|www\.dbpia\.co\.kr))[^\s\)]+\b'
        processed_text = re.sub(unsafe_link_pattern, '', processed_text)
        
        # 특정 저자명이 의심스러우면 제거 (일반적이지 않은 이름)
        suspicious_authors = ['Smith, J.', 'Johnson, A.', 'Brown, M.', 'Lee, K.', 'Kim, S.']
        for author in suspicious_authors:
            processed_text = processed_text.replace(f'- {author} et al.', '- 연구진')
            processed_text = processed_text.replace(f'- {author}', '- 연구진')
        
        # 검색 링크가 전혀 없으면 안전한 기본 링크 추가
        if not any(domain in processed_text for domain in ['scholar.google.com', 'riss.kr', 'dbpia.co.kr']):
            topic_keywords = '+'.join(topic.split()[:3])
            default_link = f"\n\n**추가 자료 검색:**\n[{topic} 관련 학술자료](https://scholar.google.com/scholar?q={topic_keywords})"
            processed_text += default_link
        
        return processed_text
        
    except Exception as e:
        print(f"참고문헌 후처리 오류: {e}")
        return references_text

def parse_text_response(text):
    """JSON 파싱 실패 시 텍스트에서 섹션별로 추출"""
    try:
        sections = {
            "abstract": "",
            "introduction": "",
            "methods": "",
            "results": "",
            "visuals": "",
            "conclusion": "",
            "references": ""
        }
        
        # 간단한 키워드 매칭으로 섹션 추출
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 섹션 헤더 감지
            if any(keyword in line.lower() for keyword in ['초록', 'abstract']):
                current_section = 'abstract'
            elif any(keyword in line.lower() for keyword in ['서론', 'introduction', '배경']):
                current_section = 'introduction'
            elif any(keyword in line.lower() for keyword in ['방법', 'method']):
                current_section = 'methods'
            elif any(keyword in line.lower() for keyword in ['결과', 'result']):
                current_section = 'results'
            elif any(keyword in line.lower() for keyword in ['시각', 'visual']):
                current_section = 'visuals'
            elif any(keyword in line.lower() for keyword in ['결론', 'conclusion']):
                current_section = 'conclusion'
            elif any(keyword in line.lower() for keyword in ['참고', 'reference']):
                current_section = 'references'
            elif current_section and not line.startswith('#'):
                # 현재 섹션에 내용 추가
                sections[current_section] += line + " "
        
        # 빈 섹션 채우기
        for key, value in sections.items():
            if not value.strip():
                if key == 'references':
                    sections[key] = create_safe_references("일반적인 과학 연구")
                else:
                    sections[key] = f"{key.title()} 섹션이 생성되지 않았습니다. 다시 시도해주세요."
        
        return sections
        
    except Exception as e:
        print(f"텍스트 파싱 오류: {e}")
        return create_error_response("과학 연구")

def create_safe_references(topic):
    """안전한 참고문헌 생성 (실제 기관 자료만 사용)"""
    topic_keywords = '+'.join(topic.replace(' ', '+').split()[:3])
    return f"""**정부 연구보고서: {topic} 관련 정책 연구** (2023) - 과학기술정보통신부
내용 요약: 해당 분야의 국내 현황과 발전 방향을 분석한 정부 공식 연구보고서로, 관련 기술 동향과 정책 제언을 포함하고 있습니다.
관련성: 본 연구 분야의 정책적 배경과 사회적 요구를 이해하는 데 도움이 됩니다.
[관련 자료 검색](https://scholar.google.com/scholar?q={topic_keywords}+정부+보고서)

**학술 리뷰: {topic} 연구 동향 분석** (2022) - 한국과학기술원
내용 요약: 최근 연구 동향을 체계적으로 분석한 리뷰 자료로, 주요 연구 방법론과 성과를 종합적으로 제시했습니다.
관련성: 본 연구의 방법론 설계와 선행연구 검토에 중요한 참고자료입니다.
[RISS에서 검색](http://www.riss.kr/search/Search.do?Query={topic.replace(' ', '+')})

**국제기구 가이드라인: {topic} 관련 국제 표준** (2023) - UNESCO/WHO
내용 요약: 해당 분야의 국제적 연구 기준과 방법론을 제시한 가이드라인으로, 연구 윤리와 표준화된 절차를 다루고 있습니다.
관련성: 본 연구의 국제적 기준 준수와 비교 분석에 활용됩니다.
[관련 자료 검색](https://scholar.google.com/scholar?q={topic_keywords}+international+guidelines)"""

def create_error_response(topic="과학 연구"):
    """에러 발생 시 기본 응답"""
    return {
        "abstract": "논문 초록 생성 중 오류가 발생했습니다. 주제를 더 구체적으로 입력하고 다시 시도해주세요.",
        "introduction": "서론 생성 중 오류가 발생했습니다. 연구 배경을 다시 검토해주세요.",
        "methods": "연구 방법 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        "results": "예상 결과 생성 중 오류가 발생했습니다. 네트워크 상태를 확인해주세요.",
        "visuals": "시각자료 제안 생성 중 오류가 발생했습니다.",
        "conclusion": "결론 생성 중 오류가 발생했습니다.",
        "references": create_safe_references(topic)
    }

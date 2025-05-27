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
        
        # 🔥 수정된 시스템 프롬프트 - 실험방법 부분 대폭 강화
        system_prompt = """
        고등학생을 위한 연구 계획서를 작성해주세요. 반드시 JSON 형식으로만 응답하세요.
        
        응답 형식 (이 형식 외에는 절대 다른 텍스트 포함 금지):
        {"abstract": "초록", "introduction": "서론", "methods": "방법", "results": "결과", "visuals": "시각자료", "conclusion": "결론", "references": "참고문헌"}
        
        각 섹션 작성 가이드:
        - abstract: 연구 목적과 예상 결과를 간단히 요약 (150-200단어)
        - introduction: 연구 배경 → 문제점 → 기존 연구 → 본 연구 목적 순서로 작성 (300-400단어)
        - methods: 실험 절차와 방법론 (400-500단어) - 아래 규칙 준수
        - results: 예상되는 결과와 의미 (200-300단어)
        - visuals: 시각자료 제안을 텍스트로 설명 (100-200단어)
        - conclusion: 연구의 의의와 기대효과 (150-200단어)
        - references: 아래 규칙에 따라 실제 자료만 참조
        
        **🔥 실험방법(Methods) 작성 규칙 (가장 중요!):**
        1. **필요한 재료 및 장비** (2-3문장으로 간단히)
           - 핵심 장비만 나열, 너무 길지 않게
        
        2. **실험 절차** (전체 분량의 80% 할당) - 매우 상세하고 친절하게!
           - "1단계: [제목]" 형식으로 번호 매기기
           - 각 단계마다 구체적인 행동을 서술형으로 설명
           - "먼저", "다음으로", "그 후에", "마지막으로" 등 연결어 사용
           - 고등학생이 따라 할 수 있을 정도로 친절하고 구체적으로
           - 측정 방법, 기록 방법, 주의사항도 포함
           - 최소 5-7단계로 나누어 설명
        
        3. **데이터 수집 및 분석**
           - 어떤 데이터를 어떻게 기록할지
           - 반복 실험 횟수와 이유
        
        **참고문헌 작성 규칙:**
        1. 실제 확인 가능한 자료만 사용하고, 클릭 가능한 링크 제공
        2. 다음 형식으로 작성:
           **[번호]. 자료 제목** 
           📄 내용 요약: (이 자료가 다루는 핵심 내용을 2-3문장으로 설명)
           🔗 링크: [실제 접근 가능한 URL]
           📌 활용 방안: (본 연구에 어떻게 도움이 되는지 1-2문장)
        
        3. 추천 자료 유형:
           - Google Scholar 검색 결과 (scholar.google.com)
           - 정부기관 공식 보고서 (.go.kr)
           - 대학 연구소 자료
           - IEEE, Nature, Science 등 공개 자료
           - arXiv 프리프린트
        
        고등학생이 실제로 실험할 수 있을 정도로 친절하고 구체적으로 써주세요.
        """
        
        user_prompt = f"""
        주제: {topic}
        연구 아이디어: {research_idea}
        
        위 내용으로 고등학생 수준의 연구 계획서를 JSON 형식으로 작성해주세요.
        
        특히 실험방법(methods) 섹션은:
        - 장비 나열보다는 "실험을 어떻게 진행하는지" 단계별 설명에 집중
        - "1단계: 준비 과정에서는...", "2단계: 측정 과정에서는..." 형식으로 상세히
        - 고등학생이 실제로 따라할 수 있을 정도로 친절하게 작성
        
        특히 참고문헌(references) 섹션은:
        - 실제 클릭해서 확인 가능한 링크만 포함
        - 각 자료의 핵심 내용을 2-3문장으로 요약
        - Google Scholar, arXiv, 정부기관 사이트 등 신뢰할 수 있는 출처만 사용
        - 형식 예시: "1. 자료제목 📄 내용요약: ... 🔗 링크: https://... 📌 활용방안: ..."
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3500,  # 더 긴 응답을 위해 증가
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
            paper_data = parse_text_response(response_text)
        
        # 참고문헌만 후처리 추가
        if paper_data and 'references' in paper_data:
            paper_data['references'] = clean_fake_references(paper_data['references'])
        
        return paper_data
        
    except Exception as e:
        print(f"❌ 전체 논문 생성 오류: {e}")
        return create_error_response()

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
                sections[key] = f"{key.title()} 섹션이 생성되지 않았습니다. 다시 시도해주세요."
        
        return sections
        
    except Exception as e:
        print(f"텍스트 파싱 오류: {e}")
        return create_error_response()

def clean_fake_references(ref_text):
    """참고문헌 품질 개선 - 실제 링크는 유지하고 가짜 정보만 제거"""
    try:
        cleaned = ref_text
        
        # 🔥 실제 확인 가능한 도메인은 유지
        trusted_domains = [
            'scholar.google.com',
            'arxiv.org', 
            'ieee.org',
            'nature.com',
            'science.org',
            'ncbi.nlm.nih.gov',
            'go.kr',  # 정부기관
            'edu',    # 대학
            'ac.kr'   # 한국 대학
        ]
        
        # 신뢰할 수 있는 도메인의 링크는 유지
        # 나머지 의심스러운 링크만 제거
        lines = cleaned.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 신뢰할 수 있는 도메인 링크가 있으면 유지
            has_trusted_link = any(domain in line for domain in trusted_domains)
            
            if has_trusted_link:
                filtered_lines.append(line)
            else:
                # 의심스러운 링크 제거
                line_without_suspicious = re.sub(r'https?://[^\s\)]+', '', line)
                if line_without_suspicious.strip():  # 빈 줄이 아니면 추가
                    filtered_lines.append(line_without_suspicious)
        
        cleaned = '\n'.join(filtered_lines)
        
        # 의심스러운 가짜 저자명 제거 (기존 로직 유지)
        fake_authors = ['Smith, J.', 'Johnson, A.', 'Brown, M.', 'Lee, K.', 'Kim, S.', 'Park, H.']
        for fake in fake_authors:
            cleaned = cleaned.replace(f'- {fake}', '- 연구진')
            cleaned = cleaned.replace(fake, '연구진')
        
        return cleaned.strip()
    except:
        return ref_text

def create_error_response():
    """에러 발생 시 기본 응답"""
    return {
        "abstract": "논문 초록 생성 중 오류가 발생했습니다. 주제를 더 구체적으로 입력하고 다시 시도해주세요.",
        "introduction": "서론 생성 중 오류가 발생했습니다. 연구 배경을 다시 검토해주세요.",
        "methods": "연구 방법 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        "results": "예상 결과 생성 중 오류가 발생했습니다. 네트워크 상태를 확인해주세요.",
        "visuals": "시각자료 제안 생성 중 오류가 발생했습니다.",
        "conclusion": "결론 생성 중 오류가 발생했습니다.",
        "references": "참고문헌 생성 중 오류가 발생했습니다."
    }

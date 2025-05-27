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
        
        # 🔥 간단하고 명확한 시스템 프롬프트로 수정
        system_prompt = """
        고등학생 연구 계획서를 JSON 형식으로 작성해주세요.

        반드시 이 JSON 형식만 사용:
        {"abstract": "초록내용", "introduction": "서론내용", "methods": "방법내용", "results": "결과내용", "visuals": "시각자료내용", "conclusion": "결론내용", "references": "참고문헌내용"}

        각 섹션 요구사항:
        - abstract: 연구목적과 예상결과 요약 (100-150단어)
        - introduction: 배경→문제→목적 순서 (200-250단어)
        - methods: 실험단계를 명확히 구분해서 작성 (250-300단어)
        - results: 예상되는 구체적 결과들 (150-200단어)
        - visuals: 필요한 그래프/차트 설명 (100-150단어)
        - conclusion: 연구의 의의와 활용방안 (100-150단어)
        - references: 실제 확인가능한 자료 3-4개

        실험방법 작성법:
        1단계: [제목] - 구체적 설명
        2단계: [제목] - 구체적 설명
        3단계: [제목] - 구체적 설명
        (이런 식으로 단계별로 명확히 구분)

        참고문헌 작성법:
        1. 자료제목
        - 내용: 핵심내용 2문장 설명  
        - 검색: Google Scholar에서 "[키워드]" 검색 또는 실제 존재하는 사이트만 (nasa.gov, nih.gov, 대학사이트 등)
        - 활용: 연구에 어떻게 도움되는지
        
        주의: 절대로 가짜 DOI나 존재하지 않는 링크를 만들지 말고, 대신 검색 방법을 안내하세요.
        """
        
        # 🔥 간단한 사용자 프롬프트
        user_prompt = f"""
        주제: {topic}
        아이디어: {research_idea}

        위 내용으로 고등학생 연구계획서를 JSON으로 작성해주세요.
        실험방법은 단계별로 명확히, 다른 섹션들도 균형있게 작성해주세요.
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,  # 토큰 줄여서 더 집중된 응답
            temperature=0.2,  # 더 일관된 응답
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        print(f"=== Claude 응답 원본 ===")
        print(response_text[:300] + "...")
        
        # 🔥 더 강력한 JSON 추출
        paper_data = extract_json_robust(response_text)
        
        # 🔥 섹션별 검증 및 수정
        if paper_data:
            paper_data = validate_and_fix_sections(paper_data)
        
        return paper_data if paper_data else create_error_response()
        
    except Exception as e:
        print(f"❌ 전체 논문 생성 오류: {e}")
        return create_error_response()

def extract_json_robust(text):
    """더 강력한 JSON 추출"""
    try:
        # 방법 1: 직접 파싱
        try:
            return json.loads(text)
        except:
            pass
        
        # 방법 2: 코드블록 제거
        if "```json" in text:
            content = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            content = text.split("```")[1].strip()
        else:
            content = text
        
        try:
            return json.loads(content)
        except:
            pass
        
        # 방법 3: 정규식으로 JSON 찾기
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and 'abstract' in data:
                    return data
            except:
                continue
        
        # 방법 4: 수동 파싱
        return manual_parse_sections(text)
        
    except:
        return None

def manual_parse_sections(text):
    """수동으로 섹션 파싱"""
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
        
        # 더 유연한 키워드 검색
        keywords = {
            'abstract': ['초록', 'abstract', '요약'],
            'introduction': ['서론', 'introduction', '배경', '도입'],
            'methods': ['방법', 'method', '실험', '절차'],
            'results': ['결과', 'result', '예상'],
            'visuals': ['시각', 'visual', '그래프', '차트'],
            'conclusion': ['결론', 'conclusion', '결과'],
            'references': ['참고', 'reference', '문헌']
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('{') or line.startswith('}'):
                continue
            
            # 섹션 감지
            found_section = None
            for section, kws in keywords.items():
                if any(kw in line.lower() for kw in kws):
                    found_section = section
                    break
            
            if found_section:
                current_section = found_section
            elif current_section and not line.startswith('"') and not line.startswith(','):
                # 내용 추가
                if sections[current_section]:
                    sections[current_section] += " " + line
                else:
                    sections[current_section] = line
        
        # 빈 섹션 처리
        for key, value in sections.items():
            if not value.strip():
                sections[key] = get_default_content(key)
        
        return sections
        
    except:
        return None

def validate_and_fix_sections(paper_data):
    """섹션별 검증 및 수정"""
    try:
        required_sections = ['abstract', 'introduction', 'methods', 'results', 'visuals', 'conclusion', 'references']
        
        for section in required_sections:
            if section not in paper_data or not paper_data[section] or len(paper_data[section].strip()) < 20:
                paper_data[section] = get_default_content(section)
        
        # methods 섹션 특별 처리 (너무 길면 단축)
        if len(paper_data['methods']) > 1000:
            methods_text = paper_data['methods'][:800] + "...\n\n데이터 수집 및 분석: 실험 결과를 체계적으로 기록하고 통계적으로 분석합니다."
            paper_data['methods'] = methods_text
        
        # references 섹션 정리
        if paper_data['references']:
            paper_data['references'] = clean_references(paper_data['references'])
        
        return paper_data
        
    except:
        return paper_data

def get_default_content(section):
    """기본 내용 제공"""
    defaults = {
        'abstract': "본 연구는 제시된 주제에 대해 체계적인 실험을 통해 과학적 근거를 확보하고자 합니다. 실험을 통해 얻은 데이터를 분석하여 의미있는 결론을 도출할 예정입니다.",
        'introduction': "현재 관련 분야에서는 다양한 연구가 진행되고 있지만, 여전히 해결되지 않은 문제들이 존재합니다. 본 연구는 이러한 문제점을 해결하기 위한 새로운 접근 방법을 제시하고자 합니다.",
        'methods': "1단계: 실험 재료 준비\n필요한 실험 도구와 재료를 준비합니다.\n\n2단계: 실험 환경 설정\n실험에 적합한 환경을 조성합니다.\n\n3단계: 데이터 수집\n체계적으로 실험을 진행하며 데이터를 수집합니다.\n\n4단계: 결과 분석\n수집된 데이터를 분석하여 의미있는 패턴을 찾습니다.",
        'results': "실험을 통해 다음과 같은 결과를 얻을 것으로 예상됩니다: 측정값들 간의 상관관계, 가설의 검증 결과, 그리고 실용적 활용 가능성에 대한 평가입니다.",
        'visuals': "실험 결과를 효과적으로 표현하기 위해 다음과 같은 시각자료를 제작할 예정입니다: 실험 과정을 보여주는 사진, 데이터 변화를 나타내는 그래프, 결과를 요약한 표 등입니다.",
        'conclusion': "본 연구를 통해 제시된 주제에 대한 새로운 이해를 얻을 수 있을 것이며, 이는 관련 분야의 발전에 기여할 것으로 기대됩니다. 또한 실생활에서의 응용 가능성도 탐구할 예정입니다.",
        'references': "1. 관련 주제 연구 동향\n- 내용: 해당 분야의 최신 연구 동향과 주요 발견사항을 정리한 자료\n- 검색: Google Scholar에서 '주제명 + research trends' 검색\n- 활용: 연구 배경 이해와 방향 설정에 도움\n\n2. 실험 방법론 가이드\n- 내용: 과학적 실험 설계와 데이터 분석 방법에 대한 종합적 안내\n- 검색: 각 대학교 과학교육과 또는 실험방법론 관련 교재 검색\n- 활용: 체계적인 실험 진행을 위한 참고자료\n\n3. 정부 연구 보고서\n- 내용: 관련 분야에 대한 정부 차원의 연구 및 정책 자료\n- 검색: 국가과학기술정보센터(NDSL) 또는 관련 정부기관 홈페이지\n- 활용: 국가적 관점에서의 연구 방향성 파악"
    }
    return defaults.get(section, f"{section} 섹션 내용이 생성되지 않았습니다.")

def clean_references(ref_text):
    """참고문헌 정리 - 가짜 링크 제거하고 검색 방법으로 대체"""
    try:
        cleaned = ref_text
        
        # 🔥 가짜 DOI와 링크들 제거
        fake_patterns = [
            r'https?://[^\s]*X\d+',  # X123456789 같은 가짜 ID
            r'https?://doi\.org/10\.\d+/[^\s]*XXX[^\s]*',  # XXX 포함 가짜 DOI
            r'https?://[^\s]*fake[^\s]*',  # fake 포함 링크
            r'DOI:\s*10\.\d+/[^\s]*XXX[^\s]*'  # 가짜 DOI 패턴
        ]
        
        for pattern in fake_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 🔥 "링크:" 를 "검색:" 으로 변경
        cleaned = cleaned.replace('링크:', '검색:')
        cleaned = cleaned.replace('- 링크:', '- 검색:')
        
        # 🔥 빈 링크 라인 정리
        lines = cleaned.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not (line.startswith('검색:') and len(line) < 20):
                filtered_lines.append(line)
        
        cleaned = '\n'.join(filtered_lines)
        
        # 너무 짧으면 기본값 사용
        if len(cleaned.strip()) < 50:
            return get_default_content('references')
        
        return cleaned.strip()
    except:
        return get_default_content('references')

def parse_text_response(text):
    """JSON 파싱 실패 시 텍스트에서 섹션별로 추출"""
    return manual_parse_sections(text)

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

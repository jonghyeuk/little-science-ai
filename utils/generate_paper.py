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
        - abstract: 연구목적과 예상결과 요약 (100-150단어) - 학술논문 형식, 교육 대상 언급 금지
        - introduction: 배경→문제→목적 순서 (200-250단어) - 학술논문 형식, 교육 대상 언급 금지
        - methods: 실험단계를 명확히 구분해서 작성 (250-300단어)
        - results: 예상되는 구체적 결과들 (150-200단어)
        - visuals: 필요한 그래프/차트 설명 (100-150단어)
        - conclusion: 실험을 통해 증명하려는 과학적 결론과 학술적 의의 (100-150단어)
        - references: 실제 확인가능한 자료 8-10개 (반드시 실제 링크 포함)

        실험방법 작성법:
        1단계: [제목] - (장비/재료 간단히)
        2단계: [제목] - "먼저 ~를 준비합니다. 다음으로 ~를 설정합니다" 형태로 친절하게 서술
        3단계: [제목] - "그 후에 ~를 진행합니다. 이때 주의할 점은 ~입니다" 형태로 친절하게 서술  
        4단계: [제목] - "마지막으로 ~를 측정합니다. ~를 기록합니다" 형태로 친절하게 서술
        (각 단계마다 고등학생이 따라할 수 있도록 구체적이고 친절한 서술형으로)

        참고문헌 작성법:
        1. 자료제목 (총 8-10개: 한국어 6개 + 영어 4개)
        - 내용: 핵심내용 2문장 설명  
        - 링크: 실제 DB 사이트 링크 포함
        - 활용: 연구에 어떻게 도움되는지
        
        중요: 주제와 밀접한 관련이 있는 자료만 선택하세요.
        """
        
        # 🔥 간단한 사용자 프롬프트
        user_prompt = f"""
        주제: {topic}
        아이디어: {research_idea}

        위 내용으로 학술 연구계획서를 JSON으로 작성해주세요.
        
        주의사항:
        - 초록과 서론: 학술논문 형식으로, "고등학생" 등 교육 대상 언급 금지
        - 결론: 실험을 통해 증명하려는 과학적 결론과 학술적 의의 중심
        - 실험방법: "먼저 ~를 합니다. 다음으로 ~를 설정합니다" 친절한 서술형
        - 참고문헌: 8-10개, 주제와 직접 관련된 자료만 선택
        """
        
        # Claude 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        print(f"=== Claude 응답 원본 ===")
        print(response_text[:300] + "...")

        paper_data = extract_json_robust(response_text)
        if paper_data:
            paper_data = validate_and_fix_sections(paper_data)
        
        return paper_data if paper_data else create_error_response()
        
    except Exception as e:
        print(f"❌ 전체 논문 생성 오류: {e}")
        return create_error_response()

def extract_json_robust(text):
    try:
        try:
            return json.loads(text)
        except:
            pass
        
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
        
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and 'abstract' in data:
                    return data
            except:
                continue
        
        return manual_parse_sections(text)
        
    except:
        return None

def manual_parse_sections(text):
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
            
            found_section = None
            for section, kws in keywords.items():
                if any(kw in line.lower() for kw in kws):
                    found_section = section
                    break
            
            if found_section:
                current_section = found_section
            elif current_section and not line.startswith('"') and not line.startswith(','):
                if sections[current_section]:
                    sections[current_section] += " " + line
                else:
                    sections[current_section] = line
        
        for key, value in sections.items():
            if not value.strip():
                sections[key] = get_default_content(key)
        
        return sections
        
    except:
        return None

def validate_and_fix_sections(paper_data):
    try:
        required_sections = ['abstract', 'introduction', 'methods', 'results', 'visuals', 'conclusion', 'references']
        
        for section in required_sections:
            if section not in paper_data or not paper_data[section] or len(paper_data[section].strip()) < 20:
                paper_data[section] = get_default_content(section)
        
        if len(paper_data['methods']) > 1000:
            methods_text = paper_data['methods'][:800] + "...\n\n데이터 수집 및 분석: 실험 결과를 체계적으로 기록하고 통계적으로 분석합니다."
            paper_data['methods'] = methods_text
        
        if paper_data['references']:
            paper_data['references'] = clean_references(paper_data['references'])
            paper_data['references'] = make_links_clickable(paper_data['references'])  # ✅ 링크 클릭 가능하게 처리
        
        return paper_data
        
    except:
        return paper_data

def make_links_clickable(reference_text):
    """링크 텍스트를 실제 클릭 가능한 <a> 링크로 변환"""
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank" style="color:#0969da;">🔗 링크 바로가기</a>', reference_text)

def get_default_content(section):
    defaults = {
        'abstract': "본 연구는 제시된 주제에 대해 체계적인 실험을 통해 과학적 근거를 확보하고자 한다...",
        'introduction': "현재 관련 분야에서는 다양한 연구가 진행되고 있지만...",
        'methods': "1단계: 실험 재료 준비\n필요한 실험 도구와 재료를 준비합니다...\n\n4단계: 결과 분석 및 정리...",
        'results': "실험을 통해 다음과 같은 결과를 얻을 것으로 예상된다...",
        'visuals': "실험 결과를 효과적으로 표현하기 위해 다음과 같은 시각자료를 제작할 예정입니다...",
        'conclusion': "본 연구를 통해 제시된 가설이 실험적으로 검증될 것으로 예상된다...",
        'references': "1. 관련 주제 최신 연구 동향\n- 링크: https://www.dbpia.co.kr/\n..."
    }
    return defaults.get(section, f"{section} 섹션 내용이 생성되지 않았습니다.")

def clean_references(ref_text):
    try:
        cleaned = ref_text
        all_links = re.findall(r'https://[^\s]*', cleaned)
        replacement_links = [
            'https://www.dbpia.co.kr/',
            'https://www.riss.kr/',
            'https://www.kci.go.kr/',
            'https://www.ndsl.kr/',
            'https://kiss.kstudy.com/',
            'https://www.nl.go.kr/',
            'https://www.sciencedirect.com/',
            'https://ieeexplore.ieee.org/',
            'https://www.nature.com/',
            'https://pubmed.ncbi.nlm.nih.gov/'
        ]
        for i, old_link in enumerate(all_links):
            if i < len(replacement_links):
                replacement_link = replacement_links[i]
                cleaned = cleaned.replace(old_link, replacement_link, 1)
            else:
                replacement_link = replacement_links[i % len(replacement_links)]
                cleaned = cleaned.replace(old_link, replacement_link, 1)
        return cleaned.strip()
    except:
        return ref_text

def parse_text_response(text):
    return manual_parse_sections(text)

def create_error_response():
    return {
        "abstract": "논문 초록 생성 중 오류가 발생했습니다...",
        "introduction": "서론 생성 중 오류가 발생했습니다...",
        "methods": "연구 방법 생성 중 오류가 발생했습니다...",
        "results": "예상 결과 생성 중 오류가 발생했습니다...",
        "visuals": "시각자료 제안 생성 중 오류가 발생했습니다.",
        "conclusion": "결론 생성 중 오류가 발생했습니다.",
        "references": "참고문헌 생성 중 오류가 발생했습니다."
    }

# app.py 수정본 (정보 설명을 사이드바로 이동 + DB 초기화 추가 + 틈새주제 선택 기능 추가)
import streamlit as st
import time
import re
import logging
from utils.layout import load_css
from utils.search_db import search_similar_titles, initialize_db  # initialize_db 추가
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf
from utils.generate_paper import generate_research_paper

# 3. 추가: streamlit 콘솔 로그 확인을 위한 코드 (맨 위에 추가)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 앱 시작 시 DB 초기화 (성능 최적화)
initialize_db()

# 틈새주제 파싱 함수 (수정된 버전)
def parse_niche_topics(explanation_lines):
    """explain_topic 결과에서 확장 가능한 탐구 아이디어 섹션을 파싱"""
    try:
        topics = []
        
        # 전체 라인을 하나의 텍스트로 합치기
        full_text = "\n".join(explanation_lines)
        print(f"=== 전체 텍스트 확인 ===\n{full_text[:500]}...\n")
        
        # "확장 가능한 탐구 아이디어" 섹션 찾기
        if "확장 가능한 탐구 아이디어" in full_text:
            # 해당 섹션 이후의 텍스트 추출
            section_start = full_text.find("확장 가능한 탐구 아이디어")
            section_text = full_text[section_start:]
            print(f"=== 섹션 텍스트 ===\n{section_text[:300]}...\n")
            
            # 라인별로 분리
            lines = section_text.split('\n')
            
            current_topic = ""
            current_description = ""
            
            for line in lines:
                line = line.strip()
                print(f"처리 중인 라인: '{line}'")
                
                # • 로 시작하는 제목 찾기
                if line.startswith('•') and len(line) > 2:
                    # 이전 주제가 있다면 저장
                    if current_topic:
                        full_topic = f"{current_topic}"
                        if current_description:
                            full_topic += f" - {current_description}"
                        topics.append(full_topic)
                        print(f"주제 저장: {full_topic}")
                    
                    # 새 주제 시작
                    current_topic = line[1:].strip()  # • 제거
                    current_description = ""
                    print(f"새 주제 시작: {current_topic}")
                
                # · 로 시작하는 설명 찾기  
                elif line.startswith('·') and current_topic and len(line) > 2:
                    current_description = line[1:].strip()  # · 제거
                    print(f"설명 추가: {current_description}")
            
            # 마지막 주제 저장
            if current_topic:
                full_topic = f"{current_topic}"
                if current_description:
                    full_topic += f" - {current_description}"
                topics.append(full_topic)
                print(f"마지막 주제 저장: {full_topic}")
        
        print(f"=== 최종 파싱된 주제들 ===\n{topics}\n")
        
        # 최소 3개 보장
        if len(topics) >= 3:
            return topics
        else:
            fallback_topics = [
                "기존 연구의 한계점 개선 - 현재 연구에서 부족한 부분을 찾아 개선방안 제시",
                "실용적 응용 방안 탐구 - 실생활에 적용할 수 있는 구체적 방법 연구", 
                "다른 분야와의 융합 연구 - 타 학문 분야와 연결한 새로운 접근법"
            ]
            print(f"fallback 주제 사용: {fallback_topics}")
            return fallback_topics
        
    except Exception as e:
        print(f"파싱 오류: {e}")  # 디버깅용
        fallback_topics = [
            "기존 연구의 한계점 개선 - 현재 연구에서 부족한 부분을 찾아 개선방안 제시",
            "실용적 응용 방안 탐구 - 실생활에 적용할 수 있는 구체적 방법 연구",
            "다른 분야와의 융합 연구 - 타 학문 분야와 연결한 새로운 접근법"
        ]
        return fallback_topics

# DOI 감지 및 링크 변환 함수
def convert_doi_to_links(text):
    """DOI 패턴을 감지하여 클릭 가능한 링크로 변환"""
    # DOI 패턴 정규 표현식: 10.XXXX/YYYY 형식
    doi_pattern = r'(?<!\w)(?:DOI\s*:\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
    
    # HTML 링크로 변환
    def replace_doi(match):
        doi = match.group(1)
        return f'<a href="https://doi.org/{doi}" target="_blank" style="color: #0969da; text-decoration: none;">{doi}</a>'
    
    # 텍스트 내 DOI 패턴을 링크로 변환
    linked_text = re.sub(doi_pattern, replace_doi, text)
    
    return linked_text

# 기본 설정
st.set_page_config(page_title="LittleScienceAI", layout="wide")
load_css()

# 중앙 정렬 CSS
st.markdown("""
<style>
section.main > div.block-container {
    max-width: 800px !important; 
    margin: 0 auto !important;
    padding: 2rem 3rem !important;
    background-color: white !important;
}

.sidebar-info-box {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 15px;
    border-left: 3px solid #4a86e8;
    font-size: 0.9em;
}

.sidebar-info-box h4 {
    margin-top: 0;
    color: #2c5aa0;
}

.sidebar-info-box.arxiv {
    border-left-color: #4caf50;
}

.sidebar-info-box.arxiv h4 {
    color: #2e7d32;
}

.paper-subsection {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin: 15px 0;
    border-left: 3px solid #28a745;
}

.stButton > button {
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
""", unsafe_allow_html=True)

# 인증 시스템
ACCESS_KEYS = st.secrets["general"]["access_keys"]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## LittleScienceAI 로그인")
    user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
    
    if user_key in ACCESS_KEYS:
        st.session_state.authenticated = True
        st.rerun()
    elif user_key:
        st.warning("🚫 올바른 인증 키를 입력하세요.")
    st.stop()

# 세션 상태 초기화 (🔥 캐싱용 상태 추가)
if 'niche_topics' not in st.session_state:
    st.session_state.niche_topics = []
if 'generated_paper' not in st.session_state:
    st.session_state.generated_paper = {}
# 🔥 캐싱용 세션 상태 (최소한만 추가)
if 'last_searched_topic' not in st.session_state:
    st.session_state.last_searched_topic = ""
if 'cached_internal_results' not in st.session_state:
    st.session_state.cached_internal_results = []
if 'cached_arxiv_results' not in st.session_state:
    st.session_state.cached_arxiv_results = []

# 사이드바
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1. 주제 입력
2. 개념 해설 보기
3. 논문 추천 확인
4. 틈새주제 선택
5. 논문 형식 작성
6. PDF 저장
""")

# 사이드바에 학술 자료 설명 추가
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 학술 자료 정보")

# ISEF 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box">
<h4>📊 ISEF</h4>
<p>
세계 최대 규모의 고등학생 과학 경진대회로, 80여 개국에서 1,800명 이상의 학생들이 참가하여 혁신적인 연구 프로젝트를 발표합니다. 1950년부터 시작된 이 대회는 과학, 기술, 공학, 수학(STEM) 분야의 차세대 인재를 발굴합니다.
</p>
</div>
""", unsafe_allow_html=True)

# arXiv 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box arxiv">
<h4>📑 arXiv</h4>
<p>
물리학, 수학, 컴퓨터 과학 등의 분야에서 연구자들이 논문을 정식 출판 전에 공유하는 플랫폼입니다. 코넬 대학에서 운영하며, 최신 연구 동향을 빠르게 접할 수 있지만 일부는 아직 peer review를 거치지 않은 상태일 수 있습니다.
</p>
</div>
""", unsafe_allow_html=True)

# 메인 타이틀
st.title("🧪 과학논문 주제 탐색 도우미")

# 초기화
if 'full_text' not in st.session_state:
    st.session_state.full_text = ""

# 검색창
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:", 
                     placeholder="예: 양자 컴퓨팅, 유전자 편집, 미생물 연료전지...")

# 🔥 주제가 입력된 경우 (캐싱 로직 적용)
if topic:
    # 새 주제일 때만 검색 실행
    if True:  # st.session_state.last_searched_topic != topic:
        # 새 주제 검색
        st.session_state.last_searched_topic = topic
        st.session_state.generated_paper = {}  # 논문 초기화
        
        # 주제 해설 표시
        st.subheader("📘 주제 해설")
        
        # 즉시 해설 생성 및 표시 (DOI 링크 변환 추가)
        with st.spinner("🤖 AI가 주제 분석 중..."):
            try:
                explanation_lines = explain_topic(topic)
                explanation_text = "\n\n".join(explanation_lines)
                
                # 틈새주제 파싱 및 저장
                print("=== 디버깅: explanation_lines 구조 ===")
                for i, line in enumerate(explanation_lines):
                    print(f"라인 {i}: {repr(line[:100])}...")  # 처음 100자만 출력
                    if "확장 가능한 탐구 아이디어" in line:
                        print(f"*** 찾았다! 라인 {i}에 확장 가능한 탐구 아이디어 있음 ***")
                        print(f"전체 내용: {repr(line)}")
                        break
                print("=== 디버깅 끝 ===")

                st.session_state.niche_topics = parse_niche_topics(explanation_lines)
                
                # DOI 패턴을 링크로 변환 (화면 표시용)
                linked_explanation = convert_doi_to_links(explanation_text)
                
                # 링크가 포함된 설명 표시
                st.markdown(linked_explanation, unsafe_allow_html=True)
                
                # PDF용 텍스트는 원본 형식으로 저장 (마크다운 형식)
                st.session_state.full_text = f"# 📘 {topic} - 주제 해설\n\n{explanation_text}\n\n"
            except Exception as e:
                st.error(f"주제 해설 생성 중 오류: {str(e)}")
                st.session_state.full_text = f"# 📘 {topic} - 주제 해설\n\n생성 중 오류 발생\n\n"
        
        # 🔥 내부 DB 검색 결과 (검색 실행 + 결과 저장)
        st.subheader("📄 ISEF (International Science and Engineering Fair) 출품논문")
        
        with st.spinner("🔍 ISEF 관련 프로젝트를 빠르게 검색 중..."):
            try:
                # 검색 실행 및 캐시 저장
                st.session_state.cached_internal_results = search_similar_titles(topic)
                internal_results = st.session_state.cached_internal_results
                
                if not internal_results:
                    st.info("❗ 관련 프로젝트가 없습니다.")
                    st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n❗ 관련 프로젝트가 없습니다.\n\n"
                else:
                    st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n"
                    
                    for project in internal_results:
                        title = project.get('제목', '')
                        summary = project.get('요약', '')
                        
                        # 메타 정보
                        meta_parts = []
                        if project.get('연도'):
                            meta_parts.append(f"📅 {project['연도']}")
                        if project.get('분야'):
                            meta_parts.append(f"🔬 {project['분야']}")
                        if project.get('국가'):
                            loc = project['국가']
                            if project.get('지역'):
                                loc += f", {project['지역']}"
                            meta_parts.append(f"🌎 {loc}")
                        if project.get('수상'):
                            meta_parts.append(f"🏆 {project['수상']}")
                        
                        meta_text = " · ".join(meta_parts)
                        
                        # 내부 결과에서도 DOI 변환 적용
                        linked_summary = convert_doi_to_links(summary)
                        
                        # 카드 형태로 표시
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                            <h3 style="color: #333; margin-top: 0;">📌 {title}</h3>
                            <p style="color: #666; font-style: italic; margin-bottom: 12px;">{meta_text}</p>
                            <p>{linked_summary}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.full_text += f"- **{title}**\n{summary}\n_{meta_text}_\n\n"
            except Exception as e:
                st.error(f"내부 DB 검색 중 오류: {str(e)}")
                st.session_state.cached_internal_results = []
                st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n검색 중 오류 발생\n\n"
        
        # 🔥 arXiv 결과 (검색 실행 + 결과 저장)
        st.subheader("🌐 아카이브 arXiv 에서 찾은 관련 논문")
        
        with st.spinner("🔍 arXiv 논문 검색 중..."):
            try:
                # 검색 실행 및 캐시 저장
                st.session_state.cached_arxiv_results = search_arxiv(topic)
                arxiv_results = st.session_state.cached_arxiv_results
                
                if not arxiv_results:
                    st.info("❗ 관련 논문이 없습니다.")
                    st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n❗ 관련 논문이 없습니다.\n\n"
                else:
                    st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n"
                    
                    for paper in arxiv_results:
                        title = paper.get('title', '')
                        summary = paper.get('summary', '')
                        link = paper.get('link', '')
                        
                        # arXiv 결과에서도 DOI 변환 적용
                        linked_summary = convert_doi_to_links(summary)
                        
                        # 카드 형태로 표시 (프리프린트 표시 추가)
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                            <h3 style="color: #333; margin-top: 0;">🌐 {title}</h3>
                            <p style="color: #666; font-style: italic; margin-bottom: 12px;">출처: arXiv (프리프린트 저장소)</p>
                            <p>{linked_summary}</p>
                            <a href="{link}" target="_blank" style="color: #0969da; text-decoration: none;">🔗 논문 링크 보기</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.full_text += f"- **{title}**\n{summary}\n[링크]({link})\n\n"
            except Exception as e:
                st.error(f"arXiv 검색 중 오류: {str(e)}")
                st.session_state.cached_arxiv_results = []
                st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n검색 중 오류 발생\n\n"
    
    else:
        # 🔥 같은 주제 - 캐시 사용 (스피너 없이 저장된 결과 표시)
        st.subheader("📘 주제 해설")
        if st.session_state.full_text:
            explanation_part = st.session_state.full_text.split("## 📄 내부 DB 유사 논문")[0]
            explanation_text = explanation_part.replace(f"# 📘 {topic} - 주제 해설\n\n", "")
            linked_explanation = convert_doi_to_links(explanation_text)
            st.markdown(linked_explanation, unsafe_allow_html=True)
        
        # 🔥 캐시된 ISEF 결과 표시 (원본 로직 그대로)
        st.subheader("📄 ISEF (International Science and Engineering Fair) 출품논문")
        
        internal_results = st.session_state.cached_internal_results
        if not internal_results:
            st.info("❗ 관련 프로젝트가 없습니다.")
        else:
            for project in internal_results:
                title = project.get('제목', '')
                summary = project.get('요약', '')
                
                # 메타 정보
                meta_parts = []
                if project.get('연도'):
                    meta_parts.append(f"📅 {project['연도']}")
                if project.get('분야'):
                    meta_parts.append(f"🔬 {project['분야']}")
                if project.get('국가'):
                    loc = project['국가']
                    if project.get('지역'):
                        loc += f", {project['지역']}"
                    meta_parts.append(f"🌎 {loc}")
                if project.get('수상'):
                    meta_parts.append(f"🏆 {project['수상']}")
                
                meta_text = " · ".join(meta_parts)
                
                # 내부 결과에서도 DOI 변환 적용
                linked_summary = convert_doi_to_links(summary)
                
                # 카드 형태로 표시
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    <h3 style="color: #333; margin-top: 0;">📌 {title}</h3>
                    <p style="color: #666; font-style: italic; margin-bottom: 12px;">{meta_text}</p>
                    <p>{linked_summary}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # 🔥 캐시된 arXiv 결과 표시 (원본 로직 그대로)
        st.subheader("🌐 아카이브 arXiv 에서 찾은 관련 논문")
        
        arxiv_results = st.session_state.cached_arxiv_results
        if not arxiv_results:
            st.info("❗ 관련 논문이 없습니다.")
        else:
            for paper in arxiv_results:
                title = paper.get('title', '')
                summary = paper.get('summary', '')
                link = paper.get('link', '')
                
                # arXiv 결과에서도 DOI 변환 적용
                linked_summary = convert_doi_to_links(summary)
                
                # 카드 형태로 표시 (프리프린트 표시 추가)
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    <h3 style="color: #333; margin-top: 0;">🌐 {title}</h3>
                    <p style="color: #666; font-style: italic; margin-bottom: 12px;">출처: arXiv (프리프린트 저장소)</p>
                    <p>{linked_summary}</p>
                    <a href="{link}" target="_blank" style="color: #0969da; text-decoration: none;">🔗 논문 링크 보기</a>
                </div>
                """, unsafe_allow_html=True)
    
    # ========== 틈새주제 선택 섹션 추가 ==========
    if st.session_state.niche_topics:
        st.markdown("---")
        st.subheader("🎯 세부 틈새주제 선택")
        st.markdown("위에서 제안된 탐구 아이디어 중에서 **1개**를 선택하여 체계적인 논문 형식으로 작성해보세요.")
        
        # 라디오 버튼으로 1개만 선택
        selected_topic_index = st.radio(
            "연구하고 싶은 틈새주제를 선택하세요:",
            range(len(st.session_state.niche_topics)),
            format_func=lambda x: f"주제 {x+1}: {st.session_state.niche_topics[x]}",
            key="selected_niche_topic"
        )
        
        # 🔥 논문 생성 버튼 (st.rerun() 제거)
        if st.button("📝 선택한 주제로 논문 형식 작성하기", type="primary"):
            selected_idea = st.session_state.niche_topics[selected_topic_index]
            
            print(f"=== 논문 생성 시작 ===")
            print(f"주제: {topic}")
            print(f"선택된 아이디어: {selected_idea}")
            print(f"참고자료 길이: {len(st.session_state.full_text)} 문자")
            
            # 논문 생성
            with st.spinner("🤖 AI가 체계적인 논문을 작성 중입니다... (약 30초 소요)"):
                try:
                    st.session_state.generated_paper = generate_research_paper(
                        topic=topic, 
                        research_idea=selected_idea, 
                        references=st.session_state.full_text
                    )
                    print(f"논문 생성 완료: {type(st.session_state.generated_paper)}")
                    print(f"논문 키들: {list(st.session_state.generated_paper.keys()) if isinstance(st.session_state.generated_paper, dict) else 'dict가 아님'}")
                except Exception as e:
                    print(f"논문 생성 오류: {e}")
                    st.error(f"논문 생성 중 오류 발생: {str(e)}")
                    st.session_state.generated_paper = {}
            
            if st.session_state.generated_paper:
                st.success("📄 논문이 성공적으로 생성되었습니다!")
                # st.rerun() ← 🔥 제거!
            else:
                st.error("논문 생성에 실패했습니다. 다시 시도해주세요.")
    
    # ========== 논문 표시 섹션 ==========
    if st.session_state.generated_paper and isinstance(st.session_state.generated_paper, dict):
        st.markdown("---")
        st.subheader("📄 생성된 연구 논문")
        
        paper_data = st.session_state.generated_paper
        
        # 초록
        if paper_data.get("abstract"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 📋 초록 (Abstract)")
            st.markdown(paper_data["abstract"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 실험 방법
        if paper_data.get("methods"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 🔬 실험 방법 (Methods)")
            st.markdown(paper_data["methods"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 예상 결과
        if paper_data.get("results"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 📊 예상 결과 (Expected Results)")
            st.markdown(paper_data["results"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 시각자료 제안
        if paper_data.get("visuals"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 📈 시각자료 제안 (Suggested Visualizations)")
            st.markdown(paper_data["visuals"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 결론
        if paper_data.get("conclusion"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 🎯 결론 (Conclusion)")
            st.markdown(paper_data["conclusion"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 참고문헌
        if paper_data.get("references"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 📚 참고문헌 (References)")
            st.markdown(paper_data["references"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # PDF용 텍스트에 논문 내용 추가
        paper_text = f"""
## 📄 생성된 연구 논문

### 초록
{paper_data.get("abstract", "")}

### 실험 방법
{paper_data.get("methods", "")}

### 예상 결과
{paper_data.get("results", "")}

### 시각자료 제안
{paper_data.get("visuals", "")}

### 결론
{paper_data.get("conclusion", "")}

### 참고문헌
{paper_data.get("references", "")}
"""
        st.session_state.full_text += paper_text
        
        # 다시 작성 버튼
        if st.button("🔄 다른 주제로 다시 작성하기"):
            st.session_state.generated_paper = {}
            st.rerun()
    
    # PDF 저장 버튼 (기존 위치 유지)
    if st.session_state.full_text:
        st.markdown("---")
        if st.button("📥 이 내용 PDF로 저장하기"):
            path = generate_pdf(st.session_state.full_text)
            with open(path, "rb") as f:
                st.download_button(
                    "📄 PDF 다운로드", 
                    f, 
                    file_name="little_science_ai_research.pdf",
                    mime="application/pdf"
                )

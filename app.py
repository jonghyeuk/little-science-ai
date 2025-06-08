# app.py 수정본 (Google Sheets 기반 인증 시스템으로 변경)
import streamlit as st
import time
import re
import logging
import os
import json
import gspread
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2.service_account import Credentials
from utils.layout import load_css
from utils.search_db import search_similar_titles, initialize_db
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.beautiful_pdf_generator import generate_pdf
from utils.generate_paper import generate_research_paper

# 3. 추가: streamlit 콘솔 로그 확인을 위한 코드 (맨 위에 추가)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 앱 시작 시 DB 초기화 (성능 최적화)
initialize_db()

# ==================== 🔥 Google Sheets 기반 이용권 시스템 ====================

# Google Sheets 연결 설정
@st.cache_resource
def connect_google_sheets():
    """Google Sheets에 연결 (캐시됨)"""
    try:
        # Streamlit secrets에서 Google 서비스 계정 정보 가져오기
        google_credentials = st.secrets["google_service_account"]
        
        # 인증 정보 설정
        credentials = Credentials.from_service_account_info(
            google_credentials,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        # gspread 클라이언트 생성
        gc = gspread.authorize(credentials)
        
        # 스프레드시트 열기
        sheet_url = st.secrets["general"]["sheet_url"]
        worksheet = gc.open_by_url(sheet_url).sheet1
        
        print("✅ Google Sheets 연결 성공")
        return worksheet
    except Exception as e:
        print(f"❌ Google Sheets 연결 실패: {e}")
        st.error(f"Google Sheets 연결 실패: {e}")
        return None

def get_license_from_sheets(user_key):
    """Google Sheets에서 이용권 정보 조회"""
    try:
        worksheet = connect_google_sheets()
        if not worksheet:
            return None
        
        # 모든 데이터 가져오기
        all_values = worksheet.get_all_values()
        
        # 첫 번째 행은 헤더이므로 제외
        headers = all_values[0]  # ['코드', '타입', '이용기간_일수', '이용기간_분수', '첫사용날짜', '마지막사용날짜', '상태']
        data_rows = all_values[1:]
        
        print(f"🔍 전체 데이터 행 수: {len(data_rows)}")
        print(f"🔍 검색 코드: {user_key}")
        
        # 해당 코드 찾기
        for i, row in enumerate(data_rows):
            if len(row) > 0 and row[0] == user_key:  # A열이 코드
                print(f"✅ 코드 발견: 행 {i+2}")
                return {
                    'row_index': i + 2,  # 실제 시트에서의 행 번호 (헤더 포함)
                    'code': row[0],
                    'type': row[1] if len(row) > 1 else '',
                    'duration_days': int(row[2]) if len(row) > 2 and row[2] else None,
                    'duration_minutes': int(row[3]) if len(row) > 3 and row[3] else None,
                    'first_used': row[4] if len(row) > 4 else '',
                    'last_used': row[5] if len(row) > 5 else '',
                    'status': row[6] if len(row) > 6 else ''
                }
        
        print(f"❌ 코드를 찾지 못함")
        return None  # 코드를 찾지 못함
        
    except Exception as e:
        print(f"❌ Sheets 조회 오류: {e}")
        return None

def update_license_in_sheets(user_key, first_used_date=None, last_used_date=None, status=None):
    """Google Sheets에서 이용권 정보 업데이트"""
    try:
        worksheet = connect_google_sheets()
        if not worksheet:
            return False
        
        # 해당 코드의 행 정보 가져오기
        license_info = get_license_from_sheets(user_key)
        if not license_info:
            return False
        
        row_index = license_info['row_index']
        print(f"📝 업데이트 대상: 행 {row_index}")
        
        # 개별 셀 업데이트 (더 안전한 방식)
        if first_used_date:
            # E열 (첫사용날짜) 업데이트
            worksheet.update(f'E{row_index}', first_used_date)
            print(f"   - E{row_index}: {first_used_date}")
        
        if last_used_date:
            # F열 (마지막사용날짜) 업데이트  
            worksheet.update(f'F{row_index}', last_used_date)
            print(f"   - F{row_index}: {last_used_date}")
        
        if status:
            # G열 (상태) 업데이트
            worksheet.update(f'G{row_index}', status)
            print(f"   - G{row_index}: {status}")
        
        print("✅ Sheets 업데이트 완료")
        return True
        
    except Exception as e:
        print(f"❌ Sheets 업데이트 오류: {e}")
        return False

def check_license_validity(user_key):
    """Google Sheets 기반 이용권 유효성 체크"""
    print(f"\n🔑 Sheets 이용권 체크 시작: {user_key}")
    
    # 1. Google Sheets에서 코드 정보 가져오기
    license_info = get_license_from_sheets(user_key)
    
    if not license_info:
        print(f"   - 결과: 잘못된 키")
        return False, "잘못된 인증 키입니다."
    
    print(f"   - 찾은 이용권: {license_info}")
    
    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 2. 상태 체크
    if license_info['status'] == '만료됨':
        print(f"   - 결과: 이미 만료된 키")
        return False, "이미 만료된 인증 키입니다."
    
    # 3. 최초 사용인지 확인
    if not license_info['first_used']:
        print(f"   - 최초 사용자 감지")
        # 최초 사용 - 시작일 기록
        update_success = update_license_in_sheets(
            user_key, 
            first_used_date=current_time_str,
            last_used_date=current_time_str,
            status='사용중'
        )
        
        if update_success:
            print(f"   - 최초 사용 정보 업데이트 완료")
            return True, f"이용권이 활성화되었습니다! ({license_info['type']})"
        else:
            return False, "이용권 활성화 중 오류가 발생했습니다."
    
    # 4. 기존 사용자 - 만료 체크
    try:
        first_used = datetime.strptime(license_info['first_used'], '%Y-%m-%d %H:%M:%S')
    except:
        try:
            first_used = datetime.strptime(license_info['first_used'], '%Y-%m-%d')
        except:
            return False, "이용권 정보가 올바르지 않습니다."
    
    print(f"   - 기존 사용자")
    print(f"   - 최초 사용: {first_used}")
    
    # 5. 만료 시간 계산
    if license_info['duration_days']:
        expire_time = first_used + timedelta(days=license_info['duration_days'])
    elif license_info['duration_minutes']:
        expire_time = first_used + timedelta(minutes=license_info['duration_minutes'])
    else:
        print(f"   - 오류: 이용권 정보 없음")
        return False, "이용권 정보가 올바르지 않습니다."
    
    print(f"   - 만료 시간: {expire_time}")
    
    # 6. 만료 여부 확인
    if current_time > expire_time:
        print(f"   - 결과: 만료됨")
        # Sheets에 만료 상태 업데이트
        update_license_in_sheets(user_key, status='만료됨')
        return False, f"이용권이 만료되었습니다. (만료일: {expire_time.strftime('%Y-%m-%d %H:%M')})"
    
    # 7. 마지막 사용 시간 업데이트
    update_license_in_sheets(user_key, last_used_date=current_time_str)
    
    time_left = expire_time - current_time
    print(f"   - 결과: 유효 (남은 시간: {time_left})")
    return True, "유효한 이용권입니다."

def get_license_info(user_key):
    """Google Sheets 기반 이용권 정보 반환"""
    license_info = get_license_from_sheets(user_key)
    if not license_info or not license_info['first_used']:
        return None
    
    try:
        first_used = datetime.strptime(license_info['first_used'], '%Y-%m-%d %H:%M:%S')
    except:
        try:
            first_used = datetime.strptime(license_info['first_used'], '%Y-%m-%d')
        except:
            return None
    
    current_time = datetime.now()
    
    # 만료 시간 계산
    if license_info['duration_days']:
        expire_time = first_used + timedelta(days=license_info['duration_days'])
    elif license_info['duration_minutes']:
        expire_time = first_used + timedelta(minutes=license_info['duration_minutes'])
    else:
        return None
    
    # 남은 시간 계산
    time_left = expire_time - current_time
    
    return {
        'license_type': license_info['type'],
        'first_used': first_used,
        'expire_time': expire_time,
        'time_left': time_left,
        'is_expired': time_left.total_seconds() <= 0,
        'status': license_info['status']
    }

def format_time_left(time_left):
    """남은 시간을 보기 좋게 포맷팅"""
    if time_left.total_seconds() <= 0:
        return "만료됨"
    
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}일 {hours}시간 {minutes}분"
    elif hours > 0:
        return f"{hours}시간 {minutes}분"
    else:
        return f"{minutes}분"

# ==================== 🔥 Google Sheets 이용권 시스템 끝 ====================

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
    """DOI 패턴을 감지하여 클릭하기 쉬운 링크로 변환"""
    # DOI 패턴 정규 표현식
    doi_pattern = r'(?<!\w)(?:DOI\s*:\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
    
    # 간단한 링크 변환
    def replace_doi(match):
        doi = match.group(1)
        return f'<a href="https://doi.org/{doi}" target="_blank" style="color: #0969da; text-decoration: none; white-space: nowrap;">📄 논문 링크</a>'
    
    # 텍스트 내 DOI 패턴을 링크로 변환
    linked_text = re.sub(doi_pattern, replace_doi, text)
    
    return linked_text

# 기본 설정
st.set_page_config(page_title="LittleScienceAI", layout="wide")
load_css()

# 중앙 정렬 CSS + 🔥 이용권 정보 CSS 추가
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

.license-info-box {
    background-color: #f0f8ff;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 20px;
    border-left: 4px solid #007bff;
    font-size: 0.9em;
}

.license-info-box.warning {
    background-color: #fff8e1;
    border-left-color: #ff9800;
}

.license-info-box.expired {
    background-color: #ffebee;
    border-left-color: #f44336;
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

# 🔥 Google Sheets 기반 인증 시스템
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_license_key" not in st.session_state:
    st.session_state.user_license_key = ""

if not st.session_state.authenticated:
    st.markdown("## LittleScienceAI 로그인")
    user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
    
    if user_key:
        is_valid, message = check_license_validity(user_key)
        if is_valid:
            st.session_state.authenticated = True
            st.session_state.user_license_key = user_key
            st.success(message)
            st.rerun()
        else:
            st.error(f"🚫 {message}")
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

# 🔥 사이드바에 이용권 정보 표시
license_info = get_license_info(st.session_state.user_license_key)
if license_info:
    # 남은 시간에 따른 스타일 결정
    time_left_total_minutes = license_info['time_left'].total_seconds() / 60
    
    if license_info['is_expired']:
        box_class = "expired"
        icon = "❌"
        status_text = "만료됨"
    elif time_left_total_minutes <= 60:  # 1시간 이하
        box_class = "warning"
        icon = "⚠️"
        status_text = "곧 만료"
    else:
        box_class = ""
        icon = "✅"
        status_text = "이용중"
    
    st.sidebar.markdown(f"""
    <div class="license-info-box {box_class}">
    <h4>{icon} 이용권 정보</h4>
    <p><strong>타입:</strong> {license_info['license_type']}</p>
    <p><strong>상태:</strong> {status_text}</p>
    <p><strong>남은 시간:</strong> {format_time_left(license_info['time_left'])}</p>
    <p><strong>만료 예정:</strong> {license_info['expire_time'].strftime('%m/%d %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 만료된 경우 접근 차단
    if license_info['is_expired']:
        st.error("🚫 이용권이 만료되었습니다. 새로운 인증 키가 필요합니다.")
        if st.button("🔄 다시 로그인"):
            st.session_state.authenticated = False
            st.session_state.user_license_key = ""
            st.rerun()
        st.stop()

# 나머지 코드는 기존과 동일...
# (사이드바, 메인 UI, 검색 로직 등은 그대로 유지)

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

# 🔥 바로 여기에 서비스 가이드 추가!
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 서비스 가이드")

guide_pdf_path = "assets/LittleScienceAI_사용가이드.pdf"

try:
    with open(guide_pdf_path, "rb") as pdf_file:
        st.sidebar.download_button(
            label="📚 필독! 사용법 가이드 다운로드",
            data=pdf_file,
            file_name="LittleScienceAI_사용가이드.pdf",
            mime="application/pdf",
            type="primary"
        )
except FileNotFoundError:
    st.sidebar.error("📄 가이드 파일을 찾을 수 없습니다.")

st.sidebar.markdown("""
<div class="sidebar-info-box">
<h4>💡 가이드 활용법</h4>
<p>
- 처음 사용하시나요? 가이드를 먼저 꼭 읽어보세요<br>
- 각 단계별 상세한 설명과 팁 포함<br>
</p>
</div>
""", unsafe_allow_html=True)

# 사이드바에 학술 자료 설명 추가
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 학술 자료 정보")

# ISEF 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box">
<h4>📊 ISEF</h4>
<p>
1950년대부터 시작한 세계 최대 규모의 고등학생 과학 경진대회로, 80여 개국에서 1,800명 이상의 학생들이 참가하여 혁신적인 연구 프로젝트를 발표합니다.
</p>
</div>
""", unsafe_allow_html=True)

# arXiv 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box arxiv">
<h4>📑 arXiv</h4>
<p>
과학계 연구자들이 논문을 정식 출판 전에 공유하는 플랫폼으로 현재 코넬 대학에서 운영하며, 최신 연구 동향을 빠르게 접할 수 있지만 일부는 아직 peer review를 거치지 않은 상태일 수 있습니다.
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
                     placeholder="예: 다이오드 트렌지스터, 미세먼지 필터, 미생물 연료전지...")

# 🔥 깔끔한 가이드
if not topic:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid #007bff;">
    <h4 style="color: #007bff; margin-top: 0;">💡 입력 가이드</h4>
    
    <p><strong>📝 입력 방식:</strong></p>
    <ul>
    <li><strong>단어형:</strong> <code>미세플라스틱</code>, <code>회절현상</code></li>
    <li><strong>주제형:</strong> <code>광학을 활용한 실험 설계</code></li>
    </ul>
    
    <p><strong>⚠️ 주의:</strong> 연관성 있는 과학 개념을 조합해주세요. 동떨어진 주제를 검색시 엉뚱한 결과가 나올 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

# 🔥 주제가 입력된 경우 (캐싱 로직 적용)
if topic:
   
    # 🔥 수정된 코드:
    if (st.session_state.last_searched_topic != topic or 
        len(st.session_state.cached_internal_results) == 0 or 
        len(st.session_state.cached_arxiv_results) == 0):
        # 새 주제 검색
        st.session_state.last_searched_topic = topic
        st.session_state.generated_paper = {}  # 논문 초기화
        
# 주제 해설 표시
        st.subheader("📘 주제 해설")
        
        try:
            # 전체 내용 생성 (기존과 동일)
            with st.spinner("⚡ AI가 주제 분석 중..."):
                explanation_lines = explain_topic(topic)
                explanation_text = "\n\n".join(explanation_lines)
                
                # 틈새주제 파싱 및 저장
                st.session_state.niche_topics = parse_niche_topics(explanation_lines)
            
            # 섹션별로 분할 (확장 가능한 탐구 아이디어까지 vs 나머지)
            full_text = explanation_text
            if "## 📊 **최신논문검색**" in full_text:
                # 애니메이션 부분: 확장 가능한 탐구 아이디어까지
                animation_part = full_text.split("## 📊 **최신논문검색**")[0]
                # 즉시 표시 부분: 최신논문검색부터
                remaining_part = "## 📊 **최신논문검색**" + full_text.split("## 📊 **최신논문검색**")[1]
            else:
                # 분할점을 찾지 못하면 전체를 애니메이션으로
                animation_part = full_text
                remaining_part = ""
            
            # 타이핑 애니메이션 함수 (스킵 버튼 없음)
            def typewriter_animation(text, speed=0.002):
                placeholder = st.empty()
                displayed_text = ""
                for char in text:
                    displayed_text += char
                    placeholder.markdown(displayed_text + "▌", unsafe_allow_html=True)
                    time.sleep(speed)
                placeholder.markdown(text, unsafe_allow_html=True)
            
            # 1단계: 확장 가능한 탐구 아이디어까지 애니메이션
            animation_linked = convert_doi_to_links(animation_part)
            typewriter_animation(animation_linked)
            
            # 2단계: 나머지 즉시 표시
            if remaining_part:
                st.markdown("---")
                remaining_linked = convert_doi_to_links(remaining_part)
                st.markdown(remaining_linked, unsafe_allow_html=True)
            
            # PDF용 텍스트 저장 (전체 내용)
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
                        
                        # 🔥 길이 제한 추가 (400자 이상이면 자르고 ... 추가)
                        if len(linked_summary) > 400:
                            display_summary = linked_summary[:297] + "..."
                        else:
                            display_summary = linked_summary
                        
                        # 카드 형태로 표시
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                            <h3 style="color: #333; margin-top: 0;">📌 {title}</h3>
                            <p style="color: #666; font-style: italic; margin-bottom: 12px;">{meta_text}</p>
                            <p>{display_summary}</p>
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
                        
                        # 🔥 길이 제한 추가 (400자 이상이면 자르고 ... 추가)
                        if len(linked_summary) > 400:
                            display_summary = linked_summary[:297] + "..."
                        else:
                            display_summary = linked_summary
                        
                        # 카드 형태로 표시 (프리프린트 표시 추가)
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                            <h3 style="color: #333; margin-top: 0;">🌐 {title}</h3>
                            <p style="color: #666; font-style: italic; margin-bottom: 12px;">출처: arXiv (프리프린트 저장소)</p>
                            <p>{display_summary}</p>
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
                
                # 🔥 길이 제한 추가 (400자 이상이면 자르고 ... 추가)
                if len(linked_summary) > 400:
                    display_summary = linked_summary[:297] + "..."
                else:
                    display_summary = linked_summary
                
                # 카드 형태로 표시
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    <h3 style="color: #333; margin-top: 0;">📌 {title}</h3>
                    <p style="color: #666; font-style: italic; margin-bottom: 12px;">{meta_text}</p>
                    <p>{display_summary}</p>
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
                
                # 🔥 길이 제한 추가 (400자 이상이면 자르고 ... 추가)
                if len(linked_summary) > 400:
                    display_summary = linked_summary[:297] + "..."
                else:
                    display_summary = linked_summary
                
                # 카드 형태로 표시 (프리프린트 표시 추가)
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    <h3 style="color: #333; margin-top: 0;">🌐 {title}</h3>
                    <p style="color: #666; font-style: italic; margin-bottom: 12px;">출처: arXiv (프리프린트 저장소)</p>
                    <p>{display_summary}</p>
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
        
        # 서론 추가 ⭐ 새로 추가된 부분
        if paper_data.get("introduction"):
            st.markdown('<div class="paper-subsection">', unsafe_allow_html=True)
            st.markdown("### 📖 서론 (Introduction)")
            st.markdown(paper_data["introduction"])
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
        
        # PDF용 텍스트에 논문 내용 추가 (서론 포함)
        paper_text = f"""
## 📄 생성된 연구 논문

### 초록
{paper_data.get("abstract", "")}

### 서론
{paper_data.get("introduction", "")}

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
    
    # PDF 저장 버튼 - 논문 완성 후에만 활성화
    st.markdown("---")
    st.subheader("📄 PDF 저장")

    # 논문이 완성되었는지 확인
    paper_completed = bool(st.session_state.generated_paper and 
                          isinstance(st.session_state.generated_paper, dict) and
                          st.session_state.generated_paper.get("abstract"))

    if paper_completed:
        if st.button("📥 완성된 연구보고서 PDF로 저장하기", type="primary"):
            if st.session_state.full_text:
                path = generate_pdf(st.session_state.full_text)
                if path and os.path.exists(path):
                    with open(path, "rb") as f:
                        st.download_button(
                            "📄 PDF 다운로드", 
                            f, 
                            file_name="little_science_ai_research.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error("PDF 생성에 실패했습니다.")
    else:
        st.button("📥 연구보고서 PDF로 저장하기", 
                 disabled=True, 
                 help="논문 생성을 완료한 후 PDF 저장이 가능합니다.")

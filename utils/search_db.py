import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic
import re

# 📁 내부 DB 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# DB 파일 존재 확인
print(f"📁 DB 파일 확인: {os.path.exists(DB_PATH)} ({DB_PATH})")

# 전역 변수 - 사전 처리된 데이터 저장
_DB_INITIALIZED = False
_PROCESSED_DB = None
_VECTORIZER = None
_TFIDF_MATRIX = None

# 초기화 함수 - 앱 시작 시 한 번만 실행
@st.cache_data(ttl=86400, show_spinner=False)
def initialize_db():
    """데이터베이스와 벡터라이저 초기화"""
    global _DB_INITIALIZED, _PROCESSED_DB, _VECTORIZER, _TFIDF_MATRIX
    
    try:
        df = pd.read_excel(DB_PATH)
        _PROCESSED_DB = df
        
        # 벡터화 미리 수행
        corpus = df['Project Title'].fillna("").astype(str).tolist()
        
        _VECTORIZER = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2),
            lowercase=True,
            max_features=5000  # 성능 최적화
        )
        
        _TFIDF_MATRIX = _VECTORIZER.fit_transform(corpus)
        _DB_INITIALIZED = True
        
        print(f"✅ 내부 DB 초기화 완료: {len(df)} 개 논문 로드됨")
        return True
    except Exception as e:
        print(f"❌ 내부 DB 초기화 실패: {e}")
        return False

# 🔥 간단한 키워드 추출 (한국어 → 영어) - 확장된 버전
def extract_and_translate_keywords(text):
    """한국어 입력을 영어 키워드로 변환"""
    # 🔥 확장된 매핑 테이블
    keyword_map = {
        # 운동/건강 관련 - 확장
        '운동': 'exercise physical activity fitness training workout',
        '체지방': 'body fat weight loss adipose tissue',
        '감량': 'weight loss reduction decrease',
        '다이어트': 'diet weight loss nutrition dietary',
        '근육': 'muscle strength training resistance',
        '건강': 'health wellness medical fitness',
        '스포츠': 'sports athletics performance competition',
        '비만': 'obesity overweight BMI body mass',
        '식이': 'dietary nutrition food eating',
        '칼로리': 'calorie energy metabolism burn',
        '근력': 'strength resistance training power',
        '지구력': 'endurance cardio aerobic stamina',
        '헬스': 'fitness health wellness gym',
        '트레이닝': 'training exercise workout routine',
        '체중': 'weight body mass scale',
        '신진대사': 'metabolism metabolic rate energy',
        
        # 환경 관련
        '환경': 'environment environmental pollution ecology',
        '오염': 'pollution contamination environmental waste',
        '미세플라스틱': 'microplastic plastic pollution marine ocean',
        '기후': 'climate change global warming temperature',
        '재활용': 'recycling waste management sustainability',
        '지구온난화': 'global warming climate change temperature',
        '생태계': 'ecosystem ecological environment biodiversity',
        
        # 에너지 관련
        '태양광': 'solar energy renewable photovoltaic panel',
        '신재생': 'renewable energy sustainable green',
        '배터리': 'battery energy storage power cell',
        '연료전지': 'fuel cell hydrogen energy power',
        '전기': 'electricity electrical power energy',
        '발전': 'power generation electricity energy',
        
        # 생물학 관련
        '유전자': 'gene genetic DNA molecular biology',
        '세포': 'cell cellular biology molecular membrane',
        '항생제': 'antibiotic antimicrobial resistance bacteria',
        '바이러스': 'virus viral infection disease pathogen',
        '박테리아': 'bacteria bacterial microbiology pathogen',
        '단백질': 'protein molecular biology biochemistry',
        '효소': 'enzyme biochemistry catalysis reaction',
        
        # 화학 관련
        '화학': 'chemistry chemical reaction synthesis compound',
        '촉매': 'catalyst catalysis chemical reaction',
        '나노': 'nano nanotechnology materials science',
        '분자': 'molecule molecular chemistry structure',
        '반응': 'reaction chemical synthesis process',
        
        # 물리학 관련
        '물리': 'physics mechanical quantum electromagnetic',
        '전자': 'electronics electronic circuit sensor device',
        '로봇': 'robot robotics automation artificial intelligence',
        '센서': 'sensor detection measurement device monitoring',
        '광학': 'optics optical light laser photon',
        
        # 컴퓨터/AI 관련
        '인공지능': 'artificial intelligence machine learning AI neural',
        '딥러닝': 'deep learning neural network AI',
        '앱': 'application software mobile technology',
        '데이터': 'data analysis statistics information',
        '알고리즘': 'algorithm computational programming',
        
        # 의학 관련
        '의학': 'medicine medical health clinical',
        '치료': 'treatment therapy medical healing',
        '약물': 'drug pharmaceutical medicine therapy',
        '질병': 'disease illness medical pathology',
        '진단': 'diagnosis medical detection screening'
    }
    
    # 입력 텍스트에서 키워드 찾기
    text_lower = text.lower()
    matched_keywords = []
    
    print(f"📝 입력 텍스트 분석: '{text_lower}'")
    
    for korean, english in keyword_map.items():
        if korean in text_lower:
            matched_keywords.extend(english.split())
            print(f"   매칭: '{korean}' → {english.split()}")
    
    # 기본 키워드가 없으면 텍스트를 단어별로 분리
    if not matched_keywords:
        # 영어 단어는 그대로 사용
        english_words = re.findall(r'[a-zA-Z]+', text)
        matched_keywords.extend(english_words)
        print(f"   영어 단어 추출: {english_words}")
        
        # 한국어 단어도 그대로 추가 (일부 논문 제목이 한국어일 수 있음)
        korean_words = re.findall(r'[가-힣]+', text)
        if korean_words:
            matched_keywords.extend(korean_words)
            print(f"   한국어 단어 추가: {korean_words}")
        
        # 🔥 추가: 공백으로 분리된 모든 단어 포함
        all_words = text.replace(',', ' ').replace('.', ' ').split()
        for word in all_words:
            if len(word) >= 2:
                matched_keywords.append(word)
        print(f"   모든 단어 추가: {all_words}")
    
    # 중복 제거 및 최대 10개로 확장 (더 많은 키워드로 검색 범위 확대)
    unique_keywords = list(set(matched_keywords))[:10]
    
    print(f"🔍 키워드 변환: '{text}' → {unique_keywords}")
    return unique_keywords

# 🤖 간단한 요약 생성 - 에러 처리 강화
@st.cache_data(show_spinner=False, ttl=3600)
def generate_simple_summary(title, category=None, index=1):
    """간단한 프로젝트 요약 생성"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        
        prompt = f"제목: '{title}'"
        if category:
            prompt += f" (분야: {category})"
        prompt += "\n\n위 과학 프로젝트 제목을 보고 3-4문장으로 내용을 추론해서 설명해주세요. '~로 추정됩니다' 표현을 사용하세요."
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        print(f"⚠️ 요약 생성 오류: {e}")
        return f"이 프로젝트는 '{title}'에 관한 연구로 추정됩니다."

# 🎯 메인 검색 함수 - 디버깅 강화 및 임계값 조정
def search_similar_titles(user_input: str, max_results: int = 5):
    """간단하고 정확한 검색 함수"""
    global _DB_INITIALIZED, _PROCESSED_DB, _VECTORIZER, _TFIDF_MATRIX
    
    print(f"🔍 검색 시작: '{user_input}'")
    
    # DB 초기화
    if not _DB_INITIALIZED:
        print("🔄 DB 초기화 중...")
        initialize_db()
    
    if _PROCESSED_DB is None:
        print("⚠️ 전역 DB 없음, 직접 로드 시도...")
        df = pd.read_excel(DB_PATH)
    else:
        df = _PROCESSED_DB
    
    if df.empty:
        print("❌ DB가 비어있음")
        return []
    
    # 1. 키워드 추출 및 변환
    print("📝 1단계: 키워드 추출 및 변환")
    keywords = extract_and_translate_keywords(user_input)
    if not keywords:
        print("❌ 키워드 추출 실패")
        return []
    
    search_query = " ".join(keywords)
    print(f"🎯 최종 검색어: '{search_query}'")
    
    # 2. 유사도 계산
    print("🔢 2단계: 유사도 계산")
    try:
        if _VECTORIZER is not None and _TFIDF_MATRIX is not None:
            search_vector = _VECTORIZER.transform([search_query])
            cosine_sim = cosine_similarity(search_vector, _TFIDF_MATRIX)[0]
            print(f"   ✅ 사전 계산된 벡터 사용")
        else:
            # 새로 계산
            print("   ⚠️ 새로 벡터 계산 중...")
            corpus = df['Project Title'].fillna("").astype(str).tolist()
            corpus.append(search_query)
            
            vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            cosine_sim = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return []
    
    # 3. 결과 정렬 및 필터링
    print("📊 3단계: 결과 분석")
    result_df = df.copy()
    result_df['score'] = cosine_sim
    
    # 🔥 상위 결과 확인 로그 추가
    print(f"🔢 유사도 계산 완료, 상위 10개 결과:")
    top_10 = result_df.nlargest(10, 'score')[['Project Title', 'Category', 'score']]
    for idx, row in top_10.iterrows():
        print(f"  {row['score']:.6f}: [{row.get('Category', 'N/A')}] {row['Project Title'][:50]}...")
    
    # 🔥 더 낮은 임계값으로 점진적 시도
    thresholds = [0.05, 0.02, 0.01, 0.005, 0.001]  # 더 낮은 임계값 추가
    filtered_df = None
    
    for threshold in thresholds:
        filtered_df = result_df[result_df['score'] > threshold]
        result_count = len(filtered_df)
        print(f"   임계값 {threshold}: {result_count}개 결과")
        
        # 적당한 수의 결과가 나오면 중단
        if 1 <= result_count <= 20:  # 범위 확대 (15→20)
            print(f"   ✅ 임계값 {threshold} 선택 ({result_count}개)")
            break
    
    if filtered_df is None or filtered_df.empty:
        print("❌ 관련 프로젝트를 찾을 수 없음")
        return []
    
    # 4. 상위 결과만 선택 (최대 5개)
    top_df = filtered_df.sort_values(by='score', ascending=False).head(max_results)
    
    print(f"📋 선택된 결과 ({len(top_df)}개):")
    for idx, row in top_df.iterrows():
        print(f"  {row['score']:.4f}: [{row.get('Category', 'N/A')}] {row['Project Title'][:60]}...")
    
    # 5. 결과 구성 - 에러 처리 강화
    print("🏗️ 4단계: 결과 구성 및 요약 생성")
    results = []
    for i, (_, row) in enumerate(top_df.iterrows()):
        try:
            # 간단한 요약 생성
            summary = generate_simple_summary(
                row.get('Project Title', ''), 
                row.get('Category', ''),
                i + 1
            )
        except Exception as e:
            print(f"⚠️ 요약 생성 실패 ({i+1}번): {e}")
            summary = f"이 프로젝트는 '{row.get('Project Title', '')}'에 관한 연구로 추정됩니다."
        
        result_item = {
            '제목': row.get('Project Title', ''),
            '연도': str(row.get('Year', '')),
            '분야': row.get('Category', ''),
            '국가': row.get('Fair Country', ''),
            '지역': row.get('Fair State', ''),
            '수상': row.get('Awards', ''),
            '요약': summary,
            'score': float(row.get('score', 0))
        }
        results.append(result_item)
    
    print(f"✅ 검색 완료: {len(results)}개 결과 반환")
    return results

# 내부 DB 로드 함수 (폴백용)
@st.cache_data(ttl=3600)
def load_internal_db():
    """기본 DB 로드 함수"""
    try:
        df = pd.read_excel(DB_PATH)
        return df
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        return pd.DataFrame()

# 🧪 테스트 함수 추가
def test_search():
    """간단한 검색 테스트"""
    test_queries = ["운동", "exercise", "체지방", "환경", "운동과 체지방 감량"]
    for query in test_queries:
        print(f"\n🧪 테스트: '{query}'")
        try:
            results = search_similar_titles(query, max_results=3)
            print(f"✅ 결과: {len(results)}개")
            if results:
                for i, result in enumerate(results[:2]):  # 상위 2개만 출력
                    print(f"  {i+1})점수:{result['score']:.4f} - {result['제목'][:50]}...")
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
        print("-" * 50)

# 사용 예시 (개발/테스트용)
if __name__ == "__main__":
    print("🚀 검색 엔진 테스트 시작...")
    test_search()

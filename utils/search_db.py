# 수정된 search_db.py - 누락된 함수 추가 및 중복 제거

import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic
import re

# 📁 내부 DB 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

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
        # Excel 파일 로드
        df = pd.read_excel(DB_PATH)
        _PROCESSED_DB = df
        
        # 벡터화 미리 수행
        title_field = 'Project Title'
        corpus = df[title_field].fillna("").astype(str).tolist()
        
        _VECTORIZER = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2),
            lowercase=True
        )
        
        _TFIDF_MATRIX = _VECTORIZER.fit_transform(corpus)
        _DB_INITIALIZED = True
        
        print(f"✅ 내부 DB 초기화 완료: {len(df)} 개 논문 로드됨")
        return True
    except Exception as e:
        print(f"❌ 내부 DB 초기화 실패: {e}")
        return False

# 키워드 추출 함수
def extract_keywords(text, top_n=5):
    """텍스트에서 중요 키워드 추출"""
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    stopwords = [
        '이', '가', '을', '를', '에', '에서', '로', '으로', '의', '는', '은', '도', '만', 
        '부터', '까지', '와', '과', '하고', '에게', '한테', '께', '하다', '있다', '되다',
        'the', 'of', 'and', 'a', 'to', 'in', 'is', 'that', 'for', 'on', 'with', 'as', 
        'be', 'by', 'from', 'at', 'or'
    ]
    
    words = []
    for word in text.split():
        if len(word) >= 2 and word not in stopwords and not word.isdigit():
            # 한국어 조사 제거
            if any('\uAC00' <= char <= '\uD7A3' for char in word):
                if word.endswith(('이', '가', '을', '를', '에', '로', '의', '는', '은')):
                    word = word[:-1]
                elif word.endswith(('에서', '으로', '에게', '한테')):
                    word = word[:-2]
            words.append(word)
    
    # 단어 빈도 계산
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # 빈도순 정렬
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [word for word, _ in sorted_words[:top_n]]
    
    return top_keywords

# ⭐ 누락된 함수 추가: 키워드 번역 함수
@st.cache_data(show_spinner=False, ttl=3600)
def claude_translate_keywords(keywords, tgt_lang="en"):
    """키워드를 영어로 번역"""
    if not keywords:
        return []
        
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        keyword_text = ", ".join(keywords)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            system=f"다음 키워드들을 {tgt_lang}로 번역해주세요. 번역된 키워드만 쉼표로 구분하여 알려주세요.",
            messages=[
                {"role": "user", "content": keyword_text}
            ]
        )
        
        translated = response.content[0].text.strip()
        return [k.strip() for k in translated.split(',')]
    except Exception as e:
        print(f"키워드 번역 중 오류: {e}")
        return keywords

# 일괄 처리 함수 - Claude API 효율화
@st.cache_data(show_spinner=False, ttl=3600)
def batch_infer_content(titles, categories=None):
    """여러 프로젝트 제목을 한 번에 처리하여 Claude API 호출 최소화"""
    if not titles:
        return []
    
    print(f"=== 일괄 요약 생성 시작: {len(titles)}개 논문 ===")    
    try:
        client = anthropic.Anthropic(api_key=st.secrets["api"]["claude_key"])
        
        # 제목이 너무 많으면 5개씩 분할 처리
        if len(titles) > 5:
            print(f"⚠️ 제목이 {len(titles)}개로 많음, 5개씩 분할 처리")
            all_summaries = []
            for i in range(0, len(titles), 5):
                batch_titles = titles[i:i+5]
                batch_categories = categories[i:i+5] if categories else None
                batch_summaries = batch_infer_content(batch_titles, batch_categories)
                all_summaries.extend(batch_summaries)
            return all_summaries
        
        # 범주 정보 추가
        prompts = []
        for i, title in enumerate(titles):
            category = categories[i] if categories and i < len(categories) else None
            if category:
                prompts.append(f"{i+1}. '{title}' (분야: {category})")
            else:
                prompts.append(f"{i+1}. '{title}'")
        
        # 시스템 프롬프트
        system_prompt = """
        과학 논문 제목을 보고 내용을 추론해서 설명해주세요.
        
        규칙:
        1. 각 논문마다 번호를 붙여서 설명 (1., 2., 3. ...)
        2. 제목만 보고 추론하므로 "~로 추정됩니다", "~일 것으로 보입니다" 표현 사용
        3. 각 설명은 3-4문장으로 간결하게
        4. 전문용어는 쉽게 풀어서 설명
        
        형식 예시:
        1. 이 연구는 [주제]에 관한 것으로 추정됩니다. [예상 내용 설명]. 이는 [의의/응용분야]에 도움이 될 것으로 보입니다.
        """
        
        # 사용자 프롬프트 작성
        user_prompt = "다음 과학 논문 제목들을 분석해주세요:\n\n" + "\n".join(prompts)
        
        # Claude API 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.5,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        full_response = response.content[0].text.strip()
        print(f"✅ Claude 응답 받음: {len(full_response)} 글자")
        
        # 응답 파싱
        summaries = []
        lines = full_response.split('\n')
        current_summary = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 번호로 시작하는 라인 감지 (1., 2., 3. 등)
            number_match = re.match(r'^(\d+)\.', line)
            if number_match:
                # 이전 요약 저장
                if current_summary:
                    summaries.append(current_summary.strip())
                # 새 요약 시작
                current_summary = line
            else:
                # 현재 요약에 라인 추가
                if current_summary:
                    current_summary += " " + line
        
        # 마지막 요약 저장
        if current_summary:
            summaries.append(current_summary.strip())
        
        # 부족한 요약 보충
        while len(summaries) < len(titles):
            idx = len(summaries)
            title = titles[idx] if idx < len(titles) else "Unknown"
            fallback_summary = f"{idx+1}. 이 프로젝트는 '{title}'에 관한 연구로 추정됩니다."
            summaries.append(fallback_summary)
        
        # 초과 요약 제거
        if len(summaries) > len(titles):
            summaries = summaries[:len(titles)]
        
        print(f"✅ 일괄 요약 완료: {len(summaries)}개")
        return summaries
    
    except Exception as e:
        print(f"❌ 일괄 추론 오류: {e}")
        # 에러 발생시 폴백
        return [f"{i+1}. 이 프로젝트는 '{title}'에 관한 연구로 추정됩니다. (요약 생성 중 오류 발생)" 
                for i, title in enumerate(titles)]

# 내부 DB 로드 함수
@st.cache_data(ttl=3600)
def load_internal_db():
    """기본 DB 로드 함수"""
    try:
        df = pd.read_excel(DB_PATH)
        return df
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        return pd.DataFrame()

# 메인 검색 함수
def search_similar_titles(user_input: str, max_results: int = 10):
    """메인 검색 함수 - 사용자 입력으로 유사한 논문 제목들을 검색"""
    global _DB_INITIALIZED, _PROCESSED_DB, _VECTORIZER, _TFIDF_MATRIX
    
    print(f"🔍 검색 시작: '{user_input}'")
    
    # DB 초기화 확인
    if not _DB_INITIALIZED:
        initialize_db()
    
    # DB 로드
    if _PROCESSED_DB is None:
        df = load_internal_db()
    else:
        df = _PROCESSED_DB
    
    if df.empty:
        print("❌ DB가 비어있음")
        return []
    
    # 1. 키워드 추출
    print("📝 키워드 추출 중...")
    keywords = extract_keywords(user_input)
    print(f"   추출된 키워드: {keywords}")
    
    if not keywords:
        print("❌ 키워드 추출 실패")
        return []
    
    # 2. 키워드 번역
    print("🌐 키워드 번역 중...")
    translated_keywords = claude_translate_keywords(keywords)
    print(f"   번역된 키워드: {translated_keywords}")
    
    if not translated_keywords:
        translated_keywords = keywords
    
    search_query = " ".join(translated_keywords)
    print(f"   최종 검색어: '{search_query}'")
    
    # 3. 유사도 계산
    print("🔢 유사도 계산 중...")
    try:
        if _VECTORIZER is not None and _TFIDF_MATRIX is not None:
            # 사전 처리된 벡터 사용
            search_vector = _VECTORIZER.transform([search_query])
            cosine_sim = cosine_similarity(search_vector, _TFIDF_MATRIX)[0]
            print(f"   벡터화 성공, {len(cosine_sim)}개 문서와 비교")
        else:
            # 새로 계산
            print("   새로 벡터화 계산...")
            title_field = 'Project Title'
            corpus = df[title_field].fillna("").astype(str).tolist()
            corpus.append(search_query)
            
            vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(corpus)
            cosine_sim = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
            print(f"   새로 벡터화 완료, {len(cosine_sim)}개 문서와 비교")
    except Exception as e:
        print(f"❌ 검색 벡터화 오류: {e}")
        return []
    
    # 4. 결과 정렬 및 필터링
    print("📊 결과 분석 중...")
    result_df = df.copy()
    result_df['score'] = cosine_sim
    
    # 상위 결과 확인
    top_scores = result_df.nlargest(10, 'score')[['Project Title', 'Category', 'score']]
    print("   상위 10개 유사도 점수:")
    for idx, row in top_scores.iterrows():
        print(f"     {row['score']:.6f}: [{row.get('Category', 'N/A')}] {row['Project Title'][:60]}...")
    
    # 임계값 설정
    threshold = 0.005
    filtered_df = result_df[result_df['score'] > threshold].copy()
    
    if filtered_df.empty:
        print("❌ 관련 프로젝트를 찾을 수 없음")
        return []
    
    # 상위 결과 선택
    top_df = filtered_df.sort_values(by='score', ascending=False).head(max_results)
    print(f"   최종 선택: {len(top_df)}개")
    
    # 5. AI 요약 생성
    titles = [row.get('Project Title', '') for _, row in top_df.iterrows()]
    categories = [row.get('Category', '') for _, row in top_df.iterrows()]
    
    if titles:
        print("🤖 AI 요약 생성 중...")
        summaries = batch_infer_content(titles, categories)
        print(f"   생성된 요약: {len(summaries)}개")
    else:
        summaries = []
    
    # 6. 결과 구성
    results = []
    for i, (_, row) in enumerate(top_df.iterrows()):
        summary = ""
        if i < len(summaries):
            summary_text = summaries[i]
            summary = re.sub(r'^\d+\.\s*', '', summary_text)
        else:
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

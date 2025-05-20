# search_db.py 수정 버전
import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.explain_topic import explain_topic
from openai import OpenAI
import re

# 📁 내부 DB 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# 🔤 ISEF DB 열 매핑 (수정됨)
COLUMN_MAP = {
    'Project Title': '제목',
    'Year': '연도',
    'Category': '분야',
    'Fair Country': '국가',
    'Fair State': '지역',
    'Awards': '수상'
}

# 키워드 추출 함수 (NLTK 없이 구현)
def extract_keywords(text, top_n=5):
    """텍스트에서 중요 키워드 추출 - 간단한 버전"""
    # 특수문자 제거 및 소문자화
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # 한국어 및 영어 불용어 (확장)
    stopwords = ['이', '그', '저', '것', '및', '등', '를', '을', '에', '에서', '의', '으로', '로', '에게', '하다', '있다', '되다',
                'the', 'of', 'and', 'a', 'to', 'in', 'is', 'that', 'for', 'on', 'with']
    
    # 단어 분리 및 불용어 제거
    words = []
    for word in text.split():
        if word not in stopwords and len(word) > 1:  # 2글자 이상만 포함
            words.append(word)
    
    # 빈도수 기반 키워드 추출
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # 빈도순 정렬 및 상위 키워드 반환
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]

# ✅ GPT 번역 함수 (키워드만 번역)
@st.cache_data(show_spinner=False)
def gpt_translate_keywords(keywords, tgt_lang="en") -> list:
    """키워드 리스트만 번역 (API 호출 최소화)"""
    if not keywords:
        return []
        
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        # 키워드를 한 번에 번역 요청
        keyword_text = ", ".join(keywords)
        prompt = f"다음 키워드들을 {tgt_lang}로 번역해주세요. 번역된 키워드만 쉼표로 구분하여 알려주세요: {keyword_text}"
        
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # 번역된 키워드 파싱
        translated = res.choices[0].message.content.strip()
        return [k.strip() for k in translated.split(',')]
    except Exception as e:
        st.warning(f"키워드 번역 중 오류: {e}")
        return keywords  # 실패 시 원본 반환

# ✅ 프로젝트 내용 추론 함수 (수정됨)
def infer_project_content(title, category=None):
    """프로젝트 제목과 카테고리를 바탕으로 내용 추론"""
    try:
        prompt = title
        if category:
            prompt = f"{title} (연구 분야: {category})"
            
        explanation = explain_topic(prompt)[0]
        return explanation
    except Exception as e:
        return f"이 프로젝트는 '{title}'에 관한 연구입니다."

# ✅ 내부 DB 로드 및 정제
def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
        
        # 열 이름 원본 유지 (소문자화 하지 않음)
        for orig_col, new_col in COLUMN_MAP.items():
            if orig_col in df.columns:
                df[new_col] = df[orig_col]
        
        # 참가자 이름(Finalist) 열은 사용하지 않음
        
        return df
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

# ✅ 새로운 유사 프로젝트 검색 함수
def search_similar_titles(user_input, max_results=5):
    # DB 로드
    df = load_internal_db()
    
    # DB가 비어있으면 빈 결과 반환
    if df.empty:
        st.error("❌ 내부 DB가 비어있거나 로드할 수 없습니다.")
        return []
    
    # 1. 사용자 입력에서 키워드 추출
    keywords = extract_keywords(user_input)
    
    # 키워드가 없으면 빈 결과 반환
    if not keywords:
        st.warning("⚠️ 입력에서 키워드를 추출할 수 없습니다.")
        return []
    
    # 2. 키워드만 번역 (API 호출 최소화)
    translated_keywords = gpt_translate_keywords(keywords)
    
    if not translated_keywords:
        translated_keywords = keywords  # 번역 실패 시 원본 사용
    
    # 3. 검색용 쿼리 생성
    search_query = " ".join(translated_keywords)
    
    # 4. 유사도 분석 준비
    # 영어 제목 필드 사용 (ISEF DB는 영어 제목)
    title_field = 'Project Title'
    
    # 제목 필드가 없으면 오류 반환
    if title_field not in df.columns:
        st.error(f"❌ DB에 '{title_field}' 필드가 없습니다.")
        return []
    
    # 안전하게 corpus 생성
    corpus = df[title_field].fillna("").astype(str).tolist()
    corpus.append(search_query)  # 마지막에 검색어 추가
    
    try:
        # 단어 수준 분석
        vectorizer = TfidfVectorizer(
            analyzer='word', 
            ngram_range=(1, 2),
            lowercase=True,
            max_features=5000
        )
        
        tfidf_matrix = vectorizer.fit_transform(corpus)
        
        # 마지막 행(검색어)과 나머지 행(DB) 사이의 유사도 계산
        cosine_sim = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
        
        # 유사도 점수가 올바른 길이인지 확인
        if len(cosine_sim) != len(df):
            st.error(f"❌ 유사도 벡터 길이({len(cosine_sim)})와 데이터프레임 길이({len(df)})가 일치하지 않습니다.")
            return []
            
    except Exception as e:
        st.error(f"❌ 유사도 분석 오류: {str(e)}")
        return []
    
    # 5. 결과 데이터프레임 생성 (원본 수정 방지)
    result_df = df.copy()
    result_df['score'] = cosine_sim
    
    # 최소 유사도 임계값 적용
    filtered_df = result_df[result_df['score'] > 0.05].copy()  # 임계값 낮춤
    
    # 결과가 없으면 빈 리스트 반환
    if filtered_df.empty:
        return []
    
    # 6. 상위 결과 선택
    top_df = filtered_df.sort_values(by='score', ascending=False).head(max_results)
    
    # 7. 결과 리스트 구성 (파이널리스트 정보 제외)
    results = []
    for _, row in top_df.iterrows():
        # 기본 정보 가져오기
        project_title = row.get('Project Title', '')
        category = row.get('Category', '')
        
        # AI로 프로젝트 내용 추론
        project_summary = infer_project_content(project_title, category)
        
        # 결과 딕셔너리 구성
        result_item = {
            '제목': project_title,
            '요약': project_summary,
            '연도': str(row.get('Year', '')),
            '분야': category,
            '국가': row.get('Fair Country', ''),
            '지역': row.get('Fair State', ''),
            '수상': row.get('Awards', ''),
            'score': float(row.get('score', 0))
        }
        
        results.append(result_item)
    
    return results

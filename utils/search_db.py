# utils/search_db.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import streamlit as st

# 파일 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# 열 이름 매핑 (영문 → 한글)
COLUMN_MAP = {
    'project title': '제목',
    'year': '연도',
    'category': '분야'
}

def load_internal_db():
    """내부 DB 엑셀 파일 로드 및 컬럼명 변환"""
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 파일을 불러오는 중 오류 발생: {e}")
        st.stop()

    # 열 이름 표준화 및 한글로 매핑
    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns=lambda c: COLUMN_MAP.get(c, c), inplace=True)

    # 필드 기본값 처리
    df['제목'] = df.get('제목', pd.Series(["제목 없음"] * len(df))).fillna("제목 없음").astype(str)
    df['요약'] = df.get('요약', pd.Series(["요약 없음"] * len(df))).fillna("요약 없음").astype(str)
    df['분야'] = df.get('분야', pd.Series(["분야 없음"] * len(df))).fillna("분야 없음").astype(str)
    df['연도'] = df.get('연도', pd.Series(["연도 없음"] * len(df))).fillna("연도 없음").astype(str)

    return df

def search_similar_titles(user_input, max_results=5):
    """입력된 주제와 유사한 논문 제목을 내부 DB에서 검색"""
    df = load_internal_db()

    # TF-IDF 유사도 기반 검색 (char 기반 n-gram 분석)
    corpus = df['제목'].tolist() + [user_input]

    try:
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',         # ✅ 단어 아닌 문자 기반 분석
            ngram_range=(3, 5),         # ✅ 3~5 글자 단위 비교
            lowercase=True
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 계산 중 오류 발생: {e}")
        st.stop()

    df['score'] = cosine_sim
    results = df.sort_values(by='score', ascending=False).head(max_results)

    return results[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')

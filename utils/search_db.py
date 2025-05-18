# utils/search_db.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import streamlit as st

# 파일 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

def load_internal_db():
    """엑셀 DB 로드"""
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 파일을 불러오는 중 오류 발생: {e}")
        st.stop()

    # 열 이름 소문자+공백 제거 처리
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def search_similar_titles(user_input, max_results=5):
    """입력된 주제와 유사한 논문 제목을 내부 DB에서 검색"""
    df = load_internal_db()

    # 필수 열 체크
    required_cols = ['제목', '요약', '연도', '분야']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"❗ 내부 DB 파일에 다음 열이 없습니다: {', '.join(missing_cols)}")
        st.stop()

    titles = df['제목'].fillna("").astype(str).tolist()
    corpus = titles + [user_input]

    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 계산 중 오류 발생: {e}")
        st.stop()

    df['score'] = cosine_sim
    results = df.sort_values(by='score', ascending=False).head(max_results)

    return results[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')


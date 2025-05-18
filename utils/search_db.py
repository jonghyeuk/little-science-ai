# utils/search_db.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# 파일 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

def load_internal_db():
    """엑셀 DB 로드"""
    df = pd.read_excel(DB_PATH)
    # 열 이름 표준화
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def search_similar_titles(user_input, max_results=5):
    """입력된 주제와 유사한 논문 제목을 내부 DB에서 검색"""
    df = load_internal_db()
    
    if '제목' not in df.columns:
        raise ValueError("엑셀 파일에 '제목' 컬럼이 없습니다. 열 이름을 확인하세요.")

    titles = df['제목'].fillna("").astype(str).tolist()
    corpus = titles + [user_input]  # 마지막에 사용자 입력 추가

    # TF-IDF 기반 유사도 측정
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

    df['score'] = cosine_sim
    results = df.sort_values(by='score', ascending=False).head(max_results)

    return results[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')

import pandas as pd
import os
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.explain_topic import explain_topic
from openai import OpenAI

# 📁 내부 DB 경로
DB_PATH = os.path.join("data", "ISEF Final DB.xlsx")

# 🔤 열 이름 매핑
COLUMN_MAP = {
    'project title': '제목',
    'year': '연도',
    'category': '분야'
}

# ✅ GPT 번역 함수 (캐시 사용)
@st.cache_data(show_spinner=False)
def gpt_translate(text: str, tgt_lang="en") -> str:
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        prompt = f"다음 문장을 {tgt_lang} 언어로 자연스럽게 번역해줘: '{text}'"
        res = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return text

# ✅ 요약 생성 함수
def get_summary(title):
    try:
        return explain_topic(title)[0]
    except:
        return "요약 없음"

# ✅ 내부 DB 로드 및 정제
def load_internal_db():
    try:
        df = pd.read_excel(DB_PATH)
    except Exception as e:
        st.error(f"❌ 내부 DB 로드 실패: {e}")
        st.stop()

    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns=lambda c: COLUMN_MAP.get(c, c), inplace=True)

    df['제목'] = df.get('제목', pd.Series(["제목 없음"] * len(df))).fillna("제목 없음").astype(str)
    df['요약'] = df.get('요약', pd.Series([""] * len(df))).fillna("").astype(str)
    df['분야'] = df.get('분야', pd.Series(["분야 없음"] * len(df))).fillna("분야 없음").astype(str)
    df['연도'] = df.get('연도', pd.Series(["연도 없음"] * len(df))).fillna("연도 없음").astype(str)

    return df

# ✅ 유사 논문 검색
def search_similar_titles(user_input, max_results=5):
    df = load_internal_db()

    # 🔁 입력 주제 GPT 번역
    translated_input = gpt_translate(user_input)

    # 🔁 DB 제목 리스트 번역
    unique_titles = list(set(df['제목'].tolist()))
    translated_map = {t: gpt_translate(t) for t in unique_titles}
    df['제목_번역'] = df['제목'].map(translated_map)

    # 🔍 TF-IDF 유사도 분석
    corpus = df['제목_번역'].tolist() + [translated_input]
    try:
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), lowercase=True)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    except Exception as e:
        st.error(f"❌ 유사도 분석 오류: {e}")
        st.stop()

    df['score'] = cosine_sim
    df = df[df['score'] > 0]

    top = df.sort_values(by='score', ascending=False).head(max_results)

    # ⛓ 요약 생성 보완
    top['요약'] = top.apply(
        lambda row: row['요약'].strip() if row['요약'].strip() else get_summary(row['제목']),
        axis=1
    )

    return top[['제목', '요약', '연도', '분야', 'score']].to_dict(orient='records')

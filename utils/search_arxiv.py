# utils/search_arxiv.py

import urllib.parse
import feedparser
import streamlit as st
from deep_translator import GoogleTranslator

def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"

    # ✅ Step 1: 쿼리를 영어로 번역
    try:
        translated_query = GoogleTranslator(source='auto', target='en').translate(query)
    except Exception as e:
        st.error(f"❌ 검색어 번역 중 오류 발생: {e}")
        translated_query = query  # fallback

    encoded_query = urllib.parse.quote(translated_query)
    query_url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}"

    try:
        feed = feedparser.parse(query_url)

        if not feed.entries:
            return [{
                "title": "검색 결과 없음",
                "summary": "해당 주제와 관련된 arXiv 논문을 찾을 수 없습니다.",
                "link": "",
                "source": "arXiv"
            }]

        results = []
        for entry in feed.entries:
            title_en = entry.title
            summary_en = entry.get("summary", "")

            # ✅ Step 2: 결과 번역 (제목 + 요약)
            try:
                title_ko = GoogleTranslator(source='en', target='ko').translate(title_en)
                summary_ko = GoogleTranslator(source='en', target='ko').translate(summary_en)
            except:
                title_ko = title_en
                summary_ko = summary_en

            # ✅ Step 3: 한국어 + 영어 병기 표시
            results.append({
                "title": f"{title_ko}  
<sub><i>{title_en}</i></sub>",
                "summary": summary_ko,
                "link": entry.link,
                "source": "arXiv"
            })

        return results

    except Exception as e:
        st.error(f"❌ arXiv 검색 중 오류가 발생했습니다: {e}")
        return [{
            "title": "arXiv 검색 실패",
            "summary": str(e),
            "link": "",
            "source": "arXiv"
        }]

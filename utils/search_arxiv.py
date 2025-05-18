# utils/search_arxiv.py

import urllib.parse
import feedparser
import streamlit as st
from deep_translator import GoogleTranslator

def translate(text, src="en", tgt="ko"):
    """번역기 래퍼 함수"""
    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except:
        return text

def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"

    # ✅ Step 1: 한글 주제를 영어로 변환
    try:
        translated_query = translate(query, src='auto', tgt='en')
    except Exception as e:
        st.error(f"❌ 검색어 번역 실패: {e}")
        translated_query = query

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
            link = entry.link

            # ✅ Step 2: 결과 병기 처리
            title_ko = translate(title_en)
            summary_ko = translate(summary_en)

            results.append({
                "title": f"{title_ko} \n({title_en})",     # 병기
                "summary": summary_ko,
                "link": link,
                "source": "arXiv"
            })

        return results

    except Exception as e:
        st.error(f"❌ arXiv 검색 중 오류: {e}")
        return [{
            "title": "arXiv 검색 실패",
            "summary": "",
            "link": "",
            "source": "arXiv"
        }]

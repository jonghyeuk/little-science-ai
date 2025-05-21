import urllib.parse
import feedparser
import streamlit as st
from openai import OpenAI  # 검색어 번역용

# 검색어 번역 함수 추가
def translate_to_english(query):
    """한글 검색어를 영어로 번역"""
    try:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 빠른 모델 사용
            messages=[
                {"role": "system", "content": "한국어를 영어로 번역해주세요. 번역만 제공하고 다른 설명은 하지 마세요."},
                {"role": "user", "content": query}
            ]
        )
        translated = response.choices[0].message.content.strip()
        print(f"번역: '{query}' → '{translated}'")
        return translated
    except Exception as e:
        print(f"번역 오류: {e}")
        return query  # 오류 발생 시 원본 검색어 사용

# arXiv 검색 함수 수정
def search_arxiv(query, max_results=5):
    # 1. 한글 검색어 번역
    if any('\uAC00' <= c <= '\uD7A3' for c in query):  # 한글 포함 확인
        english_query = translate_to_english(query)
    else:
        english_query = query
        
    # 2. 검색 쿼리 형식 최적화
    base_url = "http://export.arxiv.org/api/query"
    
    # 검색어를 AND로 결합하여 더 많은 결과 반환
    words = english_query.split()
    if len(words) > 1:
        search_term = " AND ".join(words)
    else:
        search_term = english_query
        
    encoded_query = urllib.parse.quote(search_term)
    query_url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}"
    
    print(f"arXiv API 요청 URL: {query_url}")
    
    try:
        # Feed 파싱
        feed = feedparser.parse(query_url)
        
        if hasattr(feed, 'status'):
            print(f"arXiv API 응답 상태: {feed.status}")
        
        entries = feed.entries
        print(f"검색 결과 수: {len(entries)}")
        
        if not entries:
            # 검색 실패 시 더 일반적인 용어로 재시도
            if len(words) > 1:
                # 가장 중요한 1-2개 단어만 사용해서 재검색
                important_words = words[:2]
                simplified_query = " ".join(important_words)
                encoded_simplified = urllib.parse.quote(simplified_query)
                simplified_url = f"{base_url}?search_query=all:{encoded_simplified}&start=0&max_results={max_results}"
                
                print(f"단순화된 검색 시도: {simplified_url}")
                simplified_feed = feedparser.parse(simplified_url)
                entries = simplified_feed.entries
                
                if not entries:
                    return [{
                        "title": "검색 결과 없음",
                        "summary": f"해당 주제와 관련된 arXiv 논문을 찾을 수 없습니다. (검색어: {english_query})",
                        "link": "",
                        "source": "arXiv"
                    }]
        
        # 결과 구성
        results = []
        for entry in entries:
            title = entry.title.replace('\n', ' ').strip()
            summary = entry.get("summary", "").replace('\n', ' ').strip()
            
            # 긴 요약은 일부만 표시
            if len(summary) > 500:
                summary = summary[:497] + "..."
                
            link = entry.link
            
            results.append({
                "title": title,
                "summary": f"[영문 요약] {summary}",
                "link": link,
                "source": "arXiv"
            })
                
        return results
        
    except Exception as e:
        print(f"arXiv API 오류: {str(e)}")
        st.error(f"❌ arXiv 검색 중 오류 발생: {e}")
        return [{
            "title": "arXiv 검색 실패",
            "summary": f"오류 내용: {str(e)}",
            "link": "",
            "source": "arXiv"
        }]

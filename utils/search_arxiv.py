import urllib.parse
import feedparser
import streamlit as st
from utils.explain_topic import explain_topic  # ✅ GPT 설명 추론

# ✅ arXiv 논문 검색 및 요약 추론
def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query"
    encoded_query = urllib.parse.quote(query)
    query_url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}"
    
    # 디버깅 로그 추가 (나중에 제거 가능)
    print(f"arXiv API 요청 URL: {query_url}")
    
    try:
        # 🔍 Feed 파싱
        feed = feedparser.parse(query_url)
        
        # 응답 상태 확인 (디버깅용)
        if hasattr(feed, 'status'):
            print(f"arXiv API 응답 상태: {feed.status}")
        
        entries = feed.entries
        print(f"검색 결과 수: {len(entries)}")
        
        if not entries:
            return [{
                "title": "검색 결과 없음",
                "summary": "해당 주제와 관련된 arXiv 논문을 찾을 수 없습니다.",
                "link": "",
                "source": "arXiv"
            }]
            
        # 📌 결과 구성 (나머지는 동일)
        results = []
        for entry in entries:
            title = entry.title
            summary = entry.get("summary", "")
            link = entry.link
            # 🤖 GPT로 요약 추론
            try:
                explanation_lines = explain_topic(title)
                explanation = explanation_lines[0] if explanation_lines else summary
            except Exception as e:
                print(f"GPT 요약 오류: {str(e)}")
                explanation = summary or "요약 정보 없음"
                
            results.append({
                "title": f"{title}",
                "summary": explanation,
                "link": link,
                "source": "arXiv"
            })
        return results
    except Exception as e:
        print(f"arXiv API 오류: {str(e)}")  # 콘솔에 자세한 오류 출력
        st.error(f"❌ arXiv 검색 중 오류 발생: {e}")
        return [{
            "title": "arXiv 검색 실패",
            "summary": f"오류 내용: {str(e)}",
            "link": "",
            "source": "arXiv"
        }]

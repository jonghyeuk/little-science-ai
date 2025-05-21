import urllib.parse
import feedparser
import streamlit as st
from utils.explain_topic import explain_topic  # GPT API 사용 (선택적)

# arXiv 논문 검색 및 요약 표시
def search_arxiv(query, max_results=5, use_gpt=False):
    """
    arXiv API를 사용하여 학술 논문을 검색하고 결과를 반환합니다.
    
    use_gpt: True면 요약을 GPT로 번역/설명, False면 원본 영문 요약 사용 (빠름)
    """
    base_url = "http://export.arxiv.org/api/query"
    encoded_query = urllib.parse.quote(query)
    query_url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}"
    
    try:
        # Feed 파싱
        feed = feedparser.parse(query_url)
        entries = feed.entries
        
        if not entries:
            return [{
                "title": "검색 결과 없음",
                "summary": "해당 주제와 관련된 arXiv 논문을 찾을 수 없습니다.",
                "link": "",
                "source": "arXiv"
            }]
        
        # 결과 수집
        results = []
        
        # GPT 번역 사용하지 않는 빠른 모드 (기본값)
        if not use_gpt:
            for entry in entries:
                title = entry.title.replace('\n', ' ').strip()
                summary = entry.get("summary", "").replace('\n', ' ').strip()
                
                # 긴 요약은 일부만 표시
                if len(summary) > 500:
                    summary = summary[:497] + "..."
                    
                link = entry.link
                
                results.append({
                    "title": title,
                    "summary": f"[영문 요약] {summary}",  # 영문 요약임을 표시
                    "link": link,
                    "source": "arXiv"
                })
                
        # GPT 번역 모드 (느림)
        else:
            # 여기서는 원래 코드와 동일하게 동작
            for entry in entries:
                title = entry.title
                summary = entry.get("summary", "")
                link = entry.link
                
                try:
                    explanation_lines = explain_topic(title)
                    explanation = explanation_lines[0] if explanation_lines else summary
                except Exception as e:
                    explanation = summary or "요약 정보 없음"
                    
                results.append({
                    "title": title,
                    "summary": explanation,
                    "link": link,
                    "source": "arXiv"
                })
                
        return results
        
    except Exception as e:
        st.error(f"❌ arXiv 검색 중 오류 발생: {e}")
        return [{
            "title": "arXiv 검색 실패",
            "summary": f"오류 내용: {str(e)}",
            "link": "",
            "source": "arXiv"
        }]

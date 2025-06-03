# utils/modern_pdf_generator.py
from playwright.sync_api import sync_playwright
import os
import re
from datetime import datetime
import tempfile
import warnings

warnings.filterwarnings("ignore")

OUTPUT_DIR = "outputs"

def get_claude_style_template():
    """Claude/Notion 스타일의 HTML 템플릿"""
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - 연구탐색보고서</title>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Claude/Notion 스타일 디자인 */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.65;
            color: #374151;
            background: #ffffff;
            font-size: 14px;
            font-weight: 400;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 30px;
            background: white;
        }}
        
        /* 표지 스타일 */
        .cover {{
            text-align: center;
            padding: 80px 0;
            border-bottom: 1px solid #e5e7eb;
            margin-bottom: 60px;
        }}
        
        .cover h1 {{
            font-size: 32px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 16px;
            line-height: 1.3;
        }}
        
        .cover .subtitle {{
            font-size: 18px;
            color: #6b7280;
            margin-bottom: 40px;
            font-weight: 500;
        }}
        
        .cover .meta {{
            font-size: 14px;
            color: #9ca3af;
            margin-top: 30px;
        }}
        
        .cover .divider {{
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            margin: 30px auto;
            border-radius: 2px;
        }}
        
        /* 섹션 헤더 */
        .section-header {{
            margin: 50px 0 25px 0;
            padding-bottom: 12px;
            border-bottom: 2px solid #f3f4f6;
        }}
        
        .section-header h2 {{
            font-size: 24px;
            font-weight: 600;
            color: #111827;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .section-header.level-2 h3 {{
            font-size: 20px;
            font-weight: 600;
            color: #374151;
            margin: 30px 0 15px 0;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        /* 내용 블록 */
        .content-block {{
            margin: 20px 0;
            line-height: 1.7;
        }}
        
        .content-block p {{
            margin-bottom: 16px;
            color: #374151;
        }}
        
        /* 카드 스타일 (Claude 대화창 느낌) */
        .paper-card {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            transition: all 0.2s ease;
            position: relative;
        }}
        
        .paper-card:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border-color: #d1d5db;
        }}
        
        .paper-card .title {{
            font-size: 16px;
            font-weight: 600;
            color: #111827;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        
        .paper-card .source {{
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 12px;
            font-weight: 500;
        }}
        
        .paper-card .summary {{
            font-size: 14px;
            color: #4b5563;
            line-height: 1.6;
        }}
        
        .paper-card.isef {{
            border-left: 4px solid #3b82f6;
        }}
        
        .paper-card.arxiv {{
            border-left: 4px solid #10b981;
        }}
        
        /* 연구 계획 섹션 */
        .research-section {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 24px;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .research-section h4 {{
            font-size: 18px;
            font-weight: 600;
            color: #111827;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #f3f4f6;
        }}
        
        .research-section .content {{
            font-size: 14px;
            line-height: 1.7;
            color: #374151;
        }}
        
        /* 목록 스타일 */
        ul, ol {{
            margin: 16px 0;
            padding-left: 20px;
        }}
        
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        
        /* 강조 텍스트 */
        strong {{
            color: #111827;
            font-weight: 600;
        }}
        
        /* 이모지 아이콘 */
        .emoji {{
            font-size: 18px;
            margin-right: 8px;
        }}
        
        /* 페이지 브레이크 */
        .page-break {{
            page-break-before: always;
        }}
        
        /* 인쇄용 스타일 */
        @media print {{
            body {{
                font-size: 12px;
            }}
            .container {{
                padding: 20px;
            }}
            .paper-card {{
                break-inside: avoid;
            }}
            .research-section {{
                break-inside: avoid;
            }}
        }}
        
        /* 반응형 */
        @media (max-width: 768px) {{
            .container {{
                padding: 20px 15px;
            }}
            .cover h1 {{
                font-size: 28px;
            }}
            .section-header h2 {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

def clean_text_minimal(text):
    """최소한의 텍스트 정리"""
    if not text:
        return ""
    
    text = str(text)
    
    # 기본적인 정리만
    text = re.sub(r'#{1,6}\s*', '', text)  # 마크다운 헤더 제거
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)  # **볼드** → <strong>
    text = re.sub(r'[`]', '', text)  # 백틱 제거
    text = re.sub(r'https?://[^\s\)]+', '', text)  # URL 제거
    
    # 줄바꿈을 <br>로 변환 (일부만)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = re.sub(r'\n', '<br>', text)
    
    # 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def extract_topic_from_content(content):
    """내용에서 주제 추출"""
    try:
        patterns = [
            r'# 📘\s*([^\n-]+?)(?:\s*-|$)',
            r'주제[:\s]*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                topic = re.sub(r'주제\s*해설', '', topic).strip()
                if len(topic) > 3:
                    return topic[:50] if len(topic) > 50 else topic
        
        return "과학 연구 탐색"
    except:
        return "과학 연구 탐색"

def parse_content_smart(content):
    """스마트한 내용 파싱 - Claude 결과에 최적화"""
    result = {
        'topic_explanation': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        # 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            result['topic_explanation'] = explanation_match.group(1).strip()
        
        # ISEF 논문 추출
        if "ISEF" in content and ("출품논문" in content or "International" in content):
            isef_section = content[content.find("ISEF"):content.find("arXiv") if "arXiv" in content else len(content)]
            
            # 카드 형태로 추출 (Claude가 생성한 형태)
            card_pattern = r'<div[^>]*background-color[^>]*>.*?<h3[^>]*>📌\s*([^<]+)</h3>.*?<p[^>]*>([^<]+)</p>'
            cards = re.findall(card_pattern, isef_section, re.DOTALL)
            
            if not cards:
                # 대안 패턴
                title_pattern = r'📌\s*([^\n]+)'
                titles = re.findall(title_pattern, isef_section)
                
                for title in titles[:3]:
                    # 각 제목 다음의 내용 찾기
                    title_pos = isef_section.find(title)
                    next_title_pos = isef_section.find('📌', title_pos + 1)
                    if next_title_pos == -1:
                        next_title_pos = len(isef_section)
                    
                    section_content = isef_section[title_pos:next_title_pos]
                    # 메타 정보와 설명 추출
                    lines = section_content.split('\n')[1:4]  # 제목 다음 3줄
                    summary = ' '.join([line.strip() for line in lines if line.strip() and not line.strip().startswith('📅')])
                    
                    if len(summary) > 20:
                        result['isef_papers'].append((title.strip(), summary))
            else:
                for title, summary in cards[:3]:
                    result['isef_papers'].append((title.strip(), summary.strip()))
        
        # arXiv 논문 추출
        if "arXiv" in content:
            arxiv_section = content[content.find("arXiv"):]
            
            # Claude가 생성한 arXiv 카드 형태
            card_pattern = r'<div[^>]*background-color[^>]*>.*?<h3[^>]*>🌐\s*([^<]+)</h3>.*?<p[^>]*>([^<]+)</p>'
            cards = re.findall(card_pattern, arxiv_section, re.DOTALL)
            
            if not cards:
                # 대안 패턴
                title_pattern = r'🌐\s*([^\n]+)'
                titles = re.findall(title_pattern, arxiv_section)
                
                for title in titles[:3]:
                    title_pos = arxiv_section.find(title)
                    next_title_pos = arxiv_section.find('🌐', title_pos + 1)
                    if next_title_pos == -1:
                        next_title_pos = len(arxiv_section)
                    
                    section_content = arxiv_section[title_pos:next_title_pos]
                    lines = section_content.split('\n')[1:4]
                    summary = ' '.join([line.strip() for line in lines if line.strip() and '출처:' not in line])
                    
                    if len(summary) > 20:
                        result['arxiv_papers'].append((title.strip(), summary))
            else:
                for title, summary in cards[:3]:
                    result['arxiv_papers'].append((title.strip(), summary.strip()))
        
        # 생성된 논문 추출
        if "생성된 연구 논문" in content:
            paper_section = content[content.find("생성된 연구 논문"):]
            
            # Claude가 생성한 각 섹션 추출
            sections = {
                '초록': r'초록[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)',
                '서론': r'서론[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)',
                '실험 방법': r'실험\s*방법[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)',
                '예상 결과': r'예상\s*결과[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)',
                '시각자료': r'시각자료[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)',
                '결론': r'결론[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)',
                '참고문헌': r'참고문헌[^<\n]*(?:\([^)]*\))?[^<\n]*\n([^#]+?)(?=###|$)'
            }
            
            for section_name, pattern in sections.items():
                match = re.search(pattern, paper_section, re.DOTALL | re.IGNORECASE)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 20:
                        result['generated_paper'][section_name] = content_text
        
        return result
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return result

def create_html_content(topic, data):
    """HTML 콘텐츠 생성"""
    content_parts = []
    
    # 표지
    content_parts.append(f"""
    <div class="cover">
        <h1>{topic}</h1>
        <div class="divider"></div>
        <div class="subtitle">과학 연구 탐색 보고서</div>
        <div class="meta">
            생성일: {datetime.now().strftime("%Y년 %m월 %d일")}<br>
            LittleScienceAI
        </div>
    </div>
    """)
    
    # 주제 탐색
    if data['topic_explanation']:
        content_parts.append(f"""
        <div class="section-header">
            <h2><span class="emoji">🔬</span>주제 탐색 및 분석</h2>
        </div>
        <div class="content-block">
            <p>{clean_text_minimal(data['topic_explanation'][:1500])}</p>
        </div>
        """)
    
    # ISEF 연구
    if data['isef_papers']:
        content_parts.append(f"""
        <div class="section-header">
            <h2><span class="emoji">📄</span>ISEF 관련 연구 분석</h2>
        </div>
        """)
        
        for title, summary in data['isef_papers']:
            content_parts.append(f"""
            <div class="paper-card isef">
                <div class="title">{clean_text_minimal(title)}</div>
                <div class="source">출처: ISEF (International Science and Engineering Fair)</div>
                <div class="summary">{clean_text_minimal(summary)}</div>
            </div>
            """)
    
    # arXiv 연구
    if data['arxiv_papers']:
        content_parts.append(f"""
        <div class="section-header">
            <h2><span class="emoji">🌐</span>최신 연구논문 분석</h2>
        </div>
        """)
        
        for title, summary in data['arxiv_papers']:
            content_parts.append(f"""
            <div class="paper-card arxiv">
                <div class="title">{clean_text_minimal(title)}</div>
                <div class="source">출처: arXiv (프리프린트 논문저장소)</div>
                <div class="summary">{clean_text_minimal(summary)}</div>
            </div>
            """)
    
    # 생성된 연구 계획
    if data['generated_paper']:
        content_parts.append(f"""
        <div class="page-break"></div>
        <div class="section-header">
            <h2><span class="emoji">📝</span>연구 계획서</h2>
        </div>
        """)
        
        section_order = ['초록', '서론', '실험 방법', '예상 결과', '시각자료', '결론', '참고문헌']
        section_english = {
            '초록': 'Abstract',
            '서론': 'Introduction',
            '실험 방법': 'Methods',
            '예상 결과': 'Expected Results',
            '시각자료': 'Visualizations',
            '결론': 'Conclusion',
            '참고문헌': 'References'
        }
        
        for section_name in section_order:
            if section_name in data['generated_paper']:
                english_name = section_english.get(section_name, section_name)
                content_text = data['generated_paper'][section_name]
                
                content_parts.append(f"""
                <div class="research-section">
                    <h4>{section_name} ({english_name})</h4>
                    <div class="content">{clean_text_minimal(content_text)}</div>
                </div>
                """)
    
    return ''.join(content_parts)

def generate_pdf(content, filename="research_report.pdf"):
    """Claude급 퀄리티 PDF 생성 (Playwright)"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 데이터 추출
        topic = extract_topic_from_content(content)
        data = parse_content_smart(content)
        
        print(f"🎨 Claude급 PDF 생성 시작: {topic}")
        
        # HTML 콘텐츠 생성
        html_content = create_html_content(topic, data)
        template = get_claude_style_template()
        full_html = template.format(topic=topic, content=html_content)
        
        # PDF 생성
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # HTML 설정
            page.set_content(full_html)
            
            # 폰트 로딩 대기
            page.wait_for_timeout(1000)
            
            # PDF 생성
            page.pdf(
                path=output_path,
                format='A4',
                margin={
                    'top': '20mm',
                    'bottom': '20mm', 
                    'left': '15mm',
                    'right': '15mm'
                },
                print_background=True,
                prefer_css_page_size=True
            )
            
            browser.close()
        
        # 검증
        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"✅ Claude급 PDF 생성 완료: {output_path}")
            return output_path
        else:
            raise Exception("PDF 생성 실패")
            
    except Exception as e:
        print(f"❌ Playwright PDF 생성 실패: {e}")
        print("🔄 기존 방식으로 대체...")
        
        # 실패시 기존 FPDF로 대체
        try:
            from .pdf_generator import generate_pdf as fallback_generate_pdf
            return fallback_generate_pdf(content, filename)
        except:
            # 최종 백업: 텍스트 파일
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {topic} 연구탐색보고서 ===\n")
                f.write(f"생성일: {datetime.now()}\n\n")
                f.write("PDF 생성 실패로 텍스트로 저장합니다.\n\n")
                f.write(content)
            return txt_path

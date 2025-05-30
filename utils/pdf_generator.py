from fpdf import FPDF
import os
import re
import warnings
from datetime import datetime
import logging

# 로깅 레벨 조정
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

# 폰트 관련 경고 억제
warnings.filterwarnings("ignore", message="cmap value too big/small")
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")

# 폰트 경로
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
FONT_EXTRABOLD = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")
OUTPUT_DIR = "outputs"

class ProfessionalKoreanPDF(FPDF):
    def __init__(self, topic=""):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.topic = self.clean_text(topic)
        self.font_status = self.setup_fonts_robustly()
        self.section_number = 0
        self.subsection_number = 0
        
    def setup_fonts_robustly(self):
        font_status = {'korean_available': False, 'fallback_only': False}
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                if os.path.exists(FONT_REGULAR):
                    try:
                        self.add_font('Korean', '', FONT_REGULAR, uni=True)
                        font_status['korean_available'] = True
                        print("✅ 한글 폰트 로드 성공")
                    except Exception as e:
                        print(f"한글 폰트 실패: {e}")
                
                if font_status['korean_available'] and os.path.exists(FONT_BOLD):
                    try:
                        self.add_font('KoreanBold', '', FONT_BOLD, uni=True)
                        print("✅ 한글 Bold 폰트 추가 성공")
                    except:
                        pass
                        
            if not font_status['korean_available']:
                font_status['fallback_only'] = True
                print("⚠️ 한글 폰트 사용 불가 - Arial 사용")
            
            return font_status
                
        except Exception as e:
            print(f"폰트 설정 전체 실패: {e}")
            return {'korean_available': False, 'fallback_only': True}
    
    def set_safe_font(self, weight='normal', size=10):
        try:
            if self.font_status['korean_available']:
                if weight == 'bold':
                    try:
                        self.set_font('KoreanBold', size=size)
                    except:
                        self.set_font('Korean', size=size)
                else:
                    self.set_font('Korean', size=size)
            else:
                style = 'B' if weight == 'bold' else ''
                self.set_font('Arial', style, size)
        except Exception as e:
            print(f"폰트 설정 오류, Arial 사용: {e}")
            self.set_font('Arial', '', size)
    
    def header(self):
        if self.page_no() > 1:
            try:
                self.set_safe_font('normal', 9)
                self.set_text_color(120, 120, 120)
                header_text = f'{self.topic[:30]}... - 연구보고서' if len(self.topic) > 30 else f'{self.topic} - 연구보고서'
                self.cell(0, 10, header_text, align='R', ln=True)
                self.ln(3)
            except:
                pass
            
    def footer(self):
        try:
            self.set_y(-15)
            self.set_safe_font('normal', 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def add_title_page(self, topic):
        self.add_page()
        self.ln(30)
        
        try:
            self.set_safe_font('bold', 20)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 12, topic, align='C')
            self.ln(8)
            
            self.set_safe_font('normal', 14)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 10, '연구 탐색 보고서', align='C')
            self.ln(30)
            
            self.set_safe_font('normal', 10)
            self.set_text_color(120, 120, 120)
            today = datetime.now().strftime("%Y년 %m월 %d일")
            self.multi_cell(0, 8, f'생성일: {today}', align='C')
            self.ln(3)
            self.multi_cell(0, 8, 'LittleScienceAI', align='C')
            
        except Exception as e:
            print(f"표지 페이지 오류: {e}")
    
    def add_section_title(self, title, level=1):
        try:
            clean_title = self.clean_text(title)
            
            if level == 1:
                self.section_number += 1
                self.subsection_number = 0
                title_text = f"{self.section_number}. {clean_title}"
                
                self.ln(10)
                self.set_safe_font('bold', 14)
                self.set_text_color(30, 30, 30)
                
            elif level == 2:
                self.subsection_number += 1
                title_text = f"{self.section_number}.{self.subsection_number} {clean_title}"
                
                self.ln(6)
                self.set_safe_font('bold', 12)
                self.set_text_color(50, 50, 50)
            
            self.multi_cell(0, 8, title_text, align='L')
            self.ln(4)
            
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
    
    def add_elegant_subsection(self, title):
        try:
            self.ln(6)
            self.set_safe_font('bold', 11)
            self.set_text_color(60, 60, 60)
            clean_title = self.clean_text(title)
            self.multi_cell(0, 7, clean_title, align='L')
            self.ln(3)
        except Exception as e:
            print(f"소제목 오류: {e}")
    
    def add_paragraph(self, text):
        try:
            self.set_safe_font('normal', 10)
            self.set_text_color(70, 70, 70)
            
            clean_text = self.clean_text(text)
            if clean_text and len(clean_text.strip()) > 5:
                if len(clean_text) > 500:
                    parts = [clean_text[i:i+500] for i in range(0, len(clean_text), 500)]
                    for part in parts:
                        self.multi_cell(0, 6, part, align='L')
                        self.ln(2)
                else:
                    self.multi_cell(0, 6, clean_text, align='L')
                    self.ln(3)
                
        except Exception as e:
            print(f"문단 추가 오류: {e}")
    
    def add_paper_item(self, title, summary, source=""):
        try:
            self.set_safe_font('bold', 10)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            if len(clean_title) > 80:
                clean_title = clean_title[:77] + "..."
            
            self.multi_cell(0, 7, f"▪ {clean_title}", align='L')
            
            if source:
                self.set_safe_font('normal', 8)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 5, f"   {source}", align='L')
            
            self.set_safe_font('normal', 9)
            self.set_text_color(80, 80, 80)
            clean_summary = self.clean_text(summary)
            
            if len(clean_summary) > 200:
                clean_summary = clean_summary[:197] + "..."
            
            if clean_summary:
                self.multi_cell(0, 6, f"   {clean_summary}", align='L')
            
            self.ln(4)
            
        except Exception as e:
            print(f"논문 항목 오류: {e}")
    
    def add_paper_title_page(self, topic, selected_idea):
        self.add_page()
        self.ln(20)
        
        try:
            self.set_safe_font('bold', 18)
            self.set_text_color(30, 30, 30)
            paper_title = f"{topic}: {selected_idea.split(' - ')[0]}"
            self.multi_cell(0, 12, paper_title, align='C')
            self.ln(15)
            
            self.set_draw_color(150, 150, 150)
            self.line(30, self.get_y(), 180, self.get_y())
            self.ln(8)
            
        except Exception as e:
            print(f"논문 제목 페이지 오류: {e}")
    
    def add_paper_section(self, title, content, section_number):
        try:
            self.ln(8)
            self.set_safe_font('bold', 12)
            self.set_text_color(40, 40, 40)
            section_title = f"{section_number}. {title}"
            self.multi_cell(0, 8, section_title, align='L')
            self.ln(4)
            
            if "참고문헌" in title or "References" in title:
                self.add_professional_references()
            else:
                self.set_safe_font('normal', 10)
                self.set_text_color(70, 70, 70)
                clean_content = self.clean_text(content)
                
                if clean_content:
                    paragraphs = clean_content.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            self.multi_cell(0, 6, para.strip(), align='L')
                            self.ln(3)
            
        except Exception as e:
            print(f"논문 섹션 오류: {e}")
    
    def add_professional_references(self):
        try:
            self.set_safe_font('normal', 10)
            self.set_text_color(70, 70, 70)
            guide_text = "실제 연구 수행 시, 주요 학술검색 사이트를 활용하여 관련 논문들을 찾아 참고문헌에 추가하시기 바랍니다. 검색된 논문들은 다음과 같은 표준 양식으로 작성하세요."
            self.multi_cell(0, 6, guide_text, align='L')
            self.ln(6)
            
            self.set_safe_font('bold', 10)
            self.set_text_color(60, 60, 60)
            self.multi_cell(0, 7, "참고문헌 작성 양식 (APA Style):", align='L')
            self.ln(3)
            
            self.set_safe_font('normal', 9)
            self.set_text_color(80, 80, 80)
            
            examples = [
                "【학술지 논문】",
                "김철수, 이영희. (2024). 플라즈마 기술을 이용한 공기정화 시스템 개발. 한국과학기술학회지, 45(3), 123-135.",
                "",
                "Smith, J. A., & Johnson, M. B. (2023). Plasma-based air purification: Recent advances and applications. Journal of Applied Physics, 128(12), 245-258.",
                "",
                "【학회 발표논문】", 
                "박민수, 정다솜. (2024). 저온 플라즈마의 살균 효과에 관한 실험적 연구. 한국물리학회 춘계학술대회 발표논문집, 54, 89-92.",
                "",
                "【온라인 자료】",
                "국가과학기술정보센터. (2024). 플라즈마 기술 동향 보고서. https://www.kisti.re.kr/plasma-report-2024",
                "",
                "【서적】",
                "홍길동. (2023). 현대 플라즈마 물리학. 서울: 과학기술출판사."
            ]
            
            for example in examples:
                if example.startswith('【') and example.endswith('】'):
                    self.set_safe_font('bold', 9)
                    self.set_text_color(50, 50, 50)
                    self.multi_cell(0, 6, example, align='L')
                    self.ln(2)
                elif example == "":
                    self.ln(2)
                else:
                    self.set_safe_font('normal', 9)
                    self.set_text_color(80, 80, 80)
                    self.multi_cell(0, 5, example, align='L')
                    self.ln(1)
            
            self.ln(4)
            
            self.set_safe_font('normal', 9)
            self.set_text_color(100, 100, 100)
            final_note = "※ 실제 연구 시에는 최소 10-15개 이상의 관련 논문을 참고하여 보다 체계적인 연구를 수행하시기 바랍니다."
            self.multi_cell(0, 5, final_note, align='L')
            
        except Exception as e:
            print(f"참고문헌 가이드 오류: {e}")
    
    def clean_text(self, text):
        try:
            if not text:
                return ""
            
            text = str(text)
            
            text = re.sub(r'^---\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*---\s*', ' ', text)
            
            text = re.sub(r'https?://[^\s\]\)\n]+', '', text)
            text = re.sub(r'www\.[^\s\]\)\n]+', '', text)
            
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'[*_`#\[\]<>]', '', text)
            
            emoji_pattern = r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅🔍❗🚀✅📌🎉🔧🛠️🧬]'
            text = re.sub(emoji_pattern, '', text)
            
            text = re.sub(r'\(\s*\)', '', text)
            
            text = re.sub(r'DOI\s*:\s*', '', text)
            text = re.sub(r'&[a-zA-Z]+;', '', text)
            
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            return text.strip()
            
        except Exception as e:
            print(f"텍스트 정리 오류: {e}")
            return str(text)[:50] if text else ""

def extract_topic_from_content(content):
    try:
        title_match = re.search(r'# 📘\s*([^\n-]+)', content)
        if title_match:
            topic = title_match.group(1).strip()
            return topic[:50] if len(topic) > 50 else topic
        return "과학 연구 탐색"
    except:
        return "과학 연구 탐색"

def debug_content_structure(content):
    """Content 구조 디버깅"""
    print("=" * 60)
    print("📋 CONTENT 구조 분석 시작")
    print("=" * 60)
    print(f"📏 총 길이: {len(content):,} 문자")
    print(f"🔍 처음 1000자:")
    print("-" * 40)
    print(content[:1000])
    print("-" * 40)
    
    print(f"\n🧬 이모지 존재 여부:")
    emojis = ['🧬', '⚙️', '🌍', '💡']
    for emoji in emojis:
        exists = emoji in content
        print(f"  {emoji}: {'✅' if exists else '❌'}")
    
    print(f"\n📝 핵심 키워드 존재 여부:")
    keywords = ['응용 사례', '확장 가능한 탐구', '최신논문검색', '개념 정의', '작동 원리']
    for keyword in keywords:
        exists = keyword in content
        print(f"  '{keyword}': {'✅' if exists else '❌'}")
    
    print("=" * 60)
    return content

def parse_content_simple(content):
    """단순하고 확실한 파싱"""
    result = {
        'topic_explanation': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        # 1. 전체 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            result['topic_explanation'] = full_explanation
            
            # 2. 응용 사례 추출 (최신논문검색 이전까지)
            if '응용 사례' in full_explanation:
                # 응용 사례 시작점 찾기
                app_start = full_explanation.find('응용 사례')
                if app_start != -1:
                    app_section = full_explanation[app_start:]
                    
                    # 최신논문검색이나 확장 가능한 탐구까지만
                    end_markers = ['최신논문검색', '확장 가능한 탐구', '키워드 조합']
                    app_end = len(app_section)
                    
                    for marker in end_markers:
                        marker_pos = app_section.find(marker)
                        if marker_pos != -1 and marker_pos < app_end:
                            app_end = marker_pos
                    
                    app_content = app_section[:app_end].strip()
                    # 제목 라인 제거
                    app_lines = app_content.split('\n')[1:]  # 첫 번째 라인 제거
                    result['applications'] = '\n'.join(app_lines).strip()
            
            # 3. 확장 가능한 탐구 아이디어 추출 (각 아이디어 개별 분리)
            if '확장 가능한 탐구' in full_explanation:
                ideas_start = full_explanation.find('확장 가능한 탐구')
                if ideas_start != -1:
                    ideas_section = full_explanation[ideas_start:]
                    # 제목 라인 제거
                    ideas_lines = ideas_section.split('\n')[1:]  # 첫 번째 라인 제거
                    clean_ideas = []
                    
                    for line in ideas_lines:
                        line = line.strip()
                        # 검색 관련 내용 제외
                        if line and not any(skip in line for skip in ['키워드', 'Google Scholar', 'RISS', 'DBpia']):
                            # • 기호로 시작하는 각 아이디어를 개별적으로 분리
                            if line.startswith('•'):
                                # • 기호가 여러 개 연결된 경우 분리
                                ideas_in_line = line.split('•')
                                for idea in ideas_in_line:
                                    idea = idea.strip()
                                    if len(idea) > 10:  # 의미 있는 내용만
                                        clean_ideas.append(f"• {idea}")
                            elif line.startswith('-'):
                                clean_ideas.append(line.replace('-', '•', 1))
                            elif len(line) > 10:  # 의미 있는 내용이면 • 추가
                                clean_ideas.append(f"• {line}")
                    
                    result['research_ideas'] = '\n'.join(clean_ideas).strip()
        
        # 4. ISEF/arXiv 파싱 (기존 로직 유지)
        if "ISEF" in content or "내부 DB" in content:
            isef_match = re.search(r'## 📄[^\n]*\n(.*?)(?=## 🌐|## 📄 생성|$)', content, re.DOTALL)
            if isef_match:
                isef_section = isef_match.group(1)
                papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^_\n]*)', isef_section)
                result['isef_papers'] = [(title, summary) for title, summary in papers if len(title) > 5][:3]
        
        if "arXiv" in content:
            arxiv_match = re.search(r'## 🌐[^\n]*\n(.*?)(?=## 📄 생성|$)', content, re.DOTALL)
            if arxiv_match:
                arxiv_section = arxiv_match.group(1)
                papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^[\n]*)', arxiv_section)
                result['arxiv_papers'] = [(title, summary) for title, summary in papers if len(title) > 5][:3]
        
        # 5. 생성된 논문
        if "생성된 연구 논문" in content:
            paper_section = content[content.find("생성된 연구 논문"):]
            
            sections = ['초록', '서론', '실험 방법', '예상 결과', '결론', '참고문헌']
            for section in sections:
                pattern = f"### {section}[^\n]*\n(.*?)(?=###|$)"
                match = re.search(pattern, paper_section, re.DOTALL)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 10:
                        result['generated_paper'][section] = content_text
        
        print(f"파싱 결과 - 응용사례: {len(result.get('applications', ''))}, 탐구아이디어: {len(result.get('research_ideas', ''))}")
        
        # 디버깅: 탐구 아이디어 내용 확인
        if result.get('research_ideas'):
            print("=== 탐구 아이디어 파싱 결과 ===")
            print(repr(result['research_ideas']))
            print("=== 라인별 분리 ===")
            lines = result['research_ideas'].split('\n')
            for i, line in enumerate(lines):
                print(f"라인 {i}: {repr(line)}")
            print("=======================")
        
        return result
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """Import 오류 없는 안전한 PDF 생성"""
    try:
        # 디버깅
        content = debug_content_structure(content)
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        print(f"추출된 주제: {topic}")
        
        # 내용 파싱
        sections = parse_content_simple(content)
        
        # PDF 생성
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            pdf = ProfessionalKoreanPDF(topic)
            
            # 1. 표지 페이지
            pdf.add_title_page(topic)
            
            # 2. 내용 페이지
            pdf.add_page()
            
            # 3. 주제 개요
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                # 전체 설명에서 각 부분 추출하여 소제목으로 구분
                explanation = sections['topic_explanation']
                
                # 개념 정의 부분
                if '개념' in explanation or '정의' in explanation:
                    concept_part = explanation.split('작동')[0] if '작동' in explanation else explanation[:500]
                    if len(concept_part) > 50:
                        pdf.add_elegant_subsection("개념 정의")
                        pdf.add_paragraph(concept_part)
                
                # 응용 사례
                if sections.get('applications'):
                    pdf.add_elegant_subsection("응용 사례 및 활용 분야")
                    pdf.add_paragraph(sections['applications'])
                
                # 확장 가능한 탐구 아이디어 (별도 소제목, 각 아이디어 개별 처리)
                if sections.get('research_ideas'):
                    pdf.add_elegant_subsection("확장 가능한 탐구 아이디어")
                    
                    # 각 아이디어를 개별 라인으로 처리
                    ideas_text = sections['research_ideas']
                    if ideas_text:
                        # 줄바꿈으로 분리하여 각각 개별 처리
                        idea_lines = ideas_text.split('\n')
                        for line in idea_lines:
                            line = line.strip()
                            if line and len(line) > 5:
                                # 각 아이디어를 개별 문단으로 추가
                                pdf.add_paragraph(line)
            
            # 4. 문헌 조사
            pdf.add_section_title("문헌 조사")
            
            # ISEF 연구
            pdf.add_section_title("ISEF 관련 연구", level=2)
            if sections['isef_papers']:
                for title, summary in sections['isef_papers']:
                    pdf.add_paper_item(title, summary, "출처: ISEF 프로젝트")
            else:
                pdf.add_paragraph("관련 ISEF 프로젝트를 찾지 못했습니다.")
            
            # arXiv 연구
            pdf.add_section_title("arXiv 최신 연구", level=2)
            if sections['arxiv_papers']:
                for title, summary in sections['arxiv_papers']:
                    pdf.add_paper_item(title, summary, "출처: arXiv (프리프린트)")
            else:
                pdf.add_paragraph("관련 arXiv 논문을 찾지 못했습니다.")
            
            # 5. 생성된 논문
            if sections['generated_paper']:
                selected_idea = "선택된 연구 주제"
                if "가정용 플라즈마" in content:
                    selected_idea = "가정용 플라즈마 공기청정 장치 개발"
                
                pdf.add_paper_title_page(topic, selected_idea)
                
                section_map = {
                    '초록': ('Abstract', 1),
                    '서론': ('Introduction', 2), 
                    '실험 방법': ('Methods', 3),
                    '예상 결과': ('Expected Results', 4),
                    '결론': ('Conclusion', 5),
                    '참고문헌': ('References', 6)
                }
                
                for section_key, (english_name, num) in section_map.items():
                    if section_key in sections['generated_paper']:
                        title = f"{section_key} ({english_name})"
                        content_text = sections['generated_paper'][section_key]
                        pdf.add_paper_section(title, content_text, num)
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ PDF 생성 성공: {output_path} ({file_size:,} bytes)")
                
                try:
                    with open(output_path, 'rb') as f:
                        header = f.read(10)
                        if header.startswith(b'%PDF'):
                            print("✅ PDF 형식 검증 통과")
                            return output_path
                except:
                    pass
        
        # 실패시 텍스트 파일
        txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {topic} 연구보고서 ===\n\n")
            f.write(f"생성 시간: {datetime.now()}\n\n")
            f.write(content)
        
        print(f"✅ 백업 파일 생성: {txt_path}")
        return txt_path
            
    except Exception as e:
        print(f"❌ PDF 생성 오류: {e}")
        return None

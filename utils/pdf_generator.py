from fpdf import FPDF
import os
import re
import warnings
from datetime import datetime

# 폰트 관련 경고 억제
warnings.filterwarnings("ignore", message="cmap value too big/small")
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")

# 폰트 경로
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
FONT_EXTRABOLD = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")
OUTPUT_DIR = "outputs"

class SafeKoreanPDF(FPDF):
    def __init__(self, topic=""):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.topic = topic
        self.fonts_loaded = self.setup_fonts_safely()
        self.section_number = 0
        self.subsection_number = 0
        
    def setup_fonts_safely(self):
        """안전한 폰트 설정 (경고 최소화)"""
        try:
            print("폰트 설정 시작...")
            fonts_loaded = {}
            
            # 경고 임시 억제
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Regular 폰트 (필수)
                if os.path.exists(FONT_REGULAR):
                    try:
                        self.add_font('NanumRegular', '', FONT_REGULAR, uni=True)
                        fonts_loaded['regular'] = True
                        print("✅ Regular 폰트 로드 성공")
                    except Exception as e:
                        print(f"Regular 폰트 실패: {e}")
                        fonts_loaded['regular'] = False
                
                # Bold 폰트 (중요)
                if os.path.exists(FONT_BOLD):
                    try:
                        self.add_font('NanumBold', '', FONT_BOLD, uni=True)
                        fonts_loaded['bold'] = True
                        print("✅ Bold 폰트 로드 성공")
                    except Exception as e:
                        print(f"Bold 폰트 실패: {e}")
                        fonts_loaded['bold'] = False
                
                # ExtraBold는 선택사항 (실패해도 괜찮음)
                if os.path.exists(FONT_EXTRABOLD):
                    try:
                        self.add_font('NanumExtraBold', '', FONT_EXTRABOLD, uni=True)
                        fonts_loaded['extrabold'] = True
                        print("✅ ExtraBold 폰트 로드 성공")
                    except Exception as e:
                        print(f"ExtraBold 폰트 실패 (무시): {e}")
                        fonts_loaded['extrabold'] = False
            
            # 최소 Regular 폰트만 로드되면 성공
            success = fonts_loaded.get('regular', False)
            print(f"폰트 로딩 결과: {sum(fonts_loaded.values())}/3개, 사용 가능: {success}")
            
            return {
                'available': success,
                'regular': fonts_loaded.get('regular', False),
                'bold': fonts_loaded.get('bold', False),
                'extrabold': fonts_loaded.get('extrabold', False)
            }
                
        except Exception as e:
            print(f"폰트 설정 전체 실패: {e}")
            return {'available': False, 'regular': False, 'bold': False, 'extrabold': False}
    
    def set_safe_font(self, weight='regular', size=10):
        """안전한 폰트 설정"""
        try:
            if self.fonts_loaded['available']:
                if weight == 'extrabold' and self.fonts_loaded['extrabold']:
                    self.set_font('NanumExtraBold', size=size)
                elif weight == 'bold' and self.fonts_loaded['bold']:
                    self.set_font('NanumBold', size=size)
                elif self.fonts_loaded['regular']:
                    self.set_font('NanumRegular', size=size)
                else:
                    # 대체 폰트
                    self.set_font('Arial', 'B' if weight in ['bold', 'extrabold'] else '', size)
            else:
                # Arial 대체
                style = 'B' if weight in ['bold', 'extrabold'] else ''
                self.set_font('Arial', style, size)
        except Exception as e:
            print(f"폰트 설정 오류: {e}")
            # 최종 대체
            self.set_font('Arial', '', size)
    
    def header(self):
        """페이지 헤더"""
        if self.page_no() > 1:  # 첫 페이지 제외
            try:
                self.set_safe_font('regular', 9)
                self.set_text_color(120, 120, 120)
                self.cell(0, 10, f'{self.topic} - 연구보고서', align='R', ln=True)
                self.ln(3)
            except:
                pass
            
    def footer(self):
        """페이지 푸터"""
        try:
            self.set_y(-15)
            self.set_safe_font('regular', 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def add_title_page(self, topic):
        """표지 페이지 생성"""
        self.add_page()
        
        # 상단 여백
        self.ln(40)
        
        try:
            # 메인 제목
            self.set_safe_font('extrabold', 24)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 15, f'{topic}', align='C')
            self.ln(10)
            
            # 부제목
            self.set_safe_font('bold', 16)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 12, '연구 탐색 보고서', align='C')
            self.ln(40)
            
            # 생성 정보
            self.set_safe_font('regular', 12)
            self.set_text_color(100, 100, 100)
            today = datetime.now().strftime("%Y년 %m월 %d일")
            self.multi_cell(0, 10, f'생성일: {today}', align='C')
            self.ln(5)
            self.multi_cell(0, 10, 'LittleScienceAI', align='C')
            
        except Exception as e:
            print(f"표지 페이지 오류: {e}")
    
    def add_section_title(self, title, level=1):
        """섹션 제목 추가 (번호 포함)"""
        try:
            if level == 1:
                self.section_number += 1
                self.subsection_number = 0
                title_text = f"{self.section_number}. {title}"
                
                self.ln(12)
                self.set_safe_font('extrabold', 16)
                self.set_text_color(30, 30, 30)
                
            elif level == 2:
                self.subsection_number += 1
                title_text = f"{self.section_number}.{self.subsection_number} {title}"
                
                self.ln(8)
                self.set_safe_font('bold', 13)
                self.set_text_color(50, 50, 50)
            
            self.multi_cell(0, 10, title_text, align='L')
            self.ln(6)
            
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
    
    def add_paragraph(self, text, style='normal'):
        """문단 추가"""
        try:
            if style == 'normal':
                self.set_safe_font('regular', 10)
                self.set_text_color(70, 70, 70)
            elif style == 'emphasis':
                self.set_safe_font('bold', 10)
                self.set_text_color(60, 60, 60)
            
            # 텍스트 정리
            clean_text = self.clean_text(text)
            if clean_text.strip():
                self.multi_cell(0, 7, clean_text, align='L')
                self.ln(4)
                
        except Exception as e:
            print(f"문단 추가 오류: {e}")
    
    def add_paper_card(self, title, summary, meta_info=""):
        """논문 카드 형태로 추가"""
        try:
            # 제목
            self.set_safe_font('bold', 11)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            if len(clean_title) > 100:  # 제목 길이 제한
                clean_title = clean_title[:97] + "..."
            self.multi_cell(0, 8, f"📌 {clean_title}", align='L')
            
            # 메타 정보
            if meta_info:
                self.set_safe_font('regular', 9)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 6, self.clean_text(meta_info), align='L')
            
            # 요약
            self.set_safe_font('regular', 10)
            self.set_text_color(80, 80, 80)
            clean_summary = self.clean_text(summary)
            
            # 요약 길이 제한 (250자로 단축)
            if len(clean_summary) > 250:
                clean_summary = clean_summary[:247] + "..."
            
            self.multi_cell(0, 7, clean_summary, align='L')
            self.ln(8)
            
        except Exception as e:
            print(f"논문 카드 오류: {e}")
    
    def clean_text(self, text):
        """텍스트 정리 (더 강력한 정리)"""
        try:
            if not text:
                return ""
            
            # URL 완전 제거 (더 포괄적)
            text = re.sub(r'https?://[^\s\]\)]+', '', text)
            text = re.sub(r'www\.[^\s\]\)]+', '', text)
            
            # 마크다운 제거
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'[*_`#\[\]]', '', text)
            
            # 이모지와 특수문자 제거
            text = re.sub(r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅🔍❗🚀✅📌]', '', text)
            
            # 괄호 안의 내용 중 링크 관련 제거
            text = re.sub(r'\([^)]*http[^)]*\)', '', text)
            
            # 여러 공백을 하나로
            text = re.sub(r'\s+', ' ', text)
            
            # 특수 구문 제거
            text = re.sub(r'DOI\s*:\s*', '', text)
            
            return text.strip()
            
        except Exception as e:
            print(f"텍스트 정리 오류: {e}")
            return text[:100] if text else "[텍스트 처리 오류]"

def parse_content_sections(content):
    """내용을 섹션별로 파싱 (더 안전하게)"""
    sections = {
        'topic_explanation': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        # 주제 해설 추출
        if "# 📘" in content:
            start = content.find("# 📘")
            end = content.find("## 📄 내부 DB")
            if end == -1:
                end = content.find("## 🌐 arXiv")
            if end == -1:
                end = len(content)
            
            explanation = content[start:end].strip()
            # 제목 부분 제거
            explanation = re.sub(r'^# 📘[^\n]*\n*', '', explanation)
            sections['topic_explanation'] = explanation
        
        # 생성된 논문 추출 (더 안전하게)
        if "## 📄 생성된 연구 논문" in content:
            paper_start = content.find("## 📄 생성된 연구 논문")
            paper_content = content[paper_start:]
            
            # 각 섹션 추출
            paper_sections = ['초록', '서론', '실험 방법', '예상 결과', '시각자료 제안', '결론', '참고문헌']
            for section in paper_sections:
                pattern = f"### {section}"
                if pattern in paper_content:
                    start_idx = paper_content.find(pattern)
                    
                    # 다음 섹션 찾기
                    next_start = len(paper_content)
                    for next_sec in paper_sections:
                        next_pattern = f"### {next_sec}"
                        next_idx = paper_content.find(next_pattern, start_idx + len(pattern))
                        if next_idx != -1 and next_idx < next_start:
                            next_start = next_idx
                    
                    section_content = paper_content[start_idx + len(pattern):next_start]
                    section_content = section_content.strip()
                    
                    if section_content:  # 빈 섹션 제외
                        sections['generated_paper'][section] = section_content
        
        return sections
        
    except Exception as e:
        print(f"내용 파싱 오류: {e}")
        return sections

def generate_pdf(content, filename="research_report.pdf"):
    """안전한 PDF 생성 (경고 최소화)"""
    try:
        print("=== 안전한 PDF 생성 시작 ===")
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출 (더 안전하게)
        topic = "과학 연구 탐색"
        try:
            if "# 📘" in content:
                topic_match = re.search(r'# 📘\s*([^\n-]+)', content)
                if topic_match:
                    topic = topic_match.group(1).strip()
                    # 너무 긴 제목 제한
                    if len(topic) > 50:
                        topic = topic[:47] + "..."
        except:
            pass
        
        # 경고 억제하며 PDF 생성
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            pdf = SafeKoreanPDF(topic)
            
            # 1. 표지 페이지
            pdf.add_title_page(topic)
            
            # 2. 새 페이지에서 내용 시작
            pdf.add_page()
            
            # 내용 파싱
            sections = parse_content_sections(content)
            
            # 3. 주제 개요
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                # 문단별로 분리
                paragraphs = sections['topic_explanation'].split('\n\n')
                for para in paragraphs:
                    if para.strip() and len(para.strip()) > 10:  # 너무 짧은 문단 제외
                        pdf.add_paragraph(para.strip())
            
            # 4. 문헌 조사
            pdf.add_section_title("문헌 조사")
            
            # 4.1 ISEF 연구
            pdf.add_section_title("ISEF 관련 연구", level=2)
            
            # ISEF 논문 파싱 (더 안전하게)
            isef_found = False
            if "## 📄 내부 DB" in content or "ISEF" in content:
                # 간단한 패턴으로 논문 찾기
                papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^_\n]+)', content)
                
                if papers:
                    for title, summary in papers[:5]:  # 최대 5개만
                        if len(title.strip()) > 5 and len(summary.strip()) > 10:
                            pdf.add_paper_card(title.strip(), summary.strip(), "출처: ISEF 프로젝트")
                            isef_found = True
            
            if not isef_found:
                pdf.add_paragraph("관련 ISEF 프로젝트를 찾지 못했습니다.")
            
            # 4.2 arXiv 연구  
            pdf.add_section_title("arXiv 최신 연구", level=2)
            
            arxiv_found = False
            if "## 🌐 arXiv" in content or "arxiv" in content.lower():
                # arXiv 섹션 찾기
                arxiv_start = content.find("## 🌐 arXiv")
                if arxiv_start != -1:
                    arxiv_section = content[arxiv_start:]
                    # 다음 큰 섹션까지만
                    next_section = arxiv_section.find("## 📄")
                    if next_section != -1:
                        arxiv_section = arxiv_section[:next_section]
                    
                    # 논문 추출
                    arxiv_papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^[\n]+)', arxiv_section)
                    
                    if arxiv_papers:
                        for title, summary in arxiv_papers[:5]:  # 최대 5개만
                            if len(title.strip()) > 5 and len(summary.strip()) > 10:
                                pdf.add_paper_card(title.strip(), summary.strip(), "출처: arXiv (프리프린트)")
                                arxiv_found = True
            
            if not arxiv_found:
                pdf.add_paragraph("관련 arXiv 논문을 찾지 못했습니다.")
            
            # 5. 연구 논문 (생성된 경우에만)
            if sections['generated_paper']:
                pdf.add_section_title("연구 논문")
                
                # 논문 섹션들을 순서대로 추가
                paper_order = ['초록', '서론', '실험 방법', '예상 결과', '시각자료 제안', '결론', '참고문헌']
                section_names = {
                    '초록': 'Abstract',
                    '서론': 'Introduction', 
                    '실험 방법': 'Methods',
                    '예상 결과': 'Expected Results',
                    '시각자료 제안': 'Suggested Visualizations',
                    '결론': 'Conclusion',
                    '참고문헌': 'References'
                }
                
                for section_key in paper_order:
                    if section_key in sections['generated_paper']:
                        content_text = sections['generated_paper'][section_key]
                        if content_text and len(content_text.strip()) > 5:
                            english_name = section_names.get(section_key, section_key)
                            pdf.add_section_title(f"{section_key} ({english_name})", level=2)
                            pdf.add_paragraph(content_text)
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            pdf.output(output_path)
        
        # 파일 확인
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 3000:  # 최소 3KB
                print(f"✅ PDF 생성 성공: {output_path} ({file_size:,} bytes)")
                return output_path
            else:
                raise Exception(f"PDF 파일이 너무 작음 ({file_size} bytes)")
        else:
            raise Exception("PDF 파일이 생성되지 않음")
            
    except Exception as e:
        print(f"❌ PDF 생성 실패: {str(e)}")
        
        # 실패시 백업 텍스트 파일
        try:
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {topic} 연구보고서 ===\n")
                f.write("(PDF 생성 실패로 텍스트 버전)\n\n")
                # 정리된 내용 저장
                clean_content = re.sub(r'https?://[^\s]+', '', content)
                f.write(clean_content)
            
            print(f"✅ 백업 텍스트 파일: {txt_path}")
            return txt_path
            
        except Exception as txt_error:
            print(f"❌ 백업 파일 저장 실패: {txt_error}")
            return None

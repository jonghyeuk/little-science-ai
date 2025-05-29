from fpdf import FPDF
import os
import re
import warnings
from datetime import datetime
import logging

# 로깅 레벨 조정 (httpx 로그 억제)
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
        print(f"PDF 초기화 완료 - 주제: {self.topic}")
        
    def setup_fonts_robustly(self):
        """견고한 폰트 설정"""
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
        """안전한 폰트 설정"""
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
        """헤더"""
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
        """푸터"""
        try:
            self.set_y(-15)
            self.set_safe_font('normal', 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def add_title_page(self, topic):
        """표지 페이지"""
        self.add_page()
        self.ln(30)
        
        try:
            # 메인 제목
            self.set_safe_font('bold', 20)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 12, topic, align='C')
            self.ln(8)
            
            # 부제목
            self.set_safe_font('normal', 14)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 10, '연구 탐색 보고서', align='C')
            self.ln(30)
            
            # 생성 정보
            self.set_safe_font('normal', 10)
            self.set_text_color(120, 120, 120)
            today = datetime.now().strftime("%Y년 %m월 %d일")
            self.multi_cell(0, 8, f'생성일: {today}', align='C')
            self.ln(3)
            self.multi_cell(0, 8, 'LittleScienceAI', align='C')
            
            print("표지 페이지 추가 완료")
            
        except Exception as e:
            print(f"표지 페이지 오류: {e}")
    
    def add_section_title(self, title, level=1):
        """섹션 제목"""
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
            print(f"섹션 제목 추가: {title_text}")
            
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
    
    def add_elegant_subsection(self, title):
        """이쁜 소제목"""
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
        """문단 추가"""
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
        """논문 항목 추가"""
        try:
            # 제목
            self.set_safe_font('bold', 10)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            if len(clean_title) > 80:
                clean_title = clean_title[:77] + "..."
            
            self.multi_cell(0, 7, f"▪ {clean_title}", align='L')
            
            # 출처
            if source:
                self.set_safe_font('normal', 8)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 5, f"   {source}", align='L')
            
            # 요약
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
        """논문용 새 페이지"""
        self.add_page()
        self.ln(20)
        
        try:
            # 논문 제목
            self.set_safe_font('bold', 18)
            self.set_text_color(30, 30, 30)
            paper_title = f"{topic}: {selected_idea.split(' - ')[0]}"
            self.multi_cell(0, 12, paper_title, align='C')
            self.ln(15)
            
            # 구분선
            self.set_draw_color(150, 150, 150)
            self.line(30, self.get_y(), 180, self.get_y())
            self.ln(8)
            
            print("논문 제목 페이지 추가 완료")
            
        except Exception as e:
            print(f"논문 제목 페이지 오류: {e}")
    
    def add_paper_section(self, title, content, section_number):
        """논문 섹션 추가"""
        try:
            # 섹션 번호와 제목
            self.ln(8)
            self.set_safe_font('bold', 12)
            self.set_text_color(40, 40, 40)
            section_title = f"{section_number}. {title}"
            self.multi_cell(0, 8, section_title, align='L')
            self.ln(4)
            
            # 참고문헌 섹션 특별 처리
            if "참고문헌" in title or "References" in title:
                self.add_professional_references()
            else:
                # 일반 내용
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
        """전문적인 참고문헌 가이드"""
        try:
            # 안내 메시지
            self.set_safe_font('normal', 10)
            self.set_text_color(70, 70, 70)
            guide_text = """실제 연구 수행 시, 주요 학술검색 사이트를 활용하여 관련 논문들을 찾아 참고문헌에 추가하시기 바랍니다. 검색된 논문들은 다음과 같은 표준 양식으로 작성하세요."""
            self.multi_cell(0, 6, guide_text, align='L')
            self.ln(6)
            
            # 참고문헌 양식 예시
            self.set_safe_font('bold', 10)
            self.set_text_color(60, 60, 60)
            self.multi_cell(0, 7, "참고문헌 작성 양식 (APA Style):", align='L')
            self.ln(3)
            
            # 양식 예시들
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
                    # 분류 제목
                    self.set_safe_font('bold', 9)
                    self.set_text_color(50, 50, 50)
                    self.multi_cell(0, 6, example, align='L')
                    self.ln(2)
                elif example == "":
                    self.ln(2)
                else:
                    # 예시 내용
                    self.set_safe_font('normal', 9)
                    self.set_text_color(80, 80, 80)
                    self.multi_cell(0, 5, example, align='L')
                    self.ln(1)
            
            self.ln(4)
            
            # 마무리 안내
            self.set_safe_font('normal', 9)
            self.set_text_color(100, 100, 100)
            final_note = "※ 실제 연구 시에는 최소 10-15개 이상의 관련 논문을 참고하여 보다 체계적인 연구를 수행하시기 바랍니다."
            self.multi_cell(0, 5, final_note, align='L')
            
        except Exception as e:
            print(f"참고문헌 가이드 오류: {e}")
    
    def clean_text(self, text):
        """텍스트 정리"""
        try:
            if not text:
                return ""
            
            text = str(text)
            
            # 하이픈 구분자 제거
            text = re.sub(r'^---\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*---\s*', ' ', text)
            
            # URL 제거
            text = re.sub(r'https?://[^\s\]\)\n]+', '', text)
            text = re.sub(r'www\.[^\s\]\)\n]+', '', text)
            
            # 마크다운 제거
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'[*_`#\[\]<>]', '', text)
            
            # 이모지 제거 (PDF 출력용)
            emoji_pattern = r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅🔍❗🚀✅📌🎉🔧🛠️🧬]'
            text = re.sub(emoji_pattern, '', text)
            
            # 빈 괄호 제거
            text = re.sub(r'\(\s*\)', '', text)
            
            # 특수 문자 정리
            text = re.sub(r'DOI\s*:\s*', '', text)
            text = re.sub(r'&[a-zA-Z]+;', '', text)
            
            # 여러 공백을 하나로
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            return text.strip()
            
        except Exception as e:
            print(f"텍스트 정리 오류: {e}")
            return str(text)[:50] if text else ""

def extract_topic_from_content(content):
    """내용에서 주제 추출"""
    try:
        title_match = re.search(r'# 📘\s*([^\n-]+)', content)
        if title_match:
            topic = title_match.group(1).strip()
            return topic[:50] if len(topic) > 50 else topic
        return "과학 연구 탐색"
    except:
        return "과학 연구 탐색"

def parse_content_elegantly(content):
    """이모지 기반 내용 파싱"""
    result = {
        'topic_explanation': '',
        'concept_definition': '',
        'working_principle': '',
        'current_background': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("내용 파싱 시작...")
        
        # 1. 주제 해설 전체 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            result['topic_explanation'] = full_explanation
            
            # 2. 이모지 기반으로 각 섹션 분리
            # 개념 정의 (🧬)
            concept_match = re.search(r'🧬[^\n]*개념[^\n]*\n(.*?)(?=⚙️|🌍|💡|$)', full_explanation, re.DOTALL)
            if concept_match:
                result['concept_definition'] = concept_match.group(1).strip()
            
            # 작동 원리 (⚙️)  
            principle_match = re.search(r'⚙️[^\n]*작동[^\n]*\n(.*?)(?=🌍|💡|$)', full_explanation, re.DOTALL)
            if principle_match:
                result['working_principle'] = principle_match.group(1).strip()
            
            # 현재 배경 (🌍)
            background_match = re.search(r'🌍[^\n]*배경[^\n]*\n(.*?)(?=💡|$)', full_explanation, re.DOTALL)
            if background_match:
                result['current_background'] = background_match.group(1).strip()
            
            # 응용 사례 (💡)
            application_match = re.search(r'💡[^\n]*응용[^\n]*\n(.*?)$', full_explanation, re.DOTALL)
            if application_match:
                result['applications'] = application_match.group(1).strip()
        
        # 3. ISEF 논문들
        if "ISEF" in content or "내부 DB" in content:
            isef_match = re.search(r'## 📄[^\n]*\n(.*?)(?=## 🌐|## 📄 생성|$)', content, re.DOTALL)
            if isef_match:
                isef_section = isef_match.group(1)
                papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^_\n]*)', isef_section)
                result['isef_papers'] = [(title, summary) for title, summary in papers if len(title) > 5][:3]
        
        # 4. arXiv 논문들
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
        
        print(f"파싱 완료 - 개념정의: {bool(result.get('concept_definition'))}, 작동원리: {bool(result.get('working_principle'))}")
        print(f"배경: {bool(result.get('current_background'))}, 응용: {bool(result.get('applications'))}")
        print(f"ISEF: {len(result['isef_papers'])}, arXiv: {len(result['arxiv_papers'])}, 논문: {len(result['generated_paper'])}")
        return result
        
    except Exception as e:
        print(f"내용 파싱 오류: {e}")
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """이쁜 PDF 생성"""
    try:
        print("=== 이쁜 PDF 생성 시작 ===")
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        print(f"추출된 주제: {topic}")
        
        # 내용 파싱
        sections = parse_content_elegantly(content)
        
        # PDF 생성 (경고 완전 억제)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            pdf = ProfessionalKoreanPDF(topic)
            
            # 1. 표지 페이지
            pdf.add_title_page(topic)
            
            # 2. 내용 페이지
            pdf.add_page()
            
            # 3. 주제 개요 (이모지 기반 정확한 섹션 분리)
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                # 개념 정의
                if sections.get('concept_definition'):
                    pdf.add_elegant_subsection("개념 정의")
                    pdf.add_paragraph(sections['concept_definition'])
                
                # 작동 원리 및 메커니즘
                if sections.get('working_principle'):
                    pdf.add_elegant_subsection("작동 원리 및 메커니즘")
                    pdf.add_paragraph(sections['working_principle'])
                
                # 현재 과학적·사회적 배경
                if sections.get('current_background'):
                    pdf.add_elegant_subsection("현재 과학적·사회적 배경")
                    pdf.add_paragraph(sections['current_background'])
                
                # 응용 사례 및 활용 분야
                if sections.get('applications'):
                    pdf.add_elegant_subsection("응용 사례 및 활용 분야")
                    pdf.add_paragraph(sections['applications'])
            
            # 4. 문헌 조사
            pdf.add_section_title("문헌 조사")
            
            # 4.1 ISEF 연구
            pdf.add_section_title("ISEF 관련 연구", level=2)
            if sections['isef_papers']:
                for title, summary in sections['isef_papers']:
                    pdf.add_paper_item(title, summary, "출처: ISEF 프로젝트")
            else:
                pdf.add_paragraph("관련 ISEF 프로젝트를 찾지 못했습니다.")
            
            # 4.2 arXiv 연구
            pdf.add_section_title("arXiv 최신 연구", level=2)
            if sections['arxiv_papers']:
                for title, summary in sections['arxiv_papers']:
                    pdf.add_paper_item(title, summary, "출처: arXiv (프리프린트)")
            else:
                pdf.add_paragraph("관련 arXiv 논문을 찾지 못했습니다.")
            
            # 5. 생성된 논문 (새 페이지에서 전문적으로)
            if sections['generated_paper']:
                # 틈새주제 추출 시도
                selected_idea = "선택된 연구 주제"
                if "가정용 플라즈마" in content:
                    selected_idea = "가정용 플라즈마 공기청정 장치 개발"
                
                pdf.add_paper_title_page(topic, selected_idea)
                
                # 논문 섹션들을 전문적으로 추가
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
                print(f"✅ 이쁜 PDF 생성 성공: {output_path} ({file_size:,} bytes)")
                
                # 내용 검증
                try:
                    with open(output_path, 'rb') as f:
                        header = f.read(10)
                        if header.startswith(b'%PDF'):
                            print("✅ PDF 형식 검증 통과")
                            return output_path
                        else:
                            print("❌ PDF 형식 오류")
                except:
                    print("❌ PDF 읽기 오류")
            else:
                print(f"❌ PDF 파일이 너무 작음: {file_size} bytes")
        
        # 실패시 텍스트 파일 생성
        print("PDF 생성 실패, 백업 텍스트 파일 생성...")
        txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_debug.txt'))
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {topic} 연구보고서 (이쁜 버전) ===\n\n")
            f.write(f"생성 시간: {datetime.now()}\n")
            f.write(f"원본 내용 길이: {len(content)} 문자\n\n")
            
            # 정리된 내용
            f.write("=== 정리된 원본 내용 ===\n")
            clean_content = re.sub(r'https?://[^\s]+', '[링크제거]', content)
            clean_content = re.sub(r'---\s*[^\n]*\n', '', clean_content)
            f.write(clean_content)
        
        print(f"✅ 백업 파일 생성: {txt_path}")
        return txt_path
            
    except Exception as e:
        print(f"❌ PDF 생성 중 치명적 오류: {e}")
        return None

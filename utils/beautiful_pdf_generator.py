# utils/beautiful_pdf_generator.py
from fpdf import FPDF
import os
import re
import warnings
import logging
from datetime import datetime
import contextlib

# 🔥 기존 코드의 강화된 경고 억제 방식 사용
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

warnings.filterwarnings("ignore", message="cmap value too big/small")
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")
warnings.filterwarnings("ignore", category=UserWarning, message=".*fpdf.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fpdf")
warnings.filterwarnings("ignore", message=".*font.*")
warnings.filterwarnings("ignore", message=".*PDF.*")
warnings.filterwarnings("ignore", message=".*unicode.*")

@contextlib.contextmanager
def suppress_fpdf_warnings():
    """PDF 생성 중 모든 경고 억제 - 기존 방식"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

# 🔥 기존 코드와 동일한 폰트 경로
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
FONT_EXTRABOLD = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")
OUTPUT_DIR = "outputs"

class BeautifulSciencePDF(FPDF):
    def __init__(self, topic=""):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.topic = self.clean_text(topic)  # 🔥 기존 함수명 사용
        self.font_status = self.setup_fonts_robustly()  # 🔥 기존 방식
        self.section_number = 0
        self.subsection_number = 0
        
        # 🎨 색상 팔레트 (현대적)
        self.colors = {
            'primary': (59, 130, 246),      # 파란색
            'secondary': (16, 185, 129),    # 초록색
            'accent': (139, 92, 246),       # 보라색
            'warning': (245, 158, 11),      # 주황색
            'text_dark': (17, 24, 39),      # 진한 텍스트
            'text_medium': (55, 65, 81),    # 중간 텍스트
            'text_light': (107, 114, 128),  # 연한 텍스트
            'bg_light': (249, 250, 251),    # 연한 배경
            'border': (229, 231, 235)       # 테두리
        }
    
    def setup_fonts_robustly(self):
        """🔥 폰트 없이도 작동하는 안전한 방식"""
        font_status = {'korean_available': False, 'fallback_only': True}
        
        try:
            # 폰트 파일이 있으면 시도, 없으면 그냥 넘어감
            if os.path.exists(FONT_REGULAR):
                try:
                    with suppress_fpdf_warnings():
                        self.add_font('Korean', '', FONT_REGULAR, uni=True)
                        font_status['korean_available'] = True
                        font_status['fallback_only'] = False
                        print("✅ 한글 폰트 로드 성공")
                except Exception as e:
                    print(f"⚠️ 한글 폰트 실패, Arial 사용: {e}")
            else:
                print("⚠️ 한글 폰트 파일 없음, Arial 사용")
            
            return font_status
                
        except Exception as e:
            print(f"⚠️ 폰트 설정 오류, Arial로 대체: {e}")
            return {'korean_available': False, 'fallback_only': True}
    
    def set_safe_font(self, weight='normal', size=10, color='text_dark'):
        """🔥 기존 코드 + 색상 추가"""
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
                
            # 🎨 색상 설정 추가
            if color in self.colors:
                r, g, b = self.colors[color]
                self.set_text_color(r, g, b)
            else:
                self.set_text_color(70, 70, 70)  # 기본색
                
        except Exception as e:
            print(f"폰트 설정 오류, Arial 사용: {e}")
            self.set_font('Arial', '', size)
            self.set_text_color(70, 70, 70)
    
    def header(self):
        """🔥 기존 코드 + 색상 개선"""
        if self.page_no() > 1:
            try:
                self.set_safe_font('normal', 9, 'text_light')
                header_text = f'{self.topic[:30]}... - 연구보고서' if len(self.topic) > 30 else f'{self.topic} - 연구보고서'
                
                # 🎨 헤더 라인 추가
                r, g, b = self.colors['border']
                self.set_draw_color(r, g, b)
                self.line(20, 25, 190, 25)
                
                self.cell(0, 10, header_text, align='R', ln=True)
                self.ln(3)
            except:
                pass
            
    def footer(self):
        """🔥 기존 코드 + 색상 개선"""
        try:
            self.set_y(-20)
            
            # 🎨 푸터 라인 추가
            r, g, b = self.colors['border']
            self.set_draw_color(r, g, b)
            self.line(20, self.get_y(), 190, self.get_y())
            
            self.ln(5)
            self.set_safe_font('normal', 9, 'text_light')
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def clean_text(self, text):
        """🔥 기존 코드의 덜 공격적인 텍스트 정리 방식 사용"""
        try:
            if not text:
                return ""
            
            text = str(text)
            
            # 기본적인 마크다운 정리
            text = re.sub(r'^---\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*---\s*', ' ', text)
            
            # URL 제거를 더 신중하게
            text = re.sub(r'https?://[^\s\]\)\n]+(?:\s|$)', '', text)
            
            # 마크다운 제거를 더 완전하게
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **굵은글씨** → 굵은글씨
            text = re.sub(r'\*\*\s*$', '', text)  # 텍스트 끝의 ** 제거
            text = re.sub(r'\*\*', '', text)  # 남은 ** 제거
            text = re.sub(r'[`#\[\]<>]', '', text)  # 일부 문자만 제거
            
            # 이모지 제거를 선택적으로
            common_emojis = r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅🔍❗🚀✅📌🎉🔧🛠️🧬]'
            text = re.sub(common_emojis, '', text)
            
            # 빈 괄호 제거
            text = re.sub(r'\(\s*\)', '', text)
            
            # DOI 정리
            text = re.sub(r'DOI\s*:\s*', '', text)
            text = re.sub(r'&[a-zA-Z]+;', '', text)
            
            # 공백 정리
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            return text.strip()
            
        except Exception as e:
            print(f"텍스트 정리 오류: {e}")
            return str(text)[:200] if text else ""
    
    def safe_text_truncate(self, text, max_length=500):
        """🔥 기존 코드의 자연스러운 텍스트 자르기 방식"""
        try:
            if len(text) <= max_length:
                return text
            
            # 일단 최대한 늘려서 시도
            extended_length = max_length + 200  # 추가 200자 여유
            if len(text) <= extended_length:
                return text
            
            # 마지막 완전한 문장 찾기
            truncated = text[:extended_length]
            
            # 마지막 문장 구분자 찾기 (한국어 우선)
            sentence_endings = ['다.', '요.', '다!', '요!', '다?', '요?', '습니다.', '입니다.', 
                              '됩니다.', '합니다.', '려고', '하여', '으로', '에서', '.', '!', '?']
            last_sentence_end = -1
            
            for ending in sentence_endings:
                pos = truncated.rfind(ending)
                if pos > last_sentence_end:
                    last_sentence_end = pos
            
            # 매우 관대하게: 전체 길이의 20% 이상에서 끝나면 사용
            if last_sentence_end > max_length * 0.2:
                # 완전한 문장 구분자의 끝까지 포함
                for ending in sentence_endings:
                    if truncated[last_sentence_end:last_sentence_end+len(ending)] == ending:
                        return text[:last_sentence_end + len(ending)]
                return text[:last_sentence_end + 1]
            else:
                # 그냥 최대한 늘려서 반환 (거의 자르지 않음)
                return text[:max_length + 300] if len(text) > max_length + 300 else text
                    
        except Exception as e:
            print(f"텍스트 자르기 오류: {e}")
            # 에러 시에도 최대한 보존
            return text[:max_length + 100] if text else ""
    
    def add_title_page(self, topic):
        """🔥 기존 코드 + 이쁜 디자인"""
        self.add_page()
        self.ln(20)
        
        try:
            # 🎨 상단 색상 바
            r, g, b = self.colors['primary']
            self.set_fill_color(r, g, b)
            self.rect(20, self.get_y(), 170, 6, 'F')
            self.ln(15)
            
            # 메인 제목
            self.set_safe_font('bold', 20, 'text_dark')
            self.multi_cell(0, 12, topic, align='C')
            self.ln(8)
            
            # 🎨 장식선
            r, g, b = self.colors['accent']
            self.set_draw_color(r, g, b)
            self.set_line_width(2)
            center_x = 105
            self.line(center_x - 30, self.get_y(), center_x + 30, self.get_y())
            self.set_line_width(0.2)  # 원래대로
            
            # 부제목
            self.ln(8)
            self.set_safe_font('normal', 14, 'text_medium')
            self.multi_cell(0, 10, '과학 연구 탐색 보고서', align='C')
            self.ln(20)
            
            # 🎨 설명 박스
            self.set_fill_color(255, 255, 255)
            self.set_draw_color(*self.colors['border'])
            self.rect(40, self.get_y(), 130, 35, 'FD')
            
            self.ln(5)
            self.set_safe_font('normal', 10, 'text_medium')
            description = "본 보고서는 AI를 활용하여 과학 연구 주제를 탐색하고,\n관련 문헌을 조사하며, 연구 계획을 수립한 결과입니다."
            lines = description.split('\n')
            for line in lines:
                self.multi_cell(0, 8, line, align='C')
            
            # 하단 정보
            self.ln(20)
            self.set_safe_font('normal', 10, 'text_light')
            today = datetime.now().strftime("%Y년 %m월 %d일")
            self.multi_cell(0, 8, f'생성일: {today}', align='C')
            self.ln(3)
            self.multi_cell(0, 8, 'LittleScienceAI', align='C')
            
        except Exception as e:
            print(f"표지 페이지 오류: {e}")
    
    def add_section_title(self, title, level=1):
        """🔥 기존 코드 + 이쁜 디자인"""
        try:
            clean_title = self.clean_text(title)
            
            if level == 1:
                # 메인 섹션은 페이지 하단에서 시작하지 않도록
                if self.get_y() > 230:
                    self.add_page()
                
                self.section_number += 1
                self.subsection_number = 0
                title_text = f"{self.section_number}. {clean_title}"
                
                # 🎨 섹션 배경 박스
                r, g, b = self.colors['bg_light']
                self.set_fill_color(r, g, b)
                self.rect(15, self.get_y()-2, 180, 18, 'F')
                
                # 🎨 사이드 컬러 바
                colors = [self.colors['primary'], self.colors['secondary'], 
                         self.colors['accent'], self.colors['warning']]
                color_idx = (self.section_number - 1) % len(colors)
                r, g, b = colors[color_idx]
                self.set_fill_color(r, g, b)
                self.rect(15, self.get_y()-2, 4, 18, 'F')
                
                self.ln(3)
                self.set_safe_font('bold', 14, 'text_dark')
                
            elif level == 2:
                # 서브섹션도 페이지 하단에서 시작하지 않도록
                if self.get_y() > 240:
                    self.add_page()
                
                self.subsection_number += 1
                title_text = f"{self.section_number}.{self.subsection_number} {clean_title}"
                
                self.ln(6)
                self.set_safe_font('bold', 12, 'text_medium')
            
            self.multi_cell(0, 8, title_text, align='L')
            self.ln(4)
            
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
    
    def add_paper_item(self, title, summary, source=""):
        """🔥 기존 코드 + 이쁜 카드 디자인"""
        try:
            # 페이지 하단에서 논문 항목이 시작되면 새 페이지로
            if self.get_y() > 220:
                self.add_page()
            
            card_start_y = self.get_y()
            
            # 🎨 카드 타입별 색상
            if "ISEF" in source:
                border_color = self.colors['primary']
                bg_color = (239, 246, 255)  # 연한 파란색
                icon = "🏆"
            elif "arXiv" in source:
                border_color = self.colors['secondary']
                bg_color = (236, 253, 245)  # 연한 초록색
                icon = "📚"
            else:
                border_color = self.colors['text_light']
                bg_color = self.colors['bg_light']
                icon = "📄"
            
            # 🎨 카드 배경
            self.set_fill_color(*bg_color)
            self.set_draw_color(*self.colors['border'])
            card_height = 40
            self.rect(20, card_start_y, 170, card_height, 'FD')
            
            # 🎨 사이드 컬러 바
            self.set_fill_color(*border_color)
            self.rect(20, card_start_y, 3, card_height, 'F')
            
            # 내용
            self.ln(3)
            self.set_x(28)
            
            # 제목
            self.set_safe_font('bold', 10, 'text_dark')
            clean_title = self.clean_text(title)
            
            # 🔥 기존 코드의 길이 제한 방식 사용
            if len(clean_title) > 300:
                clean_title = self.safe_text_truncate(clean_title, 300) + "..."
            
            title_with_icon = f"{icon} {clean_title}"
            self.multi_cell(165, 7, title_with_icon, align='L')
            
            # 출처
            if source:
                self.set_x(28)
                self.set_safe_font('normal', 8, 'text_light')
                self.multi_cell(165, 5, source, align='L')
            
            # 요약
            self.set_x(28)
            self.set_safe_font('normal', 9, 'text_medium')
            clean_summary = self.clean_text(summary)
            
            # 🔥 기존 코드의 길이 제한 방식 사용 (확장됨)
            if len(clean_summary) > 500:
                clean_summary = self.safe_text_truncate(clean_summary, 500)
            
            if clean_summary:
                self.multi_cell(165, 6, clean_summary, align='L')
            
            self.ln(6)
            
        except Exception as e:
            print(f"논문 항목 오류: {e}")
    
    def add_paper_section(self, title, content, section_number):
        """🔥 기존 코드 + 이쁜 디자인"""
        try:
            self.ln(8)
            
            # 🎨 섹션별 아이콘
            icons = {
                '초록': '📋', '서론': '📖', '실험': '🔬', 
                '예상': '📊', '시각': '📈', '결론': '🎯', '참고': '📚'
            }
            icon = "📌"
            for key, ico in icons.items():
                if key in title:
                    icon = ico
                    break
            
            self.set_safe_font('bold', 12, 'text_dark')
            section_title = f"{icon} {section_number}. {title}"
            self.multi_cell(0, 8, section_title, align='L')
            
            # 🎨 제목 아래 라인
            r, g, b = self.colors['primary']
            self.set_draw_color(r, g, b)
            self.set_line_width(1)
            self.line(20, self.get_y(), 80, self.get_y())
            self.set_line_width(0.2)  # 원래대로
            
            self.ln(4)
            
            if "참고문헌" in title or "References" in title:
                self.add_professional_references()
            else:
                self.set_safe_font('normal', 10, 'text_medium')
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
        """🔥 기존 코드 그대로 유지"""
        try:
            self.set_safe_font('normal', 10, 'text_medium')
            guide_text = "실제 연구 수행 시, 주요 학술검색 사이트를 활용하여 관련 논문들을 찾아 참고문헌에 추가하시기 바랍니다."
            self.multi_cell(0, 6, guide_text, align='L')
            self.ln(6)
            
            self.set_safe_font('bold', 10, 'text_dark')
            self.multi_cell(0, 7, "참고문헌 작성 양식 (APA Style):", align='L')
            self.ln(3)
            
            self.set_safe_font('normal', 9, 'text_medium')
            
            examples = [
                "【학술지 논문】",
                "김철수, 이영희. (2024). 플라즈마 기술을 이용한 공기정화 시스템 개발. 한국과학기술학회지, 45(3), 123-135.",
                "",
                "【온라인 자료】",
                "국가과학기술정보센터. (2024). 플라즈마 기술 동향 보고서.",
                "",
                "【서적】",
                "홍길동. (2023). 현대 플라즈마 물리학. 서울: 과학기술출판사."
            ]
            
            for example in examples:
                if example.startswith('【') and example.endswith('】'):
                    self.set_safe_font('bold', 9, 'text_dark')
                    self.multi_cell(0, 6, example, align='L')
                    self.ln(2)
                elif example == "":
                    self.ln(2)
                else:
                    self.set_safe_font('normal', 9, 'text_medium')
                    self.multi_cell(0, 5, example, align='L')
                    self.ln(1)
            
        except Exception as e:
            print(f"참고문헌 가이드 오류: {e}")

def extract_topic_from_content(content):
    """🔥 기존 코드 그대로"""
    try:
        title_match = re.search(r'# 📘\s*([^\n-]+)', content)
        if title_match:
            topic = title_match.group(1).strip()
            return topic[:50] if len(topic) > 50 else topic
        return "과학 연구 탐색"
    except:
        return "과학 연구 탐색"

def parse_content_enhanced(content):
    """🔥 기존 코드의 파싱 로직 사용 (완전히 새로운 파싱)"""
    result = {
        'topic_explanation': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("🔍 파싱 로직 시작...")
        print(f"전체 콘텐츠 길이: {len(content)}")
        
        # 전체 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            result['topic_explanation'] = full_explanation
            print(f"주제 해설 추출 성공: {len(full_explanation)}자")
            
            # 🔥 틈새주제 파싱
            if '확장 가능한 탐구' in full_explanation:
                ideas_start = full_explanation.find('확장 가능한 탐구')
                ideas_section = full_explanation[ideas_start:]
                print(f"틈새주제 섹션: {ideas_section[:200]}...")
                
                # 간단하게 전체를 가져와서 정리
                lines = ideas_section.split('\n')
                clean_lines = []
                
                for line in lines[1:]:  # 첫 줄(제목) 제외
                    line = line.strip()
                    if line and len(line) > 10 and not any(skip in line for skip in ['키워드', 'Scholar', '도메인']):
                        # • · 패턴을 • 로 시작하는 제목과 설명으로 분리
                        if '• ·' in line:
                            parts = line.split('• ·')
                            if len(parts) >= 2:
                                title = parts[0].replace('•', '').strip()
                                desc = parts[1].strip()
                                clean_lines.append(f"• {title}")
                                clean_lines.append(f"  {desc}")
                        elif line.startswith('•'):
                            clean_lines.append(line)
                        elif line.startswith('·') and clean_lines:
                            clean_lines.append(f"  {line[1:].strip()}")
                        else:
                            clean_lines.append(line)
                
                result['research_ideas'] = '\n'.join(clean_lines)
                print(f"틈새주제 파싱 완료: {len(clean_lines)}줄")
        
        # 🔥 ISEF/arXiv 파싱 - 더 관대하게
        # ISEF 검색
        isef_papers = []
        if "ISEF" in content:
            # 모든 ▪ 또는 - ** 패턴 찾기
            isef_section = content[content.find("ISEF"):content.find("arXiv") if "arXiv" in content else len(content)]
            print(f"ISEF 섹션 길이: {len(isef_section)}")
            
            # 여러 패턴 시도
            patterns = [
                r'▪\s*([^\n]+)\n[^\n]*출처[^\n]*\n\s*([^▪]+?)(?=▪|\n\n|$)',
                r'-\s*\*\*([^*]+)\*\*[^\n]*\n([^-]+?)(?=-|\n\n|$)',
                r'📌\s*([^\n]+).*?\n.*?\n([^📌]+?)(?=📌|\n\n|$)'  # 새 패턴 추가
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, isef_section, re.DOTALL)
                for title, summary in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                    if len(clean_title) > 5 and len(clean_summary) > 20:
                        # 요약 길이 확장
                        if len(clean_summary) > 500:
                            sentences = re.split(r'[.!?]\s+', clean_summary)
                            kept_sentences = []
                            total_len = 0
                            for sent in sentences:
                                if total_len + len(sent) < 800:
                                    kept_sentences.append(sent)
                                    total_len += len(sent)
                                else:
                                    break
                            clean_summary = '. '.join(kept_sentences)
                            if not clean_summary.endswith('.'):
                                clean_summary += '.'
                        
                        isef_papers.append((clean_title, clean_summary))
                        if len(isef_papers) >= 3:
                            break
                if isef_papers:
                    break
        
        result['isef_papers'] = isef_papers
        print(f"ISEF 논문 파싱: {len(isef_papers)}개")
        
        # arXiv 검색
        arxiv_papers = []
        if "arXiv" in content:
            arxiv_section = content[content.find("arXiv"):]
            print(f"arXiv 섹션 길이: {len(arxiv_section)}")
            
            patterns = [
                r'▪\s*([^\n]+)\n[^\n]*arXiv[^\n]*\n\s*([^▪]+?)(?=▪|\n\n|$)',
                r'-\s*\*\*([^*]+)\*\*[^\n]*\n([^-]+?)(?=\[링크\]|-|\n\n|$)',
                r'🌐\s*([^\n]+).*?\n.*?\n([^🌐]+?)(?=🌐|\n\n|$)'  # 새 패턴 추가
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, arxiv_section, re.DOTALL)
                for title, summary in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                    
                    # 한국어 요약 부분만 추출
                    if '한국어 요약' in clean_summary:
                        clean_summary = clean_summary.split('한국어 요약')[1].split('영문 원본')[0].strip()
                    
                    if len(clean_title) > 5 and len(clean_summary) > 20:
                        # 요약 길이 확장
                        if len(clean_summary) > 500:
                            sentences = re.split(r'[.!?]\s+', clean_summary)
                            kept_sentences = []
                            total_len = 0
                            for sent in sentences:
                                if total_len + len(sent) < 800:
                                    kept_sentences.append(sent)
                                    total_len += len(sent)
                                else:
                                    break
                            clean_summary = '. '.join(kept_sentences)
                            if not clean_summary.endswith('.'):
                                clean_summary += '.'
                        
                        arxiv_papers.append((clean_title, clean_summary))
                        if len(arxiv_papers) >= 3:
                            break
                if arxiv_papers:
                    break
        
        result['arxiv_papers'] = arxiv_papers
        print(f"arXiv 논문 파싱: {len(arxiv_papers)}개")
        
        # 생성된 논문 파싱 (기존 유지)
        if "생성된 연구 논문" in content:
            paper_section = content[content.find("생성된 연구 논문"):]
            sections = ['초록', '서론', '실험 방법', '예상 결과', '시각자료', '결론', '참고문헌']
            for section in sections:
                pattern = f"### {section}[^\n]*\n(.*?)(?=###|$)"
                match = re.search(pattern, paper_section, re.DOTALL)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 10:
                        result['generated_paper'][section] = content_text
        
        print(f"🔚 파싱 완료!")
        return result
        
    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """🔥 단계별 디버깅 - 하나씩 기능 추가"""
    try:
        print("🚀 PDF 생성 시작...")
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        print(f"📝 주제 추출: {topic}")
        
        # 향상된 파싱 사용
        print("🔍 내용 파싱 시작...")
        sections = parse_content_enhanced(content)
        print(f"📊 파싱 결과: 해설({len(sections['topic_explanation'])}자), ISEF({len(sections['isef_papers'])}개), arXiv({len(sections['arxiv_papers'])}개), 논문({len(sections['generated_paper'])}섹션)")
        
        # PDF 생성
        with suppress_fpdf_warnings():
            pdf = BeautifulSciencePDF(topic)
            
            # 1단계: 표지 페이지 (이건 성공했음)
            print("📄 1단계: 표지 페이지...")
            pdf.add_title_page(topic)
            print("✅ 표지 완료")
            
            # 2단계: 새 페이지 + 간단 테스트 (이것도 성공했음)
            print("📝 2단계: 기본 페이지...")
            pdf.add_page()
            pdf.set_safe_font('bold', 14, 'text_dark')
            pdf.cell(0, 10, "=== 연구 탐색 보고서 ===", align='C', ln=True)
            pdf.ln(10)
            print("✅ 기본 페이지 완료")
            
            # 3단계: add_section_title 테스트
            print("🔬 3단계: 섹션 제목 테스트...")
            try:
                pdf.add_section_title("주제 개요")
                print("✅ 섹션 제목 성공")
            except Exception as e:
                print(f"❌ 섹션 제목 실패: {e}")
                # 실패시 간단하게 대체
                pdf.set_safe_font('bold', 12, 'text_dark')
                pdf.cell(0, 8, "1. 주제 개요", align='L', ln=True)
                pdf.ln(5)
            
            # 4단계: 간단한 텍스트 추가
            print("📝 4단계: 텍스트 추가...")
            try:
                if sections['topic_explanation']:
                    explanation = sections['topic_explanation'][:500]  # 처음 500자만
                    clean_text = pdf.clean_text(explanation)
                    pdf.set_safe_font('normal', 10, 'text_medium')
                    pdf.multi_cell(0, 6, clean_text[:200], align='L')  # 더 짧게
                    pdf.ln(5)
                    print("✅ 텍스트 추가 성공")
                else:
                    pdf.set_safe_font('normal', 10, 'text_medium')
                    pdf.cell(0, 6, "주제 해설이 없습니다.", align='L', ln=True)
            except Exception as e:
                print(f"❌ 텍스트 추가 실패: {e}")
                pdf.set_safe_font('normal', 10, 'text_medium')
                pdf.cell(0, 6, "텍스트 처리 중 오류 발생", align='L', ln=True)
            
            # 5단계: ISEF 논문 (간단 버전)
            print("🏆 5단계: ISEF 논문...")
            try:
                pdf.set_safe_font('bold', 12, 'text_dark')
                pdf.cell(0, 8, "2. ISEF 관련 연구", align='L', ln=True)
                pdf.ln(3)
                
                if sections['isef_papers']:
                    for i, (title, summary) in enumerate(sections['isef_papers'][:2]):  # 최대 2개만
                        pdf.set_safe_font('bold', 10, 'text_dark')
                        clean_title = pdf.clean_text(title)[:100]  # 100자만
                        pdf.cell(0, 6, f"🏆 {clean_title}", align='L', ln=True)
                        
                        pdf.set_safe_font('normal', 9, 'text_medium')
                        clean_summary = pdf.clean_text(summary)[:200]  # 200자만
                        pdf.multi_cell(0, 5, clean_summary, align='L')
                        pdf.ln(3)
                        print(f"✅ ISEF 논문 {i+1} 성공")
                else:
                    pdf.set_safe_font('normal', 10, 'text_medium')
                    pdf.cell(0, 6, "관련 ISEF 프로젝트가 없습니다.", align='L', ln=True)
                    
            except Exception as e:
                print(f"❌ ISEF 논문 실패: {e}")
                pdf.set_safe_font('normal', 10, 'text_medium')
                pdf.cell(0, 6, "ISEF 논문 처리 중 오류 발생", align='L', ln=True)
            
            # 6단계: arXiv 논문 (간단 버전)
            print("📚 6단계: arXiv 논문...")
            try:
                pdf.ln(5)
                pdf.set_safe_font('bold', 12, 'text_dark')
                pdf.cell(0, 8, "3. arXiv 최신 연구", align='L', ln=True)
                pdf.ln(3)
                
                if sections['arxiv_papers']:
                    for i, (title, summary) in enumerate(sections['arxiv_papers'][:2]):  # 최대 2개만
                        pdf.set_safe_font('bold', 10, 'text_dark')
                        clean_title = pdf.clean_text(title)[:100]  # 100자만
                        pdf.cell(0, 6, f"📚 {clean_title}", align='L', ln=True)
                        
                        pdf.set_safe_font('normal', 9, 'text_medium')
                        clean_summary = pdf.clean_text(summary)[:200]  # 200자만
                        pdf.multi_cell(0, 5, clean_summary, align='L')
                        pdf.ln(3)
                        print(f"✅ arXiv 논문 {i+1} 성공")
                else:
                    pdf.set_safe_font('normal', 10, 'text_medium')
                    pdf.cell(0, 6, "관련 arXiv 논문이 없습니다.", align='L', ln=True)
                    
            except Exception as e:
                print(f"❌ arXiv 논문 실패: {e}")
                pdf.set_safe_font('normal', 10, 'text_medium')
                pdf.cell(0, 6, "arXiv 논문 처리 중 오류 발생", align='L', ln=True)
            
            # 7단계: 생성된 논문 (간단 버전)
            print("📝 7단계: 연구 계획서...")
            try:
                if sections['generated_paper']:
                    pdf.add_page()  # 새 페이지
                    
                    pdf.set_safe_font('bold', 16, 'text_dark')
                    pdf.cell(0, 10, "연구 계획서", align='C', ln=True)
                    pdf.ln(10)
                    
                    section_order = ['초록', '서론', '실험 방법', '예상 결과', '결론']
                    for i, section_name in enumerate(section_order):
                        if section_name in sections['generated_paper']:
                            content_text = sections['generated_paper'][section_name]
                            
                            pdf.set_safe_font('bold', 12, 'text_dark')
                            pdf.cell(0, 8, f"{i+1}. {section_name}", align='L', ln=True)
                            pdf.ln(2)
                            
                            pdf.set_safe_font('normal', 10, 'text_medium')
                            clean_content = pdf.clean_text(content_text)[:300]  # 300자만
                            pdf.multi_cell(0, 6, clean_content, align='L')
                            pdf.ln(5)
                            
                            print(f"✅ {section_name} 섹션 성공")
                    
            except Exception as e:
                print(f"❌ 연구 계획서 실패: {e}")
                pdf.set_safe_font('normal', 10, 'text_medium')
                pdf.cell(0, 6, "연구 계획서 처리 중 오류 발생", align='L', ln=True)
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            print(f"💾 PDF 저장...")
            
            with suppress_fpdf_warnings():
                pdf.output(output_path)
            print("✅ PDF 저장 완료")
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"📊 생성된 파일 크기: {file_size:,} bytes")
            
            if file_size > 3000:  # 3KB 이상이면 성공
                print(f"🎉 단계별 PDF 생성 성공!")
                return output_path
            else:
                print(f"⚠️ 파일이 너무 작음: {file_size} bytes")
                raise Exception(f"PDF 파일 크기가 비정상적으로 작음")
        else:
            raise Exception("PDF 파일이 생성되지 않음")
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        
        # 실패시 텍스트 백업
        try:
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {extract_topic_from_content(content)} 연구보고서 ===\n\n")
                f.write(f"생성 시간: {datetime.now()}\n\n")
                f.write(content[:1000])  # 처음 1000자만
            return txt_path
        except:
            return None

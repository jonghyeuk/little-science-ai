from fpdf import FPDF
import os
import re
import warnings
from datetime import datetime
import logging
import contextlib

# 로깅 레벨 조정
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

# 강화된 경고 억제 - 모든 fpdf 관련 경고 무시
warnings.filterwarnings("ignore", message="cmap value too big/small")
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")
warnings.filterwarnings("ignore", category=UserWarning, message=".*fpdf.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fpdf")
warnings.filterwarnings("ignore", message=".*font.*")
warnings.filterwarnings("ignore", message=".*PDF.*")
warnings.filterwarnings("ignore", message=".*unicode.*")

@contextlib.contextmanager
def suppress_fpdf_warnings():
    """PDF 생성 중 모든 경고 억제"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

# 폰트 경로
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
FONT_EXTRABOLD = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")
OUTPUT_DIR = "outputs"

class ImprovedKoreanPDF(FPDF):
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
            with suppress_fpdf_warnings():
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
                # 🎨 헤더 색상 개선
                self.set_text_color(100, 100, 100)
                header_text = f'{self.topic[:30]}... - 연구보고서' if len(self.topic) > 30 else f'{self.topic} - 연구보고서'
                self.cell(0, 10, header_text, align='R', ln=True)
                self.ln(3)
            except:
                pass
            
    def footer(self):
        try:
            self.set_y(-15)
            self.set_safe_font('normal', 9)
            # 🎨 푸터 색상 개선
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def add_title_page(self, topic):
        self.add_page()
        self.ln(30)
        
        try:
            # 🎨 제목 - 파란색 볼드
            self.set_safe_font('bold', 22)
            self.set_text_color(25, 118, 210)  # Material Blue
            self.multi_cell(0, 12, topic, align='C')
            self.ln(8)
            
            # 🎨 부제목 - 진한 회색
            self.set_safe_font('bold', 16)
            self.set_text_color(55, 71, 79)  # Blue Grey
            self.multi_cell(0, 10, '연구 탐색 보고서', align='C')
            self.ln(30)
            
            # 🎨 날짜 정보 - 중간 회색
            self.set_safe_font('normal', 11)
            self.set_text_color(96, 125, 139)  # Blue Grey Light
            today = datetime.now().strftime("%Y년 %m월 %d일")
            self.multi_cell(0, 8, f'생성일: {today}', align='C')
            self.ln(3)
            
            # 🎨 브랜드 - 초록색
            self.set_safe_font('bold', 12)
            self.set_text_color(76, 175, 80)  # Material Green
            self.multi_cell(0, 8, 'LittleScienceAI', align='C')
            
        except Exception as e:
            print(f"표지 페이지 오류: {e}")
    
    def add_section_title(self, title, level=1):
        try:
            clean_title = self.clean_text(title)
            
            if level == 1:
                # 메인 섹션은 페이지 하단에서 시작하지 않도록
                if self.get_y() > 230:
                    self.add_page()
                
                self.section_number += 1
                self.subsection_number = 0
                title_text = f"{self.section_number}. {clean_title}"
                
                self.ln(12)
                # 🎨 메인 섹션 - 진한 파란색 볼드
                self.set_safe_font('bold', 16)
                self.set_text_color(13, 71, 161)  # Indigo
                
            elif level == 2:
                # 서브섹션도 페이지 하단에서 시작하지 않도록
                if self.get_y() > 240:
                    self.add_page()
                
                self.subsection_number += 1
                title_text = f"{self.section_number}.{self.subsection_number} {clean_title}"
                
                self.ln(8)
                # 🎨 서브 섹션 - 중간 파란색 볼드
                self.set_safe_font('bold', 13)
                self.set_text_color(21, 101, 192)  # Blue
            
            self.multi_cell(0, 8, title_text, align='L')
            self.ln(4)
            
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
    
    def add_elegant_subsection(self, title):
        try:
            # 페이지 끝에서 소제목이 혼자 남지 않도록 체크
            if self.get_y() > 250:
                self.add_page()
            
            self.ln(6)
            # 🎨 소제목 - 초록색 볼드
            self.set_safe_font('bold', 12)
            self.set_text_color(56, 142, 60)  # Green
            clean_title = self.clean_text(title)
            self.multi_cell(0, 7, clean_title, align='L')
            self.ln(3)
        except Exception as e:
            print(f"소제목 오류: {e}")
    
    def add_paragraph(self, text):
        try:
            # 🎨 일반 텍스트 - 진한 회색
            self.set_safe_font('normal', 10)
            self.set_text_color(55, 55, 55)
            
            clean_text = self.clean_text(text)
            if clean_text and len(clean_text.strip()) > 5:
                # 🔧 자연스러운 문단 분할
                if len(clean_text) > 800:
                    # 문장 단위로 분할
                    sentences = re.split(r'([.!?]\s+)', clean_text)
                    current_chunk = ""
                    
                    for i in range(0, len(sentences), 2):
                        if i+1 < len(sentences):
                            sentence = sentences[i] + sentences[i+1]
                        else:
                            sentence = sentences[i]
                        
                        if len(current_chunk + sentence) <= 800:
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                self.multi_cell(0, 6, current_chunk.strip(), align='L')
                                self.ln(3)
                                current_chunk = sentence
                            else:
                                self.multi_cell(0, 6, sentence, align='L')
                                self.ln(3)
                    
                    if current_chunk.strip():
                        self.multi_cell(0, 6, current_chunk.strip(), align='L')
                        self.ln(3)
                else:
                    self.multi_cell(0, 6, clean_text, align='L')
                    self.ln(3)
                
        except Exception as e:
            print(f"문단 추가 오류: {e}")
    
    def add_formatted_content(self, text):
        """🎨 웹 내용을 구조화해서 PDF에 추가 - 검색 관련 내용 제거"""
        try:
            if not text:
                return
                
            # 문단별로 분리
            paragraphs = text.split('\n\n')
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue
                
                # 🔥 검색 관련 문단 완전 제거
                paragraph_lower = paragraph.lower()
                skip_paragraph = any([
                    '키워드 조합' in paragraph,
                    'google scholar' in paragraph_lower,
                    '검색 사이트' in paragraph,
                    'scholar.google.com' in paragraph_lower,
                    'academic.naver.com' in paragraph_lower,
                    'riss.kr' in paragraph_lower,
                    'dbpia.co.kr' in paragraph_lower,
                    '이 키워드로 검색하면' in paragraph,
                    '연구들을 찾을 수 있' in paragraph,
                    '최신논문검색' in paragraph,
                    'https://' in paragraph and ('scholar' in paragraph_lower or 'academic' in paragraph_lower),
                    '네이버 학술정보' in paragraph,
                    'RISS' in paragraph,
                    'DBpia' in paragraph
                ])
                
                if skip_paragraph:
                    print(f"🚫 검색 관련 문단 제거: {paragraph[:50]}...")
                    continue
                
                # 🔥 소제목 감지 (이모지로 시작하는 경우)
                if any(emoji in paragraph[:10] for emoji in ['🧪', '🔧', '🌍', '🌎', '💡', '📊', '⚙️', '🔬', '🎯']):
                    lines = paragraph.split('\n')
                    if lines:
                        # 첫 줄을 소제목으로
                        subtitle = lines[0].strip()
                        self.add_elegant_subsection(subtitle)
                        
                        # 나머지 내용이 있으면 문단으로
                        if len(lines) > 1:
                            remaining_content = '\n'.join(lines[1:]).strip()
                            if remaining_content:
                                self.add_formatted_paragraph(remaining_content)
                
                # 🔥 일반 문단 처리
                else:
                    self.add_formatted_paragraph(paragraph)
                    
        except Exception as e:
            print(f"포맷된 내용 추가 오류: {e}")
            # 오류 시 기본 문단으로 처리
            self.add_paragraph(text)
    
    def add_formatted_paragraph(self, text):
        """🎨 문단을 보기 좋게 포맷팅해서 추가"""
        try:
            # 🎨 일반 텍스트 - 진한 회색
            self.set_safe_font('normal', 10)
            self.set_text_color(55, 55, 55)
            
            clean_text = self.clean_text(text)
            if not clean_text or len(clean_text.strip()) <= 5:
                return
            
            # 🔥 줄 단위로 처리 (들여쓰기 고려)
            lines = clean_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    self.ln(3)  # 빈 줄 간격
                    continue
                
                # 🔥 리스트 항목 감지 (-, •, 1., 2. 등)
                if re.match(r'^[-•·]\s+', line) or re.match(r'^\d+\.\s+', line):
                    # 리스트 항목은 들여쓰기 적용
                    self.cell(8, 6, '', ln=0)  # 들여쓰기
                    list_content = re.sub(r'^[-•·]\s+|^\d+\.\s+', '', line)
                    self.multi_cell(0, 6, list_content, align='L')
                    self.ln(2)
                
                # 🔥 일반 텍스트
                else:
                    # 긴 문장은 자연스럽게 분할
                    if len(line) > 600:
                        sentences = re.split(r'([.!?]\s+)', line)
                        current_chunk = ""
                        
                        for i in range(0, len(sentences), 2):
                            if i+1 < len(sentences):
                                sentence = sentences[i] + sentences[i+1]
                            else:
                                sentence = sentences[i]
                            
                            if len(current_chunk + sentence) <= 600:
                                current_chunk += sentence
                            else:
                                if current_chunk:
                                    self.multi_cell(0, 6, current_chunk.strip(), align='L')
                                    self.ln(3)
                                    current_chunk = sentence
                                else:
                                    self.multi_cell(0, 6, sentence, align='L')
                                    self.ln(3)
                        
                        if current_chunk.strip():
                            self.multi_cell(0, 6, current_chunk.strip(), align='L')
                            self.ln(3)
                    else:
                        self.multi_cell(0, 6, line, align='L')
                        self.ln(3)
            
            # 문단 끝에 추가 간격
            self.ln(2)
                
        except Exception as e:
            print(f"포맷된 문단 추가 오류: {e}")
            # 오류 시 기본 처리
            self.multi_cell(0, 6, self.clean_text(text), align='L')
            self.ln(3)
    
    def add_beautiful_research_ideas(self, text):
        """🎨 탐구아이디어 예쁘게 포맷팅 - 기존 파싱 결과 사용"""
        try:
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # ** 제거하고 • 시작하는 제목 처리
                if line.startswith('•') or '**' in line:
                    # 🎨 아이디어 제목 - 보라색 볼드
                    self.set_safe_font('bold', 11)
                    self.set_text_color(123, 31, 162)  # Purple
                    
                    # ** 제거하고 정리
                    title = line.replace('**', '').strip()
                    if not title.startswith('•'):
                        title = f"• {title}"
                    
                    self.multi_cell(0, 7, title, align='L')
                    self.ln(2)
                    
                elif line.startswith('·') or line.startswith('-') or (len(line) > 10 and not line.startswith('•')):
                    # 🎨 설명 - 진한 회색, 들여쓰기
                    self.set_safe_font('normal', 10)
                    self.set_text_color(70, 70, 70)
                    
                    # ·, - 제거하고 설명 텍스트 추출
                    desc = line.replace('·', '').replace('-', '').strip()
                    if desc:
                        # 들여쓰기 적용
                        self.cell(15, 6, '', ln=0)  # 들여쓰기 공간
                        self.multi_cell(0, 6, desc, align='L')
                        self.ln(3)
            
        except Exception as e:
            print(f"탐구아이디어 포맷팅 오류: {e}")
    
    def add_paper_title_page(self, topic, selected_idea):
        self.add_page()
        self.ln(20)
        
        try:
            # 🎨 논문 제목 - 진한 파란색 대형 볼드
            self.set_safe_font('bold', 18)
            self.set_text_color(25, 118, 210)
            paper_title = f"{topic}: 연구 계획서"
            self.multi_cell(0, 12, paper_title, align='C')
            self.ln(15)
            
            # 🎨 구분선 - 연한 회색
            self.set_draw_color(200, 200, 200)
            self.line(30, self.get_y(), 180, self.get_y())
            self.ln(8)
            
        except Exception as e:
            print(f"논문 제목 페이지 오류: {e}")
    
    def add_paper_section(self, title, content, section_number):
        try:
            self.ln(8)
            # 🎨 논문 섹션 제목 - 진한 청록색 볼드
            self.set_safe_font('bold', 13)
            self.set_text_color(0, 105, 92)  # Teal
            section_title = f"{section_number}. {title}"
            self.multi_cell(0, 8, section_title, align='L')
            self.ln(4)
            
            if "참고문헌" in title or "References" in title:
                self.add_professional_references()
            else:
                # 🎨 논문 내용 - 검은색에 가까운 진한 회색
                self.set_safe_font('normal', 10)
                self.set_text_color(40, 40, 40)
                clean_content = self.clean_text(content)
                
                if clean_content:
                    paragraphs = clean_content.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            self.add_paragraph(para.strip())
            
        except Exception as e:
            print(f"논문 섹션 오류: {e}")
    
    def add_professional_references(self):
        """🎨 컬러풀한 참고문헌 가이드"""
        try:
            # 🎨 안내 텍스트 - 진한 회색
            self.set_safe_font('normal', 10)
            self.set_text_color(70, 70, 70)
            guide_text = "실제 연구 수행 시, 주요 학술검색 사이트를 활용하여 관련 논문들을 찾아 참고문헌에 추가하시기 바랍니다."
            self.multi_cell(0, 6, guide_text, align='L')
            self.ln(6)
            
            # 🎨 양식 제목 - 진한 파란색 볼드
            self.set_safe_font('bold', 11)
            self.set_text_color(13, 71, 161)
            self.multi_cell(0, 7, "참고문헌 작성 양식 (APA Style):", align='L')
            self.ln(3)
            
            examples = [
                ("【학술지 논문】", True),
                ("김철수, 이영희. (2024). 플라즈마 기술을 이용한 공기정화 시스템 개발. 한국과학기술학회지, 45(3), 123-135.", False),
                ("", False),
                ("【온라인 자료】", True),
                ("국가과학기술정보센터. (2024). 플라즈마 기술 동향 보고서.", False),
                ("", False),
                ("【서적】", True),
                ("홍길동. (2023). 현대 플라즈마 물리학. 서울: 과학기술출판사.", False)
            ]
            
            for text, is_header in examples:
                if text == "":
                    self.ln(2)
                elif is_header:
                    # 🎨 헤더 - 초록색 볼드
                    self.set_safe_font('bold', 10)
                    self.set_text_color(76, 175, 80)
                    self.multi_cell(0, 6, text, align='L')
                    self.ln(2)
                else:
                    # 🎨 예시 - 일반 회색
                    self.set_safe_font('normal', 9)
                    self.set_text_color(80, 80, 80)
                    self.multi_cell(0, 5, text, align='L')
                    self.ln(1)
            
        except Exception as e:
            print(f"참고문헌 가이드 오류: {e}")
    
    def add_guidelines_page(self):
        """📋 논문 작성 가이드라인 페이지 추가"""
        try:
            self.add_page()
            self.ln(15)
            
            # 🎨 페이지 제목 - 진한 주황색 볼드
            self.set_safe_font('bold', 18)
            self.set_text_color(230, 81, 0)  # Deep Orange
            self.multi_cell(0, 12, "📋 고품질 논문 작성 가이드라인", align='C')
            self.ln(8)
            
            # 🎨 구분선
            self.set_draw_color(230, 81, 0)
            self.line(30, self.get_y(), 180, self.get_y())
            self.ln(8)
            
            # 📝 제목 작성법
            self.add_guideline_section("📝 제목 작성 원칙", [
                "실험의 핵심 내용과 주제를 명확히 암시하는 제목을 작성하세요.",
                "구체적인 실험 방법이나 연구 대상을 포함하면 더욱 효과적입니다.",
                "예시: '플라즈마를 이용한 공기 정화 효율성 연구'처럼 명확하게 표현"
            ])
            
            # 📋 초록 작성법  
            self.add_guideline_section("📋 초록(Abstract) 핵심 요소", [
                "논문 전체를 대표하는 글이므로 연구의 핵심을 담아야 합니다.",
                "간단한 실험 결과와 그 의미를 반드시 포함하세요.",
                "독자가 초록만 읽어도 연구의 가치를 이해할 수 있도록 작성",
                "150-200단어 내외로 간결하지만 완결성 있게 구성"
            ])
            
            # 📖 서론 작성법
            self.add_guideline_section("📖 서론(Introduction) 필수 요소", [
                "이 실험을 하게 된 당위성을 명확히 제시해야 합니다.",
                "현재 상황에서 이 실험이 갖는 의미와 목적을 구체적으로 설명",
                "모든 주장은 반드시 레퍼런스(참고논문)로 뒷받침하세요.",
                "기존 연구의 한계점을 제시하고 본 연구의 차별점을 부각",
                "※ 레퍼런스 없는 주장은 설득력이 떨어집니다!"
            ])
            
            # 🔬 실험방법 작성법
            self.add_guideline_section("🔬 실험방법(Methods) 작성 원칙", [
                "사용한 모든 장치, 재료, 시약을 정확히 기술하세요.",
                "실험 절차를 단계별로 상세히 설명 (다른 사람이 재현 가능하도록)",
                "측정 방법과 데이터 수집 과정을 명확히 제시",
                "실험 조건(온도, 압력, pH 등)을 구체적으로 명시"
            ])
            
            # 📊 실험결과 작성법  
            self.add_guideline_section("📊 실험결과(Results) 작성 핵심", [
                "객관성을 철저히 유지하며 결과물을 설명하세요.",
                "모든 해석과 설명은 레퍼런스로 뒷받침되어야 합니다.",
                "인과관계가 명확해야 하며, 무작정 주장하지 마세요.",
                "관련 논문을 많이 읽고 어떤 내용이 있었는지 기억해 활용",
                "※ 주관적 추측보다는 논문 근거를 바탕으로 설명하세요!"
            ])
            
            # 🎯 결론 작성법
            self.add_guideline_section("🎯 결론(Conclusion) 작성 요령", [
                "실험을 통해 명확히 알 수 있었던 것만 간결하게 정리",
                "가설 검증 결과와 연구의 의의를 명확히 제시",
                "한계점도 솔직하게 언급하여 신뢰성을 높이세요.",
                "향후 연구 방향이나 개선점을 제안하면 더욱 완성도 높은 결론"
            ])
            
            # 📚 참고문헌 관리법
            self.add_guideline_section("📚 참고문헌(References) 관리", [
                "서론, 본론에서 인용한 모든 레퍼런스를 넘버링하여 정리",
                "신뢰할 수 있는 학술 자료만 사용 (SCI급 논문 우선)",
                "최근 5년 이내 발표된 논문을 우선적으로 활용",
                "APA 스타일에 맞춰 일관성 있게 작성하세요."
            ])
            
            # 🌟 중요 안내사항
            self.ln(8)
            self.set_safe_font('bold', 12)
            self.set_text_color(220, 53, 69)  # Red
            self.multi_cell(0, 8, "⚠️ 필독 안내사항", align='C')
            self.ln(4)
            
            self.set_safe_font('normal', 10)
            self.set_text_color(60, 60, 60)
            important_notice = """서비스 가이드를 반드시 숙지하시기 바랍니다. 
            
고품질 논문 작성을 위해서는 충분한 관련 논문 연구가 선행되어야 하며, 
모든 주장과 해석은 신뢰할 수 있는 학술 자료를 근거로 해야 합니다.

레퍼런스의 활용은 단순한 인용이 아니라, 여러분의 주장을 뒷받침하는 
과학적 근거로 사용되어야 한다는 점을 명심하세요."""
            
            self.multi_cell(0, 6, important_notice, align='L')
            self.ln(8)
            
            # 🎨 마무리 메시지
            self.set_safe_font('bold', 12)
            self.set_text_color(76, 175, 80)  # Green
            self.multi_cell(0, 8, "🌟 과학적 사고와 체계적 연구로 훌륭한 논문을 완성하세요!", align='C')
            self.ln(4)
            
            self.set_safe_font('normal', 9)
            self.set_text_color(100, 100, 100)
            self.multi_cell(0, 6, "- LittleScienceAI에서 제공하는 논문 작성 가이드라인 -", align='C')
            
        except Exception as e:
            print(f"가이드라인 페이지 오류: {e}")
    
    def add_guideline_section(self, title, items):
        """가이드라인 섹션 추가"""
        try:
            # 페이지 끝에서 섹션이 분리되지 않도록 체크
            if self.get_y() > 220:
                self.add_page()
            
            # 🎨 섹션 제목 - 진한 파란색 볼드
            self.set_safe_font('bold', 12)
            self.set_text_color(21, 101, 192)
            self.multi_cell(0, 8, title, align='L')
            self.ln(3)
            
            # 🎨 항목들 - 진한 회색
            self.set_safe_font('normal', 9)
            self.set_text_color(60, 60, 60)
            
            for i, item in enumerate(items, 1):
                # 페이지 끝에서 항목이 분리되지 않도록 체크
                if self.get_y() > 260:
                    self.add_page()
                
                # 번호와 함께 표시
                self.cell(8, 5, f"{i}.", ln=0)
                # 나머지 공간에 텍스트 
                self.multi_cell(0, 5, item, align='L')
                
                # 다음 항목과 간격
                if i < len(items):
                    self.ln(2)
            
            # 섹션 끝 간격
            self.ln(6)
            
        except Exception as e:
            print(f"가이드라인 섹션 오류: {e}")
    
    def clean_text(self, text):
        """개선된 텍스트 정리 - 검색 관련 내용 제거"""
        try:
            if not text:
                return ""
            
            text = str(text)
            
            # 🔥 검색 관련 내용 제거 (라인 단위)
            lines = text.split('\n')
            clean_lines = []
            
            for line in lines:
                line_lower = line.lower().strip()
                
                # 검색 관련 키워드가 포함된 라인 제거
                skip_line = any([
                    '키워드 조합' in line,
                    'google scholar' in line_lower,
                    'scholar.google.com' in line_lower,
                    'academic.naver.com' in line_lower,
                    'riss.kr' in line_lower,
                    'dbpia.co.kr' in line_lower,
                    '검색 사이트' in line,
                    'https://' in line_lower and ('scholar' in line_lower or 'academic' in line_lower or 'riss' in line_lower or 'dbpia' in line_lower),
                    line.strip().startswith('키워드 조합'),
                    '이 키워드로 검색하면' in line,
                    '연구들을 찾을 수 있' in line,
                    '네이버 학술정보' in line,
                    'RISS' in line,
                    'DBpia' in line
                ])
                
                if not skip_line and line.strip():
                    clean_lines.append(line)
            
            text = '\n'.join(clean_lines)
            
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

def extract_topic_from_content(content):
    try:
        title_match = re.search(r'# 📘\s*([^\n-]+)', content)
        if title_match:
            topic = title_match.group(1).strip()
            return topic[:50] if len(topic) > 50 else topic
        return "과학 연구 탐색"
    except:
        return "과학 연구 탐색"

def parse_content_enhanced(content):
    """🔥 정교한 파싱 - 검색 부분만 선별 제거"""
    result = {
        'full_topic_explanation': '',  # 🔥 전체 주제 해설 (검색 부분만 제거)
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("🔍 정교한 검색 제거 파싱 로직 사용...")
        print(f"전체 콘텐츠 길이: {len(content)}")
        
        # 🔥 전체 주제 해설 추출 (## 📄 또는 ## 🌐 전까지)
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            print(f"주제 해설 추출 성공: {len(full_explanation)}자")
            
            # 🔥 확장 가능한 탐구 아이디어와 분리
            if '확장 가능한 탐구' in full_explanation:
                ideas_start = full_explanation.find('확장 가능한 탐구')
                
                # 탐구 아이디어 전까지의 내용
                raw_topic_content = full_explanation[:ideas_start].strip()
                
                # 🔥 정교한 검색 내용만 제거 (라인 단위)
                topic_lines = raw_topic_content.split('\n')
                clean_topic_lines = []
                
                for line in topic_lines:
                    # 🔥 매우 구체적인 검색 관련 라인만 제거
                    skip_line = (
                        line.strip().startswith('키워드 조합') or
                        'scholar.google.com' in line.lower() or
                        'academic.naver.com' in line.lower() or
                        'riss.kr' in line.lower() or
                        'dbpia.co.kr' in line.lower() or
                        (line.strip().startswith('검색 사이트') and ':' in line) or
                        ('이 키워드로 검색하면' in line and '연구' in line)
                    )
                    
                    if not skip_line:
                        clean_topic_lines.append(line)
                
                # 🔥 문단 단위에서 검색 전용 문단만 제거
                clean_content = '\n'.join(clean_topic_lines)
                paragraphs = clean_content.split('\n\n')
                final_paragraphs = []
                
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue
                    
                    # 검색 전용 문단만 제거 (더 구체적으로)
                    is_search_paragraph = (
                        ('키워드 조합' in paragraph and 'Google Scholar' in paragraph) or
                        ('scholar.google.com' in paragraph.lower() and 'academic.naver' in paragraph.lower()) or
                        (paragraph.count('https://') >= 3 and 'scholar' in paragraph.lower())
                    )
                    
                    if not is_search_paragraph:
                        final_paragraphs.append(paragraph)
                
                result['full_topic_explanation'] = '\n\n'.join(final_paragraphs)
                print(f"✅ 정교한 검색 제거 후 주제 내용 저장: {len(result['full_topic_explanation'])}자")
                
                # 디버깅: 저장된 내용 미리보기
                preview = result['full_topic_explanation'][:200] + "..." if len(result['full_topic_explanation']) > 200 else result['full_topic_explanation']
                print(f"📝 저장된 내용 미리보기: {preview}")
                
                # 탐구 아이디어 부분
                ideas_section = full_explanation[ideas_start:]
                lines = ideas_section.split('\n')
                clean_lines = []
                
                for line in lines[1:]:  # 첫 줄(제목) 제외
                    line = line.strip()
                    if line and len(line) > 10:
                        clean_lines.append(line)
                
                result['research_ideas'] = '\n'.join(clean_lines)
                print(f"✅ 탐구아이디어 저장: {len(clean_lines)}줄")
            else:
                # 탐구 아이디어가 없으면 전체를 주제 해설로 (최소한의 검색 제거)
                result['full_topic_explanation'] = full_explanation
                print("✅ 탐구 아이디어 없음 - 전체를 주제 해설로 처리")
        else:
            print("❌ 주제 해설을 찾을 수 없음")
        
        # 생성된 논문 파싱 (기존 유지)
        if "생성된 연구 논문" in content:
            paper_section = content[content.find("생성된 연구 논문"):]
            paper_sections = ['초록', '서론', '실험 방법', '예상 결과', '시각자료 제안', '결론', '참고문헌']
            for section in paper_sections:
                pattern = f"### {section}[^\n]*\n(.*?)(?=###|$)"
                match = re.search(pattern, paper_section, re.DOTALL)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 10:
                        result['generated_paper'][section] = content_text
        
        print(f"🎉 정교한 파싱 완료!")
        return result
        
    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return result

def get_highschool_default_content(section, topic):
    """🎓 고등학교 수준 기본 내용 제공"""
    defaults = {
        'abstract': f"본 연구는 {topic}에 대해 체계적인 실험을 통해 과학적 근거를 얻고자 한다. 연구의 목적은 이론적 예상을 실험으로 확인하고, 기존 연구의 부족한 점을 보완하여 새로운 관점을 제시하는 것이다. 실험을 통해 얻은 데이터를 정확하게 분석하여 의미 있는 결론을 도출할 예정이며, 이를 통해 해당 분야의 과학적 이해를 깊게 하고자 한다.",
        
        'introduction': f"현재 {topic} 분야에서는 다양한 연구가 활발히 진행되고 있지만, 여전히 해결되지 않은 중요한 문제들이 남아있다. 기존 연구들을 살펴본 결과, 몇 가지 중요한 문제점들을 발견할 수 있었다. 첫째, 실험 방법이 연구자마다 달라서 결과를 비교하기 어려운 문제가 있다. 둘째, 오랜 기간에 걸친 변화에 대한 연구가 부족하여 전체적인 이해가 제한적이다.",
        
        'methods': f"**필요 재료 및 장비:**\n전자저울, 온도계, pH시험지, 스탠드, 비커(다양한 크기), 스포이드, 메스실린더, 실험용 시약, 스톱워치, 자, 기록지\n\n**1단계: 실험 재료 준비**\n먼저 실험에 필요한 모든 재료의 상태를 확인합니다. 다음으로 각 시약의 농도를 정확히 측정하고 필요한 용액을 만듭니다.\n\n**2단계: 실험 환경 설정**\n먼저 실험실의 온도를 일정하게 유지합니다(약 25℃). 다음으로 실험 장비를 흔들리지 않는 안정한 실험대에 놓습니다.",
        
        'results': f"실험을 통해 다음과 같은 결과를 확인하였다. 첫째, 시간에 따른 주요 변수의 변화 패턴을 분석한 결과 예상했던 이론과 잘 맞는 것을 확인할 수 있었다. 그림 1에서 보면 실험이 진행될수록 측정값이 계속 증가하는 경향을 나타낸다.",
        
        'visuals': f"실험 결과를 효과적으로 보여주기 위해 다음과 같은 시각자료를 만들 예정입니다. **그림 1: 시간-측정값 변화 그래프** **그림 2: 조건별 효율성 비교 차트** **표 1: 실험군 대조군 비교**",
        
        'conclusion': f"본 연구를 통해 처음에 예상했던 내용이 실험으로 확인될 것으로 예상된다. 이는 관련 분야의 이론적 이해를 깊게 하고, 앞으로의 연구 방향을 제시하는 중요한 의미를 갖는다.",
        
        'references': "참고문헌은 자동으로 검색 가이드가 제공됩니다."
    }
    return defaults.get(section, f"{section} 섹션 내용이 생성되지 않았습니다.")

def generate_pdf(content, filename="research_report.pdf"):
    """🎨 웹 내용을 구조화해서 PDF 생성"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        
        # 🔥 단순화된 파싱 로직 사용
        sections = parse_content_enhanced(content)
        
        # 🎨 PDF 생성
        with suppress_fpdf_warnings():
            pdf = ImprovedKoreanPDF(topic)
            
            # 🎨 표지 페이지 (컬러풀하게)
            pdf.add_title_page(topic)
            
            # 내용 페이지
            pdf.add_page()
            
            # 🔥 전체 주제 해설 섹션 (웹 내용을 구조화해서 표시)
            if sections.get('full_topic_explanation'):
                pdf.add_section_title("주제 탐색 결과")
                
                topic_content = sections['full_topic_explanation']
                print(f"✅ 전체 주제 내용 PDF 추가: {len(topic_content)}자")
                
                # 🔥 새로운 포맷팅 메서드 사용
                pdf.add_formatted_content(topic_content)
                
            else:
                pdf.add_section_title("주제 탐색 결과")
                pdf.add_paragraph("주제 해설 내용을 찾을 수 없습니다.")
                print("❌ full_topic_explanation이 없음")
            
            # 🔥 확장 가능한 탐구 아이디어
            if sections.get('research_ideas'):
                pdf.add_section_title("확장 가능한 탐구 아이디어")
                pdf.add_beautiful_research_ideas(sections['research_ideas'])
            
            # 🔥 생성된 논문 (새 페이지에서 시작)
            if sections['generated_paper']:
                selected_idea = "선택된 연구 주제"
                pdf.add_paper_title_page(topic, selected_idea)
                
                section_map = {
                    '초록': ('Abstract', 1),
                    '서론': ('Introduction', 2), 
                    '실험 방법': ('Methods', 3),
                    '예상 결과': ('Expected Results', 4),
                    '시각자료 제안': ('Suggested Visualizations', 5),
                    '결론': ('Conclusion', 6),
                    '참고문헌': ('References', 7)
                }
                
                for section_key, (english_name, num) in section_map.items():
                    if section_key in sections['generated_paper']:
                        title = f"{section_key} ({english_name})"
                        content_text = sections['generated_paper'][section_key]
                        pdf.add_paper_section(title, content_text, num)
                    else:
                        # 🎓 고등학교 수준 기본 내용 사용
                        title = f"{section_key} ({english_name})"
                        section_lower = section_key.lower().replace(' ', '_').replace('시각자료_제안', 'visuals')
                        if section_lower == '실험_방법':
                            section_lower = 'methods'
                        elif section_lower == '예상_결과':
                            section_lower = 'results'
                        
                        default_content = get_highschool_default_content(section_lower, topic)
                        pdf.add_paper_section(title, default_content, num)
            
            # 🆕 논문 작성 가이드라인 페이지 추가
            pdf.add_guidelines_page()
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            with suppress_fpdf_warnings():
                pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ 검색 내용 제거된 PDF 생성 성공: {output_path} ({file_size:,} bytes)")
                return output_path
        
        # 실패시 텍스트 파일
        txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {topic} 연구보고서 ===\n\n")
            f.write(f"생성 시간: {datetime.now()}\n\n")
            f.write(content)
        
        return txt_path
            
    except Exception as e:
        print(f"❌ PDF 생성 오류: {e}")
        return None

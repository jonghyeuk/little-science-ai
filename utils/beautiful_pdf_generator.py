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
    
    def add_paper_item(self, title, summary, source=""):
        """🎨 논문 항목 예쁘게 포맷팅 - 기존 로직 유지"""
        try:
            # 페이지 하단에서 논문 항목이 시작되면 새 페이지로
            if self.get_y() > 240:
                self.add_page()
            
            # 🎨 논문 제목 - 진한 남색 볼드
            self.set_safe_font('bold', 11)
            self.set_text_color(26, 35, 126)  # Indigo
            clean_title = self.clean_text(title)
            
            # 제목 길이 제한 완화
            if len(clean_title) > 300:
                clean_title = clean_title[:297] + "..."
            
            self.multi_cell(0, 7, f"▪ {clean_title}", align='L')
            
            if source:
                # 🎨 출처 - 중간 회색 
                self.set_safe_font('normal', 9)
                self.set_text_color(117, 117, 117)
                self.multi_cell(0, 5, f"   {source}", align='L')
            
            # 🎨 요약 - 진한 회색
            self.set_safe_font('normal', 10)
            self.set_text_color(65, 65, 65)
            clean_summary = self.clean_text(summary)
            
            # 요약 길이 제한 완화
            if len(clean_summary) > 2000:
                # 자연스러운 문장 끝에서 자르기
                sentences = re.split(r'[.!?]\s+', clean_summary)
                kept_text = ""
                for sent in sentences:
                    if len(kept_text + sent) < 1500:
                        kept_text += sent + ". "
                    else:
                        break
                clean_summary = kept_text.rstrip(". ") + "."
            
            if clean_summary:
                # 들여쓰기로 예쁘게
                self.cell(10, 6, '', ln=0)  # 들여쓰기
                self.multi_cell(0, 6, clean_summary, align='L')
            
            self.ln(6)
            
        except Exception as e:
            print(f"논문 항목 오류: {e}")
    
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
    
    def add_research_utilization_guide(self, topic):
        """📖 논문 활용 가이드 - 고등학생을 위한 구체적인 섹션별 가이드"""
        try:
            # 새 페이지 시작
            self.add_page()
            
            # 🎨 메인 제목
            self.ln(8)
            self.set_safe_font('bold', 18)
            self.set_text_color(25, 118, 210)
            self.multi_cell(0, 10, "연구논문 작성 및 활용 완벽 가이드", align='C')
            self.ln(8)
            
            # 🎨 부제목
            self.set_safe_font('normal', 12)
            self.set_text_color(96, 125, 139)
            self.multi_cell(0, 8, "각 섹션별 구체적인 작성법과 활용 전략", align='C')
            self.ln(12)
            
            # === 1. 초록(Abstract) 활용법 ===
            self.add_elegant_subsection("📋 1. 초록(Abstract) - 연구의 얼굴")
            
            abstract_guide = """초록은 여러분 연구의 '예고편'이라고 생각하세요. 심사위원들이 가장 먼저 보는 부분이에요.

【무엇을 써야 할까요?】
• 연구 목적: "이 연구는 왜 중요한가?" → 예) "교통사고 감소를 위해 스마트 신호등 시스템을 개발했다"
• 연구 방법: "어떻게 했는가?" → 예) "아두이노와 센서를 이용해 실시간 제어 시스템 구현"
• 주요 결과: "무엇을 발견했는가?" → 예) "기존 대비 대기시간 25% 단축 효과 확인"
• 연구 의의: "이 결과가 왜 중요한가?" → 예) "실제 교통 체증 해결에 기여할 수 있음"

【실제 작성 팁】
초록은 150-250자 정도로 간결하게! 숫자와 구체적 결과를 포함하면 임팩트가 커져요. "효과가 있었다"보다는 "25% 개선되었다"가 훨씬 좋습니다."""
            
            self.add_paragraph(abstract_guide)
            
            # === 2. 서론(Introduction) 활용법 ===
            self.add_elegant_subsection("📖 2. 서론(Introduction) - 연구의 배경과 필요성")
            
            intro_guide = """서론은 "왜 이 연구를 해야 하는가?"에 대한 설득력 있는 답변이에요.

【구성 순서 (깔때기 모양으로)】
1) 넓은 배경: "현재 사회에서 이런 문제가 있다"
   → 예) "전 세계적으로 교통사고로 연간 135만 명이 사망하고 있다"

2) 구체적 문제: "특히 우리 지역/상황에서는..."
   → 예) "우리 학교 앞 횡단보도에서 지난해 3건의 사고 발생"

3) 기존 연구 현황: "다른 연구자들은 어떤 시도를 했는가?"
   → 예) "김○○(2023)은 고정식 신호등을 연구했으나 실시간 제어의 한계가 있었다"

4) 연구 목적: "그래서 나는 이런 걸 하겠다"
   → 예) "본 연구에서는 AI 기반 적응형 신호등 시스템을 개발하고자 한다"

【참고문헌 활용법】
최소 5-10개의 선행연구를 인용하세요. "○○○(2023)에 따르면..."처럼 구체적으로 인용하면 신뢰도가 높아집니다."""
            
            self.add_paragraph(intro_guide)
            
            # === 3. 실험방법(Methods) 활용법 ===
            self.add_elegant_subsection("🔬 3. 실험방법(Methods) - 재현 가능한 설계")
            
            methods_guide = """다른 사람이 여러분 실험을 똑같이 따라할 수 있도록 자세히 써야 해요.

【필수 포함 내용】
• 실험 재료: 브랜드명까지 구체적으로
   → 나쁜 예) "센서 사용"
   → 좋은 예) "HC-SR04 초음파 센서(DFRobot사)"

• 실험 절차: 단계별로 번호를 매겨서
   → "1단계: 아두이노 보드에 센서 연결 (5V, GND, 디지털핀 2,3번)"
   → "2단계: 코딩 후 업로드 (IDE 버전 1.8.19 사용)"

• 측정 방법: 어떻게, 몇 번, 언제 측정했는지
   → "30초 간격으로 10회 반복 측정, 평균값 사용"

• 변수 통제: 무엇을 같게 유지했는지
   → "실험실 온도 25±2℃, 습도 50±5% 유지"

【꿀팁】
사진이나 회로도를 꼭 포함하세요! "백문이 불여일견"이에요."""
            
            self.add_paragraph(methods_guide)
            
            # === 4. 결과(Results) 활용법 ===
            self.add_elegant_subsection("📊 4. 결과(Results) - 객관적 사실 제시")
            
            results_guide = """결과 섹션은 순수하게 "팩트"만 써야 해요. 해석은 다음 섹션에서!

【효과적인 결과 제시법】
• 표와 그래프 적극 활용
   → "그림 1에서 보듯이 시간이 지날수록 효율이 증가했다"
   → "표 1의 결과, 실험군이 대조군보다 평균 23% 높은 성능을 보였다"

• 구체적 숫자 제시
   → 모호한 표현) "많이 개선되었다"
   → 명확한 표현) "기존 30초에서 22.5초로 25% 단축되었다"

• 오차범위 포함
   → "평균 22.5±1.2초 (n=10, p<0.05)"

【통계 처리 팁】
고등학교 수준에서는 평균, 표준편차, t-검정 정도면 충분해요. 온라인 계산기도 활용하세요!

【그래프 작성 요령】
• X축, Y축 단위 명확히 표시
• 제목은 구체적으로 ("시간에 따른 온도 변화" ×, "LED 발열에 따른 온도 변화" ○)
• 범례와 오차막대 포함"""
            
            self.add_paragraph(results_guide)
            
            # === 5. 고찰/결론(Discussion/Conclusion) 활용법 ===
            self.add_elegant_subsection("🎯 5. 고찰 및 결론 - 의미 도출과 한계 인정")
            
            discussion_guide = """여기서 여러분의 분석력과 통찰력을 보여주세요!

【고찰 구성법】
1) 결과 해석: "왜 이런 결과가 나왔을까?"
   → "온도가 높을수록 반응속도가 빨라진 이유는 분자 운동이 활발해졌기 때문으로 사료된다"

2) 기존 연구와 비교: "다른 연구와 어떻게 다른가?"
   → "이는 Smith(2022)의 연구결과와 일치하나, 온도 범위는 더 넓게 확인되었다"

3) 실용적 의미: "실생활에 어떻게 활용할 수 있는가?"
   → "이 결과를 바탕으로 겨울철 배터리 효율 개선 방안을 제시할 수 있다"

【한계점 솔직하게 인정하기】
• "실험 기간이 2주로 제한되어 장기적 효과는 확인하지 못했다"
• "실험실 환경에서만 진행되어 실제 환경에서의 검증이 필요하다"
• "비용 문제로 샘플 수가 10개로 제한되었다"

→ 한계를 인정하는 것이 오히려 신뢰도를 높여줍니다!"""
            
            self.add_paragraph(discussion_guide)
            
            # === 6. 참고문헌(References) 활용법 ===
            self.add_elegant_subsection("📚 6. 참고문헌 - 신뢰도의 근거")
            
            references_guide = """참고문헌은 여러분 연구의 "든든한 뒷배경"이에요.

【어떤 자료를 인용해야 할까?】
• 학술지 논문 (가장 신뢰도 높음)
• 정부기관 발표자료 (통계청, 과기부 등)
• 대학교수나 전문가의 저서
• 신뢰할 만한 뉴스 기사 (과학 전문지 등)

【피해야 할 자료】
• 위키피디아 (참고용으로만, 직접 인용 금지)
• 개인 블로그
• 출처 불명 자료

【인용 형식 (APA 스타일)】
• 논문: 김철수, 이영희. (2024). 스마트 교통시스템 효과 분석. 교통공학지, 15(3), 45-67.
• 웹사이트: 교통안전공단. (2024). 2023년 교통사고 통계. Retrieved from https://www.kotsa.or.kr

【인용 개수】
고등학교 수준: 5-15개 정도가 적당해요. 너무 많으면 오히려 산만해집니다."""
            
            self.add_paragraph(references_guide)
            
            # === 7. 발표 및 포트폴리오 활용법 ===
            self.add_elegant_subsection("🎤 7. 발표 및 포트폴리오 활용 전략")
            
            presentation_guide = """완성된 논문을 다양한 곳에서 활용해보세요!

【과학 탐구 대회 발표 팁】
• 5분 발표라면: 문제제기(1분) → 방법(1분) → 결과(2분) → 의의(1분)
• 포스터라면: 그래프와 사진을 크게, 텍스트는 최소화
• 질의응답 준비: "왜 이 방법을 선택했나요?" "다른 방법과 비교했나요?" "실용화 가능성은?"

【대학 입시 포트폴리오 활용】
• 세특(세부능력 및 특기사항)에 활용
• 자기소개서에서 "도전정신"과 "탐구능력" 어필
• 면접에서 구체적 사례로 활용

【추가 연구 아이디어】
• 1년 프로젝트로 확장: 시즌별 효과 비교
• 다른 변수 추가: 날씨, 시간대별 분석
• 타 학교와 협력: 지역별 비교 연구

【성공 사례 만들기】
이 논문을 시작으로 관련 분야의 전문가가 되어보세요. 꾸준히 업데이트하고 발전시키면 3년 후에는 정말 멋진 연구자가 되어 있을 거예요!"""
            
            self.add_paragraph(presentation_guide)
            
            # === 마무리 격려 ===
            self.add_elegant_subsection("🎉 마지막 응원 메시지")
            
            final_message = """축하합니다! 여러분은 이제 진짜 '연구자'입니다.

이 논문은 끝이 아니라 시작이에요. 과학자들도 처음에는 여러분처럼 작은 호기심에서 시작했답니다. 실험이 실패해도, 결과가 예상과 달라도 괜찮아요. 그것도 소중한 발견이거든요.

앞으로도 계속 질문하고, 실험하고, 발견하세요. 여러분의 연구가 언젠가는 세상을 바꿀 수도 있어요!

Remember: 모든 위대한 발견은 "어? 이상하네?"라는 호기심에서 시작되었습니다. 🔬✨"""
            
            self.add_paragraph(final_message)
            
        except Exception as e:
            print(f"연구 활용 가이드 오류 (무시하고 계속): {e}")
    
    def clean_text(self, text):
        """개선된 텍스트 정리 - 기존 로직 유지"""
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
    """🔥 기존 파싱 로직 그대로 유지 - 안전함"""
    result = {
        'topic_explanation': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("🔍 기존 파싱 로직 사용...")
        print(f"전체 콘텐츠 길이: {len(content)}")
        
        # 전체 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            result['topic_explanation'] = full_explanation
            print(f"주제 해설 추출 성공: {len(full_explanation)}자")
            
            # 🔥 틈새주제 파싱 (기존 로직)
            if '확장 가능한 탐구' in full_explanation:
                ideas_start = full_explanation.find('확장 가능한 탐구')
                ideas_section = full_explanation[ideas_start:]
                
                # 간단하게 전체를 가져와서 정리
                lines = ideas_section.split('\n')
                clean_lines = []
                
                for line in lines[1:]:  # 첫 줄(제목) 제외
                    line = line.strip()
                    if line and len(line) > 10 and not any(skip in line for skip in ['키워드', 'Scholar', '도메인']):
                        clean_lines.append(line)
                
                result['research_ideas'] = '\n'.join(clean_lines)
                print(f"틈새주제 파싱 완료: {len(clean_lines)}줄")
        
        # 🔥 ISEF 파싱 (기존 로직 그대로)
        isef_papers = []
        if "ISEF" in content:
            isef_section = content[content.find("ISEF"):content.find("arXiv") if "arXiv" in content else len(content)]
            print(f"ISEF 섹션 길이: {len(isef_section)}")
            
            # 여러 패턴 시도
            patterns = [
                r'▪\s*([^\n]+)\n[^\n]*출처[^\n]*\n\s*([^▪]+?)(?=▪|\n\n|$)',
                r'-\s*\*\*([^*]+)\*\*[^\n]*\n([^-]+?)(?=-|\n\n|$)',
                r'([A-Z][^:\n]+):\s*([^▪\n-]+?)(?=▪|-|\n\n|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, isef_section, re.DOTALL)
                for title, summary in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                    if len(clean_title) > 5 and len(clean_summary) > 20:
                        # 요약 길이 관대하게
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
        
        # arXiv 검색 (기존 로직)
        arxiv_papers = []
        if "arXiv" in content:
            arxiv_section = content[content.find("arXiv"):]
            print(f"arXiv 섹션 길이: {len(arxiv_section)}")
            
            patterns = [
                r'▪\s*([^\n]+)\n[^\n]*arXiv[^\n]*\n\s*([^▪]+?)(?=▪|\n\n|$)',
                r'-\s*\*\*([^*]+)\*\*[^\n]*\n([^-]+?)(?=\[링크\]|-|\n\n|$)',
                r'([A-Z][^:\n]+):\s*([^▪\n-]+?)(?=▪|-|\n\n|영문 원본|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, arxiv_section, re.DOTALL)
                for title, summary in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                    
                    if len(clean_title) > 5 and len(clean_summary) > 20:
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
            sections = ['초록', '서론', '실험 방법', '예상 결과', '결론', '참고문헌']
            for section in sections:
                pattern = f"### {section}[^\n]*\n(.*?)(?=###|$)"
                match = re.search(pattern, paper_section, re.DOTALL)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 10:
                        result['generated_paper'][section] = content_text
        
        print(f"🎉 기존 파싱 완료!")
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
    """🎨 안전하게 개선된 PDF 생성 - 기존 파싱 로직 사용"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        
        # 🔥 기존 파싱 로직 사용 (안전함)
        sections = parse_content_enhanced(content)
        
        # 🎨 PDF 생성 (컬러풀하게 개선)
        with suppress_fpdf_warnings():
            pdf = ImprovedKoreanPDF(topic)
            
            # 🎨 표지 페이지 (컬러풀하게)
            pdf.add_title_page(topic)
            
            # 내용 페이지
            pdf.add_page()
            
            # 🎨 주제 개요
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                explanation = sections['topic_explanation']
                
                # 개념 정의 부분
                if '개념' in explanation or '정의' in explanation:
                    concept_part = explanation.split('응용')[0] if '응용' in explanation else explanation[:500]
                    if len(concept_part) > 50:
                        pdf.add_elegant_subsection("개념 정의")
                        pdf.add_paragraph(concept_part)
                
                # 🎨 확장 가능한 탐구 아이디어 (예쁘게 포맷팅)
                if sections.get('research_ideas'):
                    pdf.add_elegant_subsection("확장 가능한 탐구 아이디어")
                    pdf.add_beautiful_research_ideas(sections['research_ideas'])
            
            # 🎨 문헌 조사
            pdf.add_section_title("문헌 조사")
            
            # 🎨 ISEF 연구
            pdf.add_section_title("ISEF 관련 연구", level=2)
            if sections['isef_papers']:
                for title, summary in sections['isef_papers']:
                    pdf.add_paper_item(title, summary, "출처: ISEF 프로젝트")
            else:
                pdf.set_safe_font('normal', 10)
                pdf.set_text_color(158, 158, 158)
                pdf.multi_cell(0, 6, "관련 ISEF 프로젝트를 찾지 못했습니다.", align='L')
                pdf.ln(4)
            
            # 🎨 arXiv 연구
            pdf.add_section_title("arXiv 최신 연구", level=2)
            if sections['arxiv_papers']:
                for title, summary in sections['arxiv_papers']:
                    pdf.add_paper_item(title, summary, "출처: arXiv (프리프린트)")
            else:
                pdf.set_safe_font('normal', 10)
                pdf.set_text_color(158, 158, 158)
                pdf.multi_cell(0, 6, "관련 arXiv 논문을 찾지 못했습니다.", align='L')
                pdf.ln(4)
            
            # 🎨 생성된 논문 (고등학교 수준으로)
            if sections['generated_paper']:
                selected_idea = "선택된 연구 주제"
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
                    else:
                        # 🎓 고등학교 수준 기본 내용 사용
                        title = f"{section_key} ({english_name})"
                        section_lower = section_key.lower().replace(' ', '_')
                        if section_lower == '실험_방법':
                            section_lower = 'methods'
                        elif section_lower == '예상_결과':
                            section_lower = 'results'
                        
                        default_content = get_highschool_default_content(section_lower, topic)
                        pdf.add_paper_section(title, default_content, num)
            
            # 🎨 논문 활용 가이드 추가
            try:
                pdf.add_research_utilization_guide(topic)
                print("✅ 논문 활용 가이드 추가 완료")
            except Exception as e:
                print(f"⚠️ 활용 가이드 추가 실패 (PDF 생성은 계속): {e}")
                # 실패해도 PDF 생성은 계속 진행
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            with suppress_fpdf_warnings():
                pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ 안전한 개선 PDF 생성 성공: {output_path} ({file_size:,} bytes)")
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

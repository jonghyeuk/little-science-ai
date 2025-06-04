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
    
    def add_comprehensive_usage_guide(self, topic):
        """🎓 구체적이고 친절한 활용가이드 - 대폭 개선"""
        try:
            # 새 페이지 시작
            self.add_page()
            
            # 🎨 메인 제목
            self.ln(8)
            self.set_safe_font('bold', 18)
            self.set_text_color(25, 118, 210)  # 파란색
            self.multi_cell(0, 10, "📚 연구보고서 완벽 활용 가이드", align='C')
            self.ln(8)
            
            # 🎨 부제목
            self.set_safe_font('normal', 12)
            self.set_text_color(96, 125, 139)
            self.multi_cell(0, 8, "과학 탐구 대회부터 학교 발표까지 - 단계별 완전정복", align='C')
            self.ln(12)
            
            # === 1단계: 연구 주제 다듬기 ===
            self.add_elegant_subsection("🎯 1단계: 연구 주제를 더 구체적으로 다듬어보세요")
            
            step1_text = f"""지금 생성된 '{topic}' 연구를 바탕으로, 여러분만의 독창적인 관점을 추가해보세요. 예를 들어 "단순히 LED 신호등을 만드는 것"에서 벗어나 "우리 학교 주변 교통 상황을 실제로 조사해서, 그 데이터를 반영한 맞춤형 신호등 시스템 개발"로 확장할 수 있어요.

구체적인 방법:
• 우리 동네나 학교 주변의 실제 문제점 찾기 (예: 횡단보도 대기시간이 너무 길어서 학생들이 무단횡단을 한다든지)
• 설문조사나 관찰일기를 통해 데이터 수집하기
• "만약 내가 교통 엔지니어라면?" 하는 관점으로 접근하기

이렇게 하면 단순한 실험이 아니라 "사회 문제 해결형 연구"가 되어서 훨씬 임팩트가 커집니다."""
            
            self.add_paragraph(step1_text)
            
            # === 2단계: 실험 설계 업그레이드 ===
            self.add_elegant_subsection("🔬 2단계: 실험을 더 과학적으로 설계하기")
            
            step2_text = """이 보고서에 나온 기본 실험에서 한 단계 더 나아가려면 "비교 실험"을 설계해보세요. 

실제 사례로 설명하면:
• 대조군 설정: 기존 고정시간 신호등 vs 우리가 만든 적응형 신호등
• 변수 통제: 같은 시간대, 같은 장소에서 테스트
• 정량적 측정: "그냥 좋아졌다"가 아니라 "대기시간이 평균 23% 단축되었다"처럼 숫자로 표현

과학 탐구 대회에서 높은 점수를 받는 팀들의 공통점이 바로 이런 "정량적 비교 분석"이에요. 심사위원들은 "얼마나 과학적으로 접근했는가"를 가장 중요하게 봅니다."""
            
            self.add_paragraph(step2_text)
            
            # === 3단계: 발표 준비 전략 ===
            self.add_elegant_subsection("🎤 3단계: 발표에서 압도적인 임팩트 만들기")
            
            step3_text = """발표할 때는 "스토리텔링"이 핵심입니다. 기술적인 내용을 나열하는 것보다 청중이 공감할 수 있는 이야기로 포장하세요.

효과적인 발표 구성:
1. 문제 제기 (30초): "여러분도 학교 앞 횡단보도에서 이런 경험 있으시죠?"
2. 해결책 제시 (1분): "그래서 우리가 만든 게 바로 이겁니다!" (실제 작동하는 모델 시연)
3. 실험 결과 (2분): 그래프와 숫자로 효과 입증
4. 의미와 확장성 (30초): "이 기술이 실제로 적용되면 우리 도시가 이렇게 달라집니다"

꿀팁: 발표 중간중간 질문을 던져서 청중의 참여를 유도하세요. "혹시 여러분 중에 신호등 때문에 지각해본 경험 있는 분?" 이런 식으로요."""
            
            self.add_paragraph(step3_text)
            
            # === 4단계: 포트폴리오 작성법 ===
            self.add_elegant_subsection("📝 4단계: 입시에서도 빛나는 포트폴리오 만들기")
            
            step4_text = """이 연구를 대학 입시 포트폴리오에 활용할 때는 "성장 과정"을 강조하세요.

포트폴리오 작성 팁:
• 실패담도 솔직하게: "처음에는 LED가 제대로 안 켜져서 3일 밤을 새웠지만, 그 과정에서 회로 설계의 중요성을 깨달았다"
• 협업 경험 부각: "팀원과 의견이 달라 갈등이 있었지만, 토론을 통해 더 나은 해결책을 찾아냈다"
• 사회적 가치 연결: "단순한 기술 구현을 넘어 교통 약자를 배려하는 마음을 기술로 실현했다"

대학에서는 "완벽한 결과"보다 "과정에서의 학습과 성장"을 더 높이 평가합니다."""
            
            self.add_paragraph(step4_text)
            
            # === 5단계: 심화 연구 방향 ===
            self.add_elegant_subsection("🚀 5단계: 더 깊이 있는 연구로 발전시키기")
            
            step5_text = """이 연구를 기반으로 더 고도화된 프로젝트로 발전시킬 수 있는 방향들:

단기 발전 방향 (1-2개월):
• IoT 센서 추가: 실제 차량 대수를 감지하는 센서 연동
• 데이터 시각화: 웹 대시보드로 실시간 교통 상황 모니터링
• 머신러닝 적용: 과거 데이터를 학습해서 최적의 신호 타이밍 예측

장기 발전 방향 (6개월 이상):
• 스마트시티 연계: 여러 교차로를 네트워크로 연결한 광역 신호 제어
• 환경 요소 고려: 공해 저감을 위한 친환경 신호 알고리즘
• 사회적 약자 배려: 시각장애인을 위한 음성 안내 시스템 추가

이런 식으로 단계적으로 발전시키면, 3년 동안 지속할 수 있는 장기 프로젝트가 됩니다."""
            
            self.add_paragraph(step5_text)
            
            # === 6단계: 실전 경험담 ===
            self.add_elegant_subsection("💡 6단계: 실제 대회 참가 후기와 노하우")
            
            step6_text = """실제로 과학 탐구 대회에서 입상한 선배들의 노하우를 정리해드릴게요:

대회 준비 체크리스트:
✓ 2주 전: 발표 연습 시작 (최소 20번은 반복)
✓ 1주 전: 예상 질문 100개 만들어서 답변 준비
✓ 3일 전: 장비 고장에 대비한 백업 계획 수립
✓ 하루 전: 발표 영상 녹화해서 최종 점검

심사위원들이 자주 하는 질문들:
"이 연구의 사회적 가치는 무엇인가요?"
"실패했을 때는 어떻게 해결했나요?"
"다른 기존 연구와의 차별점은 무엇인가요?"
"실제로 상용화한다면 어떤 문제가 있을까요?"

이런 질문들에 대한 답변을 미리 준비하면 당황하지 않고 자신감 있게 대답할 수 있어요."""
            
            self.add_paragraph(step6_text)
            
            # === 마무리 격려 메시지 ===
            self.add_elegant_subsection("🎉 마지막으로 - 여러분을 응원합니다!")
            
            final_text = """과학 연구는 정답이 정해져 있는 문제 풀이가 아니라 "나만의 해답"을 찾아가는 여행입니다. 이 보고서는 시작점일 뿐이에요. 여러분의 창의적인 아이디어와 끈기 있는 실험 정신이 더해지면 정말 놀라운 결과물이 나올 거라고 확신합니다.

기억하세요:
• 실패는 성공의 어머니 - 실험이 안 되면 "왜 안 될까?"를 고민하는 게 진짜 과학
• 혼자보다는 함께 - 친구들과 토론하고 선생님께 조언을 구하세요
• 완벽보다는 완성 - 100% 완벽한 연구보다 80%라도 끝까지 해내는 게 중요

여러분의 연구가 세상을 조금 더 나은 곳으로 만드는 데 기여하기를 바랍니다. 화이팅! 🚀"""
            
            self.add_paragraph(final_text)
            
        except Exception as e:
            print(f"종합 활용가이드 섹션 오류: {e}")
    
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
    """🔥 원본 파싱 로직 그대로 유지 - 안전함"""
    result = {
        'topic_explanation': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("🔍 원본 파싱 로직 사용...")
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
        
        # 🔥 ISEF 파싱 (원본 그대로)
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
        
        # arXiv 검색 (원본 로직)
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
        
        print(f"🎉 원본 파싱 완료!")
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
    """🎨 원본 기반 최소 수정 PDF 생성"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        
        # 🔥 원본 파싱 로직 사용 (안전함)
        sections = parse_content_enhanced(content)
        
        # 🎨 PDF 생성 (원본 구조 유지)
        with suppress_fpdf_warnings():
            pdf = ImprovedKoreanPDF(topic)
            
            # 🎨 표지 페이지
            pdf.add_title_page(topic)
            
            # 내용 페이지
            pdf.add_page()
            
            # 🔧 수정1: 주제 개요 (최소한 수정)
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                explanation = sections['topic_explanation']
                
                # 🔧 간단한 소제목 구분 (원본보다 약간만 개선)
                # 개념 정의 부분 (원본 유지)
                if '개념' in explanation or '정의' in explanation:
                    concept_part = explanation.split('응용')[0] if '응용' in explanation else explanation[:500]
                    if len(concept_part) > 50:
                        pdf.add_elegant_subsection("📌 개념 정의")
                        pdf.add_paragraph(concept_part)
                
                # 🔧 추가: 작동 원리 (안전하게)
                if '작동' in explanation and '원리' in explanation:
                    try:
                        mechanism_start = explanation.find('작동')
                        mechanism_end = explanation.find('현재') if '현재' in explanation else explanation.find('확장') if '확장' in explanation else len(explanation)
                        mechanism_part = explanation[mechanism_start:mechanism_end]
                        if len(mechanism_part) > 50:
                            pdf.add_elegant_subsection("🔧 작동 원리 및 메커니즘")
                            pdf.add_paragraph(mechanism_part)
                    except:
                        pass  # 오류 시 무시
                
                # 🔧 추가: 현재 배경 (안전하게)
                if '현재' in explanation and ('과학' in explanation or '사회' in explanation or '배경' in explanation):
                    try:
                        background_start = explanation.find('현재')
                        background_end = explanation.find('확장') if '확장' in explanation else len(explanation)
                        background_part = explanation[background_start:background_end]
                        if len(background_part) > 50:
                            pdf.add_elegant_subsection("🌍 현재 과학적·사회적 배경")
                            pdf.add_paragraph(background_part)
                    except:
                        pass  # 오류 시 무시
                
                # 확장 가능한 탐구 아이디어 (원본 유지)
                if sections.get('research_ideas'):
                    pdf.add_elegant_subsection("🎯 확장 가능한 탐구 아이디어")
                    pdf.add_beautiful_research_ideas(sections['research_ideas'])
            
            # 🎨 생성된 논문 (원본 구조 유지)
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
            
            # 🔧 수정3: 종합 활용가이드 추가 (기존 add_simple_usage_guide 대신)
            try:
                pdf.add_comprehensive_usage_guide(topic)
            except Exception as e:
                print(f"활용가이드 추가 실패 (무시): {e}")
                # 실패해도 PDF 생성은 계속 진행
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            with suppress_fpdf_warnings():
                pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ 원본 기반 안전 PDF 생성 성공: {output_path} ({file_size:,} bytes)")
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

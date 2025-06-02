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
        """🔧 수정: 안전한 텍스트 잘림 처리"""
        try:
            self.set_safe_font('bold', 10)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            
            # 🔧 제목 안전하게 자르기
            if len(clean_title) > 150:
                clean_title = self.safe_text_truncate(clean_title, 147) + "..."
            
            self.multi_cell(0, 7, f"▪ {clean_title}", align='L')
            
            if source:
                self.set_safe_font('normal', 8)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 5, f"   {source}", align='L')
            
            self.set_safe_font('normal', 9)
            self.set_text_color(80, 80, 80)
            clean_summary = self.clean_text(summary)
            
            # 🔧 요약 안전하게 자르기 (문장 단위로)
            if len(clean_summary) > 800:
                clean_summary = self.safe_text_truncate(clean_summary, 800)
            
            if clean_summary:
                self.multi_cell(0, 6, f"   {clean_summary}", align='L')
            
            self.ln(4)
            
        except Exception as e:
            print(f"논문 항목 오류: {e}")
    
    def safe_text_truncate(self, text, max_length=500):
        """🔧 새로 추가: 텍스트를 안전하게 자르기 (문장 단위로)"""
        try:
            if len(text) <= max_length:
                return text
            
            # 마지막 완전한 문장 찾기
            truncated = text[:max_length]
            
            # 마지막 문장 구분자 찾기
            sentence_endings = ['.', '!', '?', '다.', '요.', '다!', '요!', '다?', '요?', '습니다.', '입니다.']
            last_sentence_end = -1
            
            for ending in sentence_endings:
                pos = truncated.rfind(ending)
                if pos > last_sentence_end:
                    last_sentence_end = pos
            
            if last_sentence_end > max_length * 0.5:  # 50% 이상에서 문장이 끝나면 사용
                return text[:last_sentence_end + len([e for e in sentence_endings if truncated[last_sentence_end:last_sentence_end+len(e)] == e][0])]
            else:
                # 문장 구분자가 너무 앞에 있으면 마지막 공백까지만
                last_space = truncated.rfind(' ')
                if last_space > max_length * 0.7:
                    return text[:last_space]
                else:
                    return text[:max_length]
                    
        except Exception as e:
            print(f"텍스트 자르기 오류: {e}")
            return text[:max_length] if text else ""
    
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
        """🔧 수정: 덜 공격적인 텍스트 정리"""
        try:
            if not text:
                return ""
            
            text = str(text)
            
            # 기본적인 마크다운 정리 (덜 공격적으로)
            text = re.sub(r'^---\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*---\s*', ' ', text)
            
            # 🔧 URL 제거를 더 신중하게 (논문 링크 보존)
            text = re.sub(r'https?://[^\s\]\)\n]+(?:\s|$)', '', text)
            
            # 🔧 마크다운 제거를 덜 공격적으로
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **굵은글씨** → 굵은글씨
            text = re.sub(r'[`#\[\]<>]', '', text)  # 일부 문자만 제거
            
            # 🔧 이모지 제거를 선택적으로 (중요한 구분자는 보존)
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
            return str(text)[:200] if text else ""  # 더 긴 fallback

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
    keywords = ['응용 사례', '확장 가능한 탐구', '최신논문검색', '개념 정의', 'ISEF', 'arXiv']
    for keyword in keywords:
        exists = keyword in content
        print(f"  '{keyword}': {'✅' if exists else '❌'}")
    
    # 🔧 ISEF/arXiv 섹션 디버깅 강화
    print(f"\n📄 ISEF/arXiv 섹션 분석:")
    if "ISEF" in content:
        isef_start = content.find("ISEF")
        isef_snippet = content[isef_start:isef_start+200]
        print(f"  ISEF 발견: {isef_snippet[:100]}...")
    else:
        print("  ISEF 섹션 없음")
        
    if "arXiv" in content:
        arxiv_start = content.find("arXiv")
        arxiv_snippet = content[arxiv_start:arxiv_start+200]
        print(f"  arXiv 발견: {arxiv_snippet[:100]}...")
    else:
        print("  arXiv 섹션 없음")
    
    print("=" * 60)
    return content

def parse_niche_topics_enhanced(text):
    """🔧 새로 추가: 향상된 틈새주제 파싱"""
    try:
        topics = []
        
        if "확장 가능한 탐구 아이디어" in text:
            section_start = text.find("확장 가능한 탐구 아이디어")
            section_text = text[section_start:]
            
            lines = section_text.split('\n')
            current_topic = ""
            current_description = ""
            
            for line in lines:
                line = line.strip()
                
                # • 로 시작하는 제목 찾기 (하지만 • · 는 제외)
                if line.startswith('•') and not line.startswith('• ·') and len(line) > 2:
                    # 이전 주제가 있다면 저장
                    if current_topic:
                        if current_description:
                            full_topic = f"{current_topic}\n  {current_description}"
                        else:
                            full_topic = current_topic
                        topics.append(full_topic)
                    
                    # 새 주제 시작
                    current_topic = line[1:].strip()  # • 제거
                    current_description = ""
                
                # · 로 시작하는 설명 찾기 (• · 패턴 처리)
                elif line.startswith('• ·') and current_topic and len(line) > 3:
                    current_description = line[3:].strip()  # • · 제거
                elif line.startswith('·') and current_topic and len(line) > 2:
                    current_description = line[1:].strip()  # · 제거
            
            # 마지막 주제 저장
            if current_topic:
                if current_description:
                    full_topic = f"{current_topic}\n  {current_description}"
                else:
                    full_topic = current_topic
                topics.append(full_topic)
        
        return topics if len(topics) >= 3 else [
            "기존 연구의 한계점 개선\n  현재 연구에서 부족한 부분을 찾아 개선방안 제시",
            "실용적 응용 방안 탐구\n  실생활에 적용할 수 있는 구체적 방법 연구", 
            "다른 분야와의 융합 연구\n  타 학문 분야와 연결한 새로운 접근법"
        ]
        
    except Exception as e:
        print(f"틈새주제 파싱 오류: {e}")
        return [
            "기존 연구의 한계점 개선\n  현재 연구에서 부족한 부분을 찾아 개선방안 제시",
            "실용적 응용 방안 탐구\n  실생활에 적용할 수 있는 구체적 방법 연구",
            "다른 분야와의 융합 연구\n  타 학문 분야와 연결한 새로운 접근법"
        ]

def parse_content_enhanced(content):
    """🔧 수정: 향상된 파싱 로직"""
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
            
            # 2. 응용 사례 추출
            if '응용 사례' in full_explanation:
                app_start = full_explanation.find('응용 사례')
                if app_start != -1:
                    app_section = full_explanation[app_start:]
                    end_markers = ['최신논문검색', '확장 가능한 탐구', '키워드 조합']
                    app_end = len(app_section)
                    
                    for marker in end_markers:
                        marker_pos = app_section.find(marker)
                        if marker_pos != -1 and marker_pos < app_end:
                            app_end = marker_pos
                    
                    app_content = app_section[:app_end].strip()
                    app_lines = app_content.split('\n')[1:]
                    result['applications'] = '\n'.join(app_lines).strip()
            
            # 🔧 3. 향상된 틈새주제 파싱
            result['research_ideas'] = '\n'.join(parse_niche_topics_enhanced(full_explanation))
        
        # 🔧 4. ISEF/arXiv 파싱 개선 - 여러 패턴 시도
        print("🔍 ISEF/arXiv 파싱 시작...")
        
        # ISEF 파싱 - 카드 형태 패턴 추가
        if "ISEF" in content or "내부 DB" in content:
            print("  📄 ISEF 섹션 파싱 중...")
            isef_match = re.search(r'## 📄[^\n]*\n(.*?)(?=## 🌐|## 📄 생성|$)', content, re.DOTALL)
            if isef_match:
                isef_section = isef_match.group(1)
                print(f"     ISEF 섹션 길이: {len(isef_section)} 문자")
                
                # 🔧 카드 형태 파싱 패턴 추가
                patterns = [
                    # 카드 형태 패턴 (새로 추가)
                    r'<h3[^>]*>📌\s*([^<]+)</h3>.*?<p>([^<]+)</p>',
                    # 기존 마크다운 패턴
                    r'- \*\*([^*\n]+)\*\*[^\n]*\n([^_\-\n]*)',
                    # ▪ 패턴
                    r'▪ ([^\n]+)\n[^\n]*출처[^\n]*\n([^▪\n]+)',
                    # 제목만 있는 패턴
                    r'([A-Za-z][A-Za-z\s]+Research|[A-Za-z][A-Za-z\s]+Battery|[A-Za-z][A-Za-z\s]+Effect)[^\n]*\n[^\n]*출처[^\n]*\n([^▪\-\n]+)',
                ]
                
                for i, pattern in enumerate(patterns):
                    papers = re.findall(pattern, isef_section)
                    print(f"     패턴 {i+1} 결과: {len(papers)}개")
                    if papers:
                        # 🔧 안전한 텍스트 처리
                        processed_papers = []
                        for title, summary in papers:
                            clean_title = re.sub(r'<[^>]+>', '', title).strip()
                            clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                            if len(clean_title) > 5 and len(clean_summary) > 10:
                                processed_papers.append((clean_title, clean_summary))
                        
                        result['isef_papers'] = processed_papers[:3]
                        print(f"     선택된 ISEF 논문: {len(result['isef_papers'])}개")
                        break
        
        # arXiv 파싱 - 카드 형태 패턴 추가
        if "arXiv" in content:
            print("  🌐 arXiv 섹션 파싱 중...")
            arxiv_match = re.search(r'## 🌐[^\n]*\n(.*?)(?=## 📄 생성|$)', content, re.DOTALL)
            if arxiv_match:
                arxiv_section = arxiv_match.group(1)
                print(f"     arXiv 섹션 길이: {len(arxiv_section)} 문자")
                
                # 🔧 카드 형태 파싱 패턴 추가
                patterns = [
                    # 카드 형태 패턴 (새로 추가)
                    r'<h3[^>]*>🌐\s*([^<]+)</h3>.*?<p>([^<]+)</p>',
                    # 기존 마크다운 패턴
                    r'- \*\*([^*\n]+)\*\*[^\n]*\n(.*?)(?=\[링크\]|$)',
                    # ▪ 패턴
                    r'▪ ([^\n]+)\n[^\n]*arXiv[^\n]*\n([^▪\n]+)',
                ]
                
                for i, pattern in enumerate(patterns):
                    papers = re.findall(pattern, arxiv_section, re.DOTALL)
                    print(f"     패턴 {i+1} 결과: {len(papers)}개")
                    if papers:
                        # 🔧 안전한 텍스트 처리
                        processed_papers = []
                        for title, summary in papers:
                            clean_title = re.sub(r'<[^>]+>', '', title).strip()
                            clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                            if len(clean_title) > 5 and len(clean_summary) > 10:
                                processed_papers.append((clean_title, clean_summary))
                        
                        result['arxiv_papers'] = processed_papers[:3]
                        print(f"     선택된 arXiv 논문: {len(result['arxiv_papers'])}개")
                        break
        
        # 5. 생성된 논문 파싱 (기존 로직 유지)
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
        
        print(f"🔚 파싱 완료 - ISEF: {len(result['isef_papers'])}개, arXiv: {len(result['arxiv_papers'])}개")
        
        return result
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """🔧 수정: 향상된 PDF 생성"""
    try:
        # 디버깅
        content = debug_content_structure(content)
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        print(f"추출된 주제: {topic}")
        
        # 🔧 향상된 파싱 사용
        sections = parse_content_enhanced(content)
        
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
                
                explanation = sections['topic_explanation']
                
                # 개념 정의 부분
                if '개념' in explanation or '정의' in explanation:
                    concept_part = explanation.split('응용')[0] if '응용' in explanation else explanation[:500]
                    if len(concept_part) > 50:
                        pdf.add_elegant_subsection("개념 정의")
                        pdf.add_paragraph(concept_part)
                
                # 응용 사례
                if sections.get('applications'):
                    pdf.add_elegant_subsection("응용 사례 및 활용 분야")
                    pdf.add_paragraph(sections['applications'])
                
                # 🔧 확장 가능한 탐구 아이디어 (향상된 포맷)
                if sections.get('research_ideas'):
                    pdf.add_elegant_subsection("확장 가능한 탐구 아이디어")
                    
                    ideas_text = sections['research_ideas']
                    if ideas_text:
                        idea_lines = ideas_text.split('\n')
                        for line in idea_lines:
                            line = line.strip()
                            if line and len(line) > 5:
                                # 들여쓰기 처리 유지
                                if line.startswith('  '):
                                    pdf.add_paragraph(f"    {line}")
                                else:
                                    pdf.add_paragraph(line)
            
            # 4. 문헌 조사
            pdf.add_section_title("문헌 조사")
            
            # ISEF 연구
            pdf.add_section_title("ISEF 관련 연구", level=2)
            if sections['isef_papers']:
                print(f"📄 PDF에 ISEF 논문 {len(sections['isef_papers'])}개 추가")
                for title, summary in sections['isef_papers']:
                    print(f"   - {title[:50]}... ({len(summary)}자)")
                    pdf.add_paper_item(title, summary, "출처: ISEF 프로젝트")
            else:
                print("📄 ISEF 논문 없음")
                pdf.add_paragraph("관련 ISEF 프로젝트를 찾지 못했습니다.")
            
            # arXiv 연구
            pdf.add_section_title("arXiv 최신 연구", level=2)
            if sections['arxiv_papers']:
                print(f"🌐 PDF에 arXiv 논문 {len(sections['arxiv_papers'])}개 추가")
                for title, summary in sections['arxiv_papers']:
                    print(f"   - {title[:50]}... ({len(summary)}자)")
                    pdf.add_paper_item(title, summary, "출처: arXiv (프리프린트)")
            else:
                print("🌐 arXiv 논문 없음")
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

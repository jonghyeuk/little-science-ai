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

# 강화된 경고 억제
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

class BeautifulKoreanPDF(FPDF):
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
                # 페이지 하단에서 시작하지 않도록
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
    
    def add_smart_paragraph(self, text, max_length_per_page=800):
        """🔧 개선된 문단 추가 - 자연스러운 분할"""
        try:
            # 🎨 일반 텍스트 - 진한 회색
            self.set_safe_font('normal', 10)
            self.set_text_color(55, 55, 55)
            
            clean_text = self.clean_text(text)
            if not clean_text or len(clean_text.strip()) <= 5:
                return
            
            # 페이지 여유 공간 확인
            remaining_space = 270 - self.get_y()  # A4 기준
            
            if len(clean_text) <= max_length_per_page or remaining_space > 100:
                # 한 페이지에 들어갈 수 있으면 그대로 출력
                self.multi_cell(0, 6, clean_text, align='L')
                self.ln(4)
            else:
                # 자연스러운 분할점 찾기
                sentences = re.split(r'([.!?]\s+)', clean_text)
                current_chunk = ""
                
                for i in range(0, len(sentences), 2):
                    if i+1 < len(sentences):
                        sentence = sentences[i] + sentences[i+1]
                    else:
                        sentence = sentences[i]
                    
                    if len(current_chunk + sentence) <= max_length_per_page:
                        current_chunk += sentence
                    else:
                        if current_chunk:
                            self.multi_cell(0, 6, current_chunk.strip(), align='L')
                            self.ln(4)
                            current_chunk = sentence
                        else:
                            self.multi_cell(0, 6, sentence, align='L')
                            self.ln(4)
                
                if current_chunk.strip():
                    self.multi_cell(0, 6, current_chunk.strip(), align='L')
                    self.ln(4)
                
        except Exception as e:
            print(f"스마트 문단 추가 오류: {e}")
    
    def add_beautiful_research_ideas(self, ideas_text):
        """🎨 탐구아이디어 예쁘게 포맷팅"""
        try:
            lines = ideas_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('•'):
                    # 🎨 아이디어 제목 - 보라색 볼드
                    self.set_safe_font('bold', 11)
                    self.set_text_color(123, 31, 162)  # Purple
                    
                    # • 제거하고 제목만 추출
                    title = line[1:].strip()
                    self.multi_cell(0, 7, f"• {title}", align='L')
                    self.ln(2)
                    
                elif line.startswith('  ') or line.startswith('·'):
                    # 🎨 설명 - 진한 회색, 들여쓰기
                    self.set_safe_font('normal', 10)
                    self.set_text_color(70, 70, 70)
                    
                    # 들여쓰기 적용
                    desc = line.replace('·', '').strip()
                    if desc:
                        self.cell(15, 6, '', ln=0)  # 들여쓰기 공간
                        self.multi_cell(0, 6, desc, align='L')
                        self.ln(3)
                else:
                    # 일반 텍스트
                    self.set_safe_font('normal', 10)
                    self.set_text_color(60, 60, 60)
                    self.multi_cell(0, 6, line, align='L')
                    self.ln(2)
            
        except Exception as e:
            print(f"탐구아이디어 포맷팅 오류: {e}")
    
    def add_paper_item(self, title, summary, source=""):
        """🎨 논문 항목 예쁘게 포맷팅"""
        try:
            if self.get_y() > 240:
                self.add_page()
            
            # 🎨 논문 제목 - 진한 남색 볼드
            self.set_safe_font('bold', 11)
            self.set_text_color(26, 35, 126)  # Indigo
            clean_title = self.clean_text(title)
            
            if len(clean_title) > 200:
                clean_title = clean_title[:197] + "..."
            
            self.multi_cell(0, 7, f"▪ {clean_title}", align='L')
            
            if source:
                # 🎨 출처 - 중간 회색 이탤릭 느낌
                self.set_safe_font('normal', 9)
                self.set_text_color(117, 117, 117)
                self.multi_cell(0, 5, f"   {source}", align='L')
            
            # 🎨 요약 - 진한 회색
            self.set_safe_font('normal', 10)
            self.set_text_color(65, 65, 65)
            clean_summary = self.clean_text(summary)
            
            if len(clean_summary) > 1500:
                # 자연스러운 문장 끝에서 자르기
                sentences = re.split(r'[.!?]\s+', clean_summary)
                kept_text = ""
                for sent in sentences:
                    if len(kept_text + sent) < 1200:
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
                    # 자연스러운 문단 분할
                    paragraphs = clean_content.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            self.add_smart_paragraph(para.strip())
            
        except Exception as e:
            print(f"논문 섹션 오류: {e}")
    
    def clean_text(self, text):
        """개선된 텍스트 정리"""
        try:
            if not text:
                return ""
            
            text = str(text)
            
            # 기본적인 마크다운 정리
            text = re.sub(r'^---\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*---\s*', ' ', text)
            
            # URL 제거
            text = re.sub(r'https?://[^\s\]\)\n]+(?:\s|$)', '', text)
            
            # 마크다운 제거
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*\*\s*$', '', text)
            text = re.sub(r'\*\*', '', text)
            text = re.sub(r'[`#\[\]<>]', '', text)
            
            # 이모지 제거
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

def parse_content_super_enhanced(content):
    """🔥 ISEF 파싱 강화 + 모든 문제 해결"""
    result = {
        'topic_explanation': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("🔍 슈퍼 강화된 파싱 로직 시작...")
        print(f"전체 콘텐츠 길이: {len(content)}")
        
        # 전체 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            result['topic_explanation'] = full_explanation
            print(f"주제 해설 추출 성공: {len(full_explanation)}자")
            
            # 탐구아이디어 파싱 개선
            if '확장 가능한 탐구' in full_explanation:
                ideas_start = full_explanation.find('확장 가능한 탐구')
                ideas_section = full_explanation[ideas_start:]
                
                # 더 정교한 파싱
                lines = ideas_section.split('\n')
                formatted_ideas = []
                
                for line in lines:
                    line = line.strip()
                    if not line or '키워드' in line or 'Scholar' in line:
                        continue
                    
                    # • 시작하는 제목 감지
                    if line.startswith('•'):
                        title_part = line[1:].strip()
                        # - 로 설명이 분리된 경우
                        if ' - ' in title_part:
                            parts = title_part.split(' - ', 1)
                            formatted_ideas.append(f"• {parts[0]}")
                            formatted_ideas.append(f"  {parts[1]}")
                        else:
                            formatted_ideas.append(line)
                    elif line.startswith('·'):
                        formatted_ideas.append(f"  {line[1:].strip()}")
                    elif formatted_ideas and not line.startswith(('**', '#')):
                        formatted_ideas.append(f"  {line}")
                
                result['research_ideas'] = '\n'.join(formatted_ideas)
                print(f"탐구아이디어 파싱 완료: {len(formatted_ideas)}줄")
        
        # 🔥 ISEF 파싱 대폭 강화 - 모든 패턴 시도
        isef_papers = []
        if "ISEF" in content or "📄" in content:
            print("🔍 ISEF 섹션 검색 중...")
            
            # ISEF 섹션 범위 설정
            isef_start = content.find("ISEF")
            if isef_start == -1:
                isef_start = content.find("📄")
            
            arxiv_start = content.find("arXiv")
            if arxiv_start == -1:
                arxiv_start = content.find("🌐")
            
            if isef_start != -1:
                if arxiv_start != -1 and arxiv_start > isef_start:
                    isef_section = content[isef_start:arxiv_start]
                else:
                    isef_section = content[isef_start:isef_start+3000]  # 충분한 길이
                
                print(f"ISEF 섹션 길이: {len(isef_section)}")
                print(f"ISEF 섹션 미리보기: {isef_section[:300]}")
                
                # 🔥 여러 패턴 순차적으로 시도
                patterns = [
                    # 패턴 1: 카드 형태 (HTML)
                    r'<div[^>]*>.*?<h3[^>]*>📌\s*([^<]+)</h3>.*?<p[^>]*>([^<]*)</p>.*?<p>([^<]+)</p>.*?</div>',
                    # 패턴 2: ▪ 시작 패턴
                    r'▪\s*([^\n]+)\n[^\n]*(?:📅|🔬|🌎|🏆)[^\n]*\n\s*([^▪]+?)(?=▪|## |$)',
                    # 패턴 3: ** 볼드 패턴
                    r'\*\*([^*]+)\*\*[^\n]*\n([^*]+?)(?=\*\*|## |$)',
                    # 패턴 4: 📌 패턴
                    r'📌\s*([^\n]+)\n([^📌]+?)(?=📌|## |$)',
                    # 패턴 5: - ** 패턴
                    r'-\s*\*\*([^*]+)\*\*[^\n]*\n([^-]+?)(?=-\s*\*\*|## |$)',
                    # 패턴 6: 일반 제목: 패턴
                    r'([A-Z][^:\n]{10,100}):\s*([^▪\n-]{50,}?)(?=\n[A-Z]|▪|-|## |$)'
                ]
                
                for i, pattern in enumerate(patterns):
                    print(f"패턴 {i+1} 시도 중...")
                    matches = re.findall(pattern, isef_section, re.DOTALL | re.IGNORECASE)
                    
                    for match in matches:
                        if len(match) >= 2:
                            title = re.sub(r'<[^>]+>', '', match[0]).strip()
                            summary = re.sub(r'<[^>]+>', '', match[1]).strip()
                            
                            # 품질 필터링
                            if (len(title) > 10 and len(summary) > 30 and 
                                not any(skip in title.lower() for skip in ['cookie', 'error', 'loading']) and
                                not any(skip in summary.lower() for skip in ['cookie', 'error', 'loading'])):
                                
                                # 요약 정리
                                summary = re.sub(r'\s+', ' ', summary)
                                if len(summary) > 800:
                                    sentences = re.split(r'[.!?]\s+', summary)
                                    kept = []
                                    total_len = 0
                                    for sent in sentences:
                                        if total_len + len(sent) < 600:
                                            kept.append(sent)
                                            total_len += len(sent)
                                        else:
                                            break
                                    summary = '. '.join(kept) + '.'
                                
                                isef_papers.append((title, summary))
                                print(f"  → ISEF 논문 발견: {title[:50]}...")
                                
                                if len(isef_papers) >= 5:  # 더 많이 수집
                                    break
                    
                    if isef_papers:
                        print(f"패턴 {i+1}에서 {len(isef_papers)}개 발견, 파싱 완료")
                        break
                
                if not isef_papers:
                    # 🔥 최후의 수단: 모든 텍스트에서 논문 같은 패턴 찾기
                    print("최후의 수단: 전체 텍스트에서 논문 패턴 검색...")
                    lines = isef_section.split('\n')
                    current_title = ""
                    current_summary = ""
                    
                    for line in lines:
                        line = line.strip()
                        if len(line) > 20 and any(keyword in line.lower() for keyword in ['연구', '분석', '개발', '효과', '실험', '측정']):
                            if current_title and current_summary and len(current_summary) > 50:
                                isef_papers.append((current_title, current_summary))
                                if len(isef_papers) >= 3:
                                    break
                            current_title = line[:100]
                            current_summary = ""
                        elif current_title and len(line) > 10:
                            current_summary += line + " "
                    
                    # 마지막 논문 처리
                    if current_title and current_summary and len(current_summary) > 50:
                        isef_papers.append((current_title, current_summary))
        
        result['isef_papers'] = isef_papers
        print(f"최종 ISEF 논문 파싱: {len(isef_papers)}개")
        
        # arXiv 파싱 (기존 로직 유지하되 개선)
        arxiv_papers = []
        if "arXiv" in content or "🌐" in content:
            arxiv_section = content[content.find("arXiv") if "arXiv" in content else content.find("🌐"):]
            
            patterns = [
                r'🌐\s*([^\n]+)\n[^\n]*arXiv[^\n]*\n\s*([^🌐]+?)(?=🌐|## |$)',
                r'▪\s*([^\n]+)\n[^\n]*arXiv[^\n]*\n\s*([^▪]+?)(?=▪|## |$)',
                r'\*\*([^*]+)\*\*[^\n]*\n([^*]+?)(?=\*\*|## |$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, arxiv_section, re.DOTALL)
                for title, summary in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                    
                    if len(clean_title) > 5 and len(clean_summary) > 20:
                        if len(clean_summary) > 600:
                            sentences = re.split(r'[.!?]\s+', clean_summary)
                            kept = []
                            total_len = 0
                            for sent in sentences:
                                if total_len + len(sent) < 500:
                                    kept.append(sent)
                                    total_len += len(sent)
                                else:
                                    break
                            clean_summary = '. '.join(kept) + '.'
                        
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
        
        print(f"🎉 슈퍼 강화된 파싱 완료!")
        return result
        
    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return result

def get_highschool_default_content(section, topic):
    """🎓 고등학교 수준 기본 내용 제공"""
    defaults = {
        'abstract': f"본 연구는 {topic}에 대해 체계적인 실험을 통해 과학적 근거를 얻고자 한다. 연구의 목적은 이론적 예상을 실험으로 확인하고, 기존 연구의 부족한 점을 보완하여 새로운 관점을 제시하는 것이다. 실험을 통해 얻은 데이터를 정확하게 분석하여 의미 있는 결론을 도출할 예정이며, 이를 통해 해당 분야의 과학적 이해를 깊게 하고자 한다. 본 연구 결과는 관련 분야의 기초 지식을 강화하고 향후 연구의 방향을 제시하는 데 중요한 도움이 될 것으로 기대된다.",
        
        'introduction': f"현재 {topic} 분야에서는 다양한 연구가 활발히 진행되고 있지만, 여전히 해결되지 않은 중요한 문제들이 남아있다. 기존 연구들을 살펴본 결과, 몇 가지 중요한 문제점들을 발견할 수 있었다. 첫째, 실험 방법이 연구자마다 달라서 결과를 비교하기 어려운 문제가 있다. 둘째, 오랜 기간에 걸친 변화에 대한 연구가 부족하여 전체적인 이해가 제한적이다. 이러한 문제점들을 해결하기 위해서는 더 정확한 실험 설계와 체계적인 접근이 필요하다. 따라서 본 연구에서는 기존 연구들의 문제점을 보완하고 새로운 실험 방법을 사용하여 더욱 정확하고 믿을 수 있는 결과를 얻고자 한다.",
        
        'methods': f"**필요 재료 및 장비:**\n전자저울, 온도계, pH시험지, 스탠드, 비커(다양한 크기), 스포이드, 메스실린더, 실험용 시약, 스톱워치, 자, 기록지\n\n**1단계: 실험 재료 준비 및 확인**\n먼저 실험에 필요한 모든 재료의 상태를 확인합니다. 다음으로 각 시약의 농도를 정확히 측정하고 필요한 용액을 만듭니다. 실험 장비는 사용 전에 정확한지 확인하여 측정 오차를 줄입니다.\n\n**2단계: 실험 환경 설정**\n먼저 실험실의 온도를 일정하게 유지합니다(약 25℃). 다음으로 실험 장비를 흔들리지 않는 안정한 실험대에 놓습니다.\n\n**3단계: 본 실험 진행**\n마지막으로 정해진 조건에서 본 실험을 차례대로 진행합니다. 각 단계마다 정확한 시간과 측정값을 기록합니다.",
        
        'results': f"실험을 통해 다음과 같은 결과를 확인하였다. 첫째, 시간에 따른 주요 변수의 변화 패턴을 분석한 결과 예상했던 이론과 잘 맞는 것을 확인할 수 있었다. 그림 1에서 보면 실험이 진행될수록 측정값이 계속 증가하는 경향을 나타내며, 특히 처음에는 빠른 변화를 보이다가 나중에는 안정화되는 특성을 확인할 수 있다. 둘째, 여러 조건에서의 비교 실험 결과 가장 좋은 조건을 찾을 수 있었다. 이러한 결과들은 기존 이론의 타당성을 실험으로 확인함과 동시에 실생활 적용 가능성을 보여준다.",
        
        'visuals': f"실험 결과를 효과적으로 보여주기 위해 다음과 같은 시각자료를 만들 예정입니다. **그림 1: 시간-측정값 변화 그래프** - X축: 시간(분), Y축: 측정값, 실험 진행에 따른 변화 패턴을 명확히 표현. **그림 2: 조건별 효율성 비교 차트** - 막대그래프 형태로 각 조건에서의 성능을 비교. **표 1: 실험군 대조군 비교** - 각 그룹별 평균값과 표준편차를 포함한 정리표.",
        
        'conclusion': f"본 연구를 통해 처음에 예상했던 내용이 실험으로 확인될 것으로 예상된다. 이는 관련 분야의 이론적 이해를 깊게 하고, 앞으로의 연구 방향을 제시하는 중요한 의미를 갖는다. 실험 결과는 기존 이론이 맞다는 것을 보여줌과 동시에 새로운 활용 가능성을 제시한다. 본 연구 결과는 관련 분야의 학문적 발전과 실생활 활용 모두에 도움이 될 것으로 기대된다."
    }
    return defaults.get(section, f"{section} 섹션 내용이 생성되지 않았습니다.")

def add_professional_references(pdf):
    """전문적인 참고문헌 가이드"""
    try:
        # 🎨 안내 텍스트 - 진한 회색
        pdf.set_safe_font('normal', 10)
        pdf.set_text_color(70, 70, 70)
        guide_text = "실제 연구 수행 시, 주요 학술검색 사이트를 활용하여 관련 논문들을 찾아 참고문헌에 추가하시기 바랍니다."
        pdf.multi_cell(0, 6, guide_text, align='L')
        pdf.ln(6)
        
        # 🎨 양식 제목 - 진한 파란색 볼드
        pdf.set_safe_font('bold', 11)
        pdf.set_text_color(13, 71, 161)
        pdf.multi_cell(0, 7, "참고문헌 작성 양식 (APA Style):", align='L')
        pdf.ln(3)
        
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
                pdf.ln(2)
            elif is_header:
                # 🎨 헤더 - 초록색 볼드
                pdf.set_safe_font('bold', 10)
                pdf.set_text_color(76, 175, 80)
                pdf.multi_cell(0, 6, text, align='L')
                pdf.ln(2)
            else:
                # 🎨 예시 - 일반 회색
                pdf.set_safe_font('normal', 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 5, text, align='L')
                pdf.ln(1)
        
    except Exception as e:
        print(f"참고문헌 가이드 오류: {e}")

def generate_pdf(content, filename="research_report.pdf"):
    """🎨 완전히 개선된 PDF 생성"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        
        # 슈퍼 강화된 파싱 사용
        sections = parse_content_super_enhanced(content)
        
        # 🎨 아름다운 PDF 생성
        with suppress_fpdf_warnings():
            pdf = BeautifulKoreanPDF(topic)
            
            # 🎨 표지 페이지 (컬러풀하게)
            pdf.add_title_page(topic)
            
            # 내용 페이지
            pdf.add_page()
            
            # 🎨 주제 개요
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                explanation = sections['topic_explanation']
                
                # 개념 정의 부분 (자연스러운 분할)
                if '개념' in explanation or '정의' in explanation:
                    concept_end = min([
                        explanation.find('응용') if '응용' in explanation else len(explanation),
                        explanation.find('확장') if '확장' in explanation else len(explanation),
                        800  # 최대 길이
                    ])
                    concept_part = explanation[:concept_end]
                    
                    if len(concept_part) > 50:
                        pdf.add_elegant_subsection("개념 정의")
                        pdf.add_smart_paragraph(concept_part)
                
                # 🎨 확장 가능한 탐구 아이디어 (예쁘게 포맷팅)
                if sections.get('research_ideas'):
                    pdf.add_elegant_subsection("확장 가능한 탐구 아이디어")
                    pdf.add_beautiful_research_ideas(sections['research_ideas'])
            
            # 🎨 문헌 조사
            pdf.add_section_title("문헌 조사")
            
            # 🎨 ISEF 연구 (강화된 파싱 결과)
            pdf.add_section_title("ISEF 관련 연구", level=2)
            if sections['isef_papers']:
                for title, summary in sections['isef_papers']:
                    pdf.add_paper_item(title, summary, "출처: ISEF 프로젝트")
            else:
                # 🎨 안내 메시지도 예쁘게
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
                
                # 논문 제목 페이지
                pdf.add_page()
                pdf.ln(20)
                
                # 🎨 논문 제목 - 진한 파란색 대형 볼드
                pdf.set_safe_font('bold', 18)
                pdf.set_text_color(25, 118, 210)
                paper_title = f"{topic}: 연구 계획서"
                pdf.multi_cell(0, 12, paper_title, align='C')
                pdf.ln(15)
                
                # 🎨 구분선
                pdf.set_draw_color(200, 200, 200)
                pdf.line(30, pdf.get_y(), 180, pdf.get_y())
                pdf.ln(8)
                
                # 논문 섹션들
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
                        
                        if section_key == '참고문헌':
                            pdf.ln(8)
                            pdf.set_safe_font('bold', 13)
                            pdf.set_text_color(0, 105, 92)
                            pdf.multi_cell(0, 8, f"{num}. {title}", align='L')
                            pdf.ln(4)
                            add_professional_references(pdf)
                        else:
                            pdf.add_paper_section(title, content_text, num)
                    else:
                        # 🎓 고등학교 수준 기본 내용 사용
                        title = f"{section_key} ({english_name})"
                        default_content = get_highschool_default_content(section_key.lower(), topic)
                        
                        if section_key == '참고문헌':
                            pdf.ln(8)
                            pdf.set_safe_font('bold', 13)
                            pdf.set_text_color(0, 105, 92)
                            pdf.multi_cell(0, 8, f"{num}. {title}", align='L')
                            pdf.ln(4)
                            add_professional_references(pdf)
                        else:
                            pdf.add_paper_section(title, default_content, num)
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            with suppress_fpdf_warnings():
                pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ 아름다운 PDF 생성 성공: {output_path} ({file_size:,} bytes)")
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

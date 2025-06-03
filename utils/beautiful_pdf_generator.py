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
                # 메인 섹션은 페이지 하단에서 시작하지 않도록
                if self.get_y() > 230:
                    self.add_page()
                
                self.section_number += 1
                self.subsection_number = 0
                title_text = f"{self.section_number}. {clean_title}"
                
                self.ln(10)
                self.set_safe_font('bold', 14)
                self.set_text_color(30, 30, 30)
                
            elif level == 2:
                # 서브섹션도 페이지 하단에서 시작하지 않도록
                if self.get_y() > 240:
                    self.add_page()
                
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
            # 페이지 끝에서 소제목이 혼자 남지 않도록 체크
            if self.get_y() > 250:
                self.add_page()
            
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
    
    def safe_text_truncate(self, text, max_length=500):
        """텍스트 자르기를 최대한 방지 - 거의 자르지 않음"""
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
    
    def add_paper_item(self, title, summary, source=""):
        """텍스트 잘림 대폭 완화 - 거의 제한 없이"""
        try:
            # 페이지 하단에서 논문 항목이 시작되면 새 페이지로
            if self.get_y() > 240:
                self.add_page()
            
            self.set_safe_font('bold', 10)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            
            # 제목 길이 제한 대폭 완화: 200 → 300
            if len(clean_title) > 300:
                clean_title = self.safe_text_truncate(clean_title, 300) + "..."
            
            self.multi_cell(0, 7, f"▪ {clean_title}", align='L')
            
            if source:
                self.set_safe_font('normal', 8)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 5, f"   {source}", align='L')
            
            self.set_safe_font('normal', 9)
            self.set_text_color(80, 80, 80)
            clean_summary = self.clean_text(summary)
            
            # 요약 길이 제한 거의 제거: 1500 → 3000
            if len(clean_summary) > 3000:
                clean_summary = self.safe_text_truncate(clean_summary, 3000)
            
            if clean_summary:
                # 긴 텍스트를 여러 페이지에 걸쳐 표시
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
            guide_text = "실제 연구 수행 시, 주요 학술검색 사이트를 활용하여 관련 논문들을 찾아 참고문헌에 추가하시기 바랍니다."
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
                "【온라인 자료】",
                "국가과학기술정보센터. (2024). 플라즈마 기술 동향 보고서.",
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
            
        except Exception as e:
            print(f"참고문헌 가이드 오류: {e}")
    
    def clean_text(self, text):
        """덜 공격적인 텍스트 정리"""
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
    """🔥 완전히 새로운 파싱 로직 - 문제 해결"""
    result = {
        'topic_explanation': '',
        'applications': '',
        'research_ideas': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("🔍 새로운 파싱 로직 시작...")
        print(f"전체 콘텐츠 길이: {len(content)}")
        
        # 전체 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            full_explanation = explanation_match.group(1).strip()
            result['topic_explanation'] = full_explanation
            print(f"주제 해설 추출 성공: {len(full_explanation)}자")
            
            # 🔥 틈새주제 완전히 새로운 파싱
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
                r'([A-Z][^:\n]+):\s*([^▪\n-]+?)(?=▪|-|\n\n|$)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, isef_section, re.DOTALL)
                for title, summary in matches:
                    clean_title = re.sub(r'<[^>]+>', '', title).strip()
                    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
                    if len(clean_title) > 5 and len(clean_summary) > 20:
                        # 🔥 요약 길이 확장 - 최대한 보존
                        if len(clean_summary) > 500:
                            # 문장 단위로 자르되 매우 관대하게
                            sentences = re.split(r'[.!?]\s+', clean_summary)
                            kept_sentences = []
                            total_len = 0
                            for sent in sentences:
                                if total_len + len(sent) < 800:  # 800자까지 허용
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
                r'([A-Z][^:\n]+):\s*([^▪\n-]+?)(?=▪|-|\n\n|영문 원본|$)'
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
                        # 🔥 요약 길이 확장
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
        
        print(f"🔚 파싱 완료!")
        return result
        
    except Exception as e:
        print(f"❌ 파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """향상된 PDF 생성"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        
        # 향상된 파싱 사용
        sections = parse_content_enhanced(content)
        
        # PDF 생성
        with suppress_fpdf_warnings():
            pdf = ProfessionalKoreanPDF(topic)
            
            # 표지 페이지
            pdf.add_title_page(topic)
            
            # 내용 페이지
            pdf.add_page()
            
            # 주제 개요
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
                
                # 확장 가능한 탐구 아이디어
                if sections.get('research_ideas'):
                    pdf.add_elegant_subsection("확장 가능한 탐구 아이디어")
                    pdf.add_paragraph(sections['research_ideas'])
            
            # 문헌 조사
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
            
            # 생성된 논문
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
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            with suppress_fpdf_warnings():
                pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ PDF 생성 성공: {output_path} ({file_size:,} bytes)")
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

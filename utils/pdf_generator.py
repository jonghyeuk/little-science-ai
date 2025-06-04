from fpdf import FPDF
import os
import re
import warnings
from datetime import datetime
import contextlib

# 경고 억제
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")
warnings.filterwarnings("ignore")

@contextlib.contextmanager
def suppress_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield

# 설정
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
OUTPUT_DIR = "outputs"

class SafeSciencePDF(FPDF):
    def __init__(self, topic="과학 연구"):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.topic = self.clean_text_minimal(topic)
        self.setup_fonts()
        
    def setup_fonts(self):
        """폰트 설정 - 더 안전하게"""
        self.korean_available = False
        try:
            with suppress_warnings():
                if os.path.exists(FONT_REGULAR):
                    self.add_font('Korean', '', FONT_REGULAR, uni=True)
                    self.korean_available = True
                    print("✅ 한글 폰트 로드 성공")
                if os.path.exists(FONT_BOLD) and self.korean_available:
                    self.add_font('KoreanBold', '', FONT_BOLD, uni=True)
                    print("✅ 한글 Bold 폰트 로드 성공")
        except Exception as e:
            print(f"⚠️ 한글 폰트 로드 실패, Arial 사용: {e}")
            self.korean_available = False
            
    def set_font_safe(self, weight='normal', size=10):
        """안전한 폰트 설정"""
        try:
            if self.korean_available:
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
            print(f"폰트 설정 오류: {e}")
            # 최후의 수단
            self.set_font('Arial', '', size)
    
    def header(self):
        if self.page_no() > 1:
            try:
                self.set_font_safe('normal', 8)
                self.set_text_color(150, 150, 150)
                header_text = f'{self.topic} - 연구탐색보고서'
                if len(header_text) > 40:
                    header_text = header_text[:37] + "..."
                self.cell(0, 8, header_text, align='R', ln=True)
                self.ln(2)
            except:
                pass
            
    def footer(self):
        try:
            self.set_y(-15)
            self.set_font_safe('normal', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def clean_text_minimal(self, text):
        """최소한의 텍스트 정리"""
        if not text:
            return ""
        
        text = str(text)
        
        # 기본적인 정리만
        text = re.sub(r'#{1,6}\s*', '', text)  # 마크다운 헤더 제거
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **볼드** 제거
        text = re.sub(r'[`]', '', text)  # 백틱 제거
        text = re.sub(r'https?://[^\s\)]+', '', text)  # URL 제거
        
        # 이모지는 일부만 제거
        common_emojis = r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅🔍❗🚀✅📌🎉🔧🛠️🧬]'
        text = re.sub(common_emojis, '', text)
        
        # 공백 정리
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def add_cover_page(self):
        """안전한 표지 페이지"""
        self.add_page()
        
        try:
            # 상단 공간
            self.ln(25)
            
            # 메인 제목
            self.set_font_safe('bold', 22)
            self.set_text_color(30, 30, 30)
            self.multi_cell(0, 15, self.topic, align='C')
            self.ln(8)
            
            # 부제목
            self.set_font_safe('normal', 16)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 10, '과학 연구 탐색 보고서', align='C')
            
            # 구분선 (rect 대신 line 사용)
            self.ln(15)
            self.set_draw_color(100, 100, 100)
            current_y = self.get_y()
            self.line(50, current_y, 160, current_y)
            self.ln(15)
            
            # 설명
            self.set_font_safe('normal', 11)
            self.set_text_color(100, 100, 100)
            description = "본 보고서는 AI를 활용하여 과학 연구 주제를 탐색하고,\n관련 문헌을 조사하며, 연구 계획을 수립한 결과입니다."
            self.multi_cell(0, 8, description, align='C')
            
            # 하단 정보
            self.ln(30)
            self.set_font_safe('normal', 10)
            self.set_text_color(120, 120, 120)
            today = datetime.now().strftime("%Y년 %m월 %d일")
            self.multi_cell(0, 6, f'생성일: {today}', align='C')
            self.ln(2)
            self.multi_cell(0, 6, 'LittleScienceAI', align='C')
            
        except Exception as e:
            print(f"표지 페이지 오류: {e}")
    
    def add_section_header(self, title, level=1):
        """안전한 섹션 헤더"""
        try:
            # 페이지 하단에서 시작하지 않도록
            if self.get_y() > 240:
                self.add_page()
            
            self.ln(8)
            
            if level == 1:
                self.set_font_safe('bold', 16)
                self.set_text_color(40, 40, 40)
                # 간단한 라인 (rect 대신)
                self.set_draw_color(70, 130, 180)
                current_y = self.get_y() - 2
                self.line(20, current_y, 190, current_y)
                self.ln(2)
            else:
                self.set_font_safe('bold', 13)
                self.set_text_color(60, 60, 60)
            
            self.multi_cell(0, 10, title, align='L')
            self.ln(4)
            
        except Exception as e:
            print(f"섹션 헤더 오류: {e}")
    
    def add_content_block(self, content, preserve_length=True):
        """안전한 내용 블록"""
        if not content:
            return
            
        try:
            self.set_font_safe('normal', 10)
            self.set_text_color(70, 70, 70)
            
            cleaned_content = self.clean_text_minimal(content)
            
            # 텍스트 길이 조정
            if preserve_length and len(cleaned_content) > 2000:
                # 문단 단위로 자연스럽게 줄이기
                paragraphs = cleaned_content.split('\n\n')
                kept_paragraphs = []
                total_length = 0
                
                for para in paragraphs:
                    if total_length + len(para) < 1800:
                        kept_paragraphs.append(para)
                        total_length += len(para)
                    else:
                        # 마지막 문장까지 완전히 포함
                        sentences = para.split('. ')
                        for sent in sentences:
                            if total_length + len(sent) < 1900:
                                kept_paragraphs.append(sent + '.')
                                total_length += len(sent)
                            else:
                                break
                        break
                
                cleaned_content = '\n\n'.join(kept_paragraphs)
            
            # 자연스러운 줄바꿈으로 출력
            paragraphs = cleaned_content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    self.multi_cell(0, 6, para.strip(), align='L')
                    self.ln(3)
                    
        except Exception as e:
            print(f"내용 블록 오류: {e}")
    
    def add_paper_card_safe(self, title, summary, source=""):
        """안전한 논문 카드 - rect 제거"""
        try:
            # 페이지 끝에서 카드가 시작되지 않도록
            if self.get_y() > 230:
                self.add_page()
            
            # rect 대신 간단한 들여쓰기와 색상으로 구분
            self.ln(3)
            
            # 제목
            self.set_font_safe('bold', 10)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text_minimal(title)
            if len(clean_title) > 80:
                clean_title = clean_title[:77] + "..."
            
            # 들여쓰기 효과
            self.cell(5, 6, '', ln=0)  # 여백
            self.multi_cell(0, 6, f"▪ {clean_title}", align='L')
            
            # 출처
            if source:
                self.cell(8, 5, '', ln=0)  # 들여쓰기
                self.set_font_safe('normal', 8)
                self.set_text_color(120, 120, 120)
                self.multi_cell(0, 5, source, align='L')
            
            # 요약
            self.cell(8, 5, '', ln=0)  # 들여쓰기
            self.set_font_safe('normal', 9)
            self.set_text_color(80, 80, 80)
            clean_summary = self.clean_text_minimal(summary)
            
            # 요약 길이 조정
            if len(clean_summary) > 300:
                sentences = clean_summary.split('. ')
                kept_sentences = []
                total_len = 0
                for sent in sentences:
                    if total_len + len(sent) < 280:
                        kept_sentences.append(sent)
                        total_len += len(sent)
                    else:
                        break
                clean_summary = '. '.join(kept_sentences)
                if not clean_summary.endswith('.'):
                    clean_summary += '.'
            
            self.multi_cell(0, 5, clean_summary, align='L')
            self.ln(6)
            
        except Exception as e:
            print(f"논문 카드 오류: {e}")
    
    def add_research_section_safe(self, title, content):
        """안전한 연구 섹션"""
        try:
            self.ln(5)
            
            # 섹션 제목
            self.set_font_safe('bold', 12)
            self.set_text_color(50, 50, 50)
            self.multi_cell(0, 8, title, align='L')
            self.ln(2)
            
            # 내용
            self.set_font_safe('normal', 10)
            self.set_text_color(70, 70, 70)
            cleaned_content = self.clean_text_minimal(content)
            
            # 연구 계획은 더 자세히 보존
            if len(cleaned_content) > 1500:
                paragraphs = cleaned_content.split('\n')
                kept_paragraphs = []
                total_length = 0
                
                for para in paragraphs:
                    if total_length + len(para) < 1400:
                        kept_paragraphs.append(para)
                        total_length += len(para)
                    else:
                        break
                
                cleaned_content = '\n'.join(kept_paragraphs)
            
            self.multi_cell(0, 6, cleaned_content, align='L')
            self.ln(4)
            
        except Exception as e:
            print(f"연구 섹션 오류: {e}")

def extract_topic_from_content(content):
    """내용에서 주제 추출 - 더 안전하게"""
    try:
        patterns = [
            r'# 📘\s*([^\n-]+?)(?:\s*-|$)',
            r'title["\']:\s*["\']([^"\']+)["\']',
            r'주제[:\s]*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                topic = re.sub(r'주제\s*해설', '', topic).strip()
                if len(topic) > 3:
                    return topic[:60] if len(topic) > 60 else topic
        
        return "과학 연구 탐색"
    except Exception as e:
        print(f"주제 추출 오류: {e}")
        return "과학 연구 탐색"

def extract_structured_data_safe(content):
    """안전한 구조화된 데이터 추출"""
    result = {
        'topic_explanation': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        # 주제 해설 추출
        explanation_match = re.search(r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)', content, re.DOTALL)
        if explanation_match:
            result['topic_explanation'] = explanation_match.group(1).strip()
        
        # ISEF 논문 추출 - 더 관대하게
        if "ISEF" in content:
            # 단순한 패턴으로 추출
            isef_matches = re.findall(r'📌\s*([^\n]+)', content)
            for i, title in enumerate(isef_matches[:3]):
                result['isef_papers'].append((title.strip(), "ISEF 관련 연구 프로젝트입니다."))
        
        # arXiv 논문 추출 - 더 관대하게
        if "arXiv" in content:
            arxiv_matches = re.findall(r'🌐\s*([^\n]+)', content)
            for i, title in enumerate(arxiv_matches[:3]):
                result['arxiv_papers'].append((title.strip(), "arXiv 관련 연구 논문입니다."))
        
        # 생성된 논문 추출
        if "생성된 연구 논문" in content or "생성된 연구계획서" in content:
            paper_section = content[content.find("생성된 연구"):]
            
            sections = ['초록', '서론', '실험 방법', '예상 결과', '결론', '참고문헌']
            for section_name in sections:
                pattern = f"### {section_name}[^\n]*\n(.*?)(?=###|$)"
                match = re.search(pattern, paper_section, re.DOTALL | re.IGNORECASE)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 20:
                        result['generated_paper'][section_name] = content_text
        
        return result
        
    except Exception as e:
        print(f"데이터 추출 오류: {e}")
        return result

def generate_safe_pdf(content, filename="research_report.pdf"):
    """안전한 PDF 생성"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 데이터 추출
        topic = extract_topic_from_content(content)
        data = extract_structured_data_safe(content)
        
        print(f"📊 안전한 PDF 생성 시작: {topic}")
        
        # PDF 생성
        with suppress_warnings():
            pdf = SafeSciencePDF(topic)
            
            # 1. 표지
            pdf.add_cover_page()
            
            # 2. 주제 탐색
            pdf.add_page()
            pdf.add_section_header("🔬 주제 탐색 및 분석")
            
            if data['topic_explanation']:
                explanation = data['topic_explanation']
                
                # 개념 정의
                if '개념' in explanation or '정의' in explanation:
                    concept_section = explanation.split('응용')[0] if '응용' in explanation else explanation[:800]
                    if len(concept_section) > 100:
                        pdf.add_section_header("개념 정의 및 원리", level=2)
                        pdf.add_content_block(concept_section)
                
                # 연구 아이디어
                if '확장 가능한 탐구' in explanation:
                    ideas_start = explanation.find('확장 가능한 탐구')
                    ideas_section = explanation[ideas_start:]
                    if len(ideas_section) > 100:
                        pdf.add_section_header("연구 아이디어", level=2)
                        pdf.add_content_block(ideas_section)
            
            # 3. 관련 연구 조사
            pdf.add_section_header("📚 관련 연구 문헌 조사")
            
            # ISEF 연구
            if data['isef_papers']:
                pdf.add_section_header("ISEF 프로젝트 분석", level=2)
                for title, summary in data['isef_papers']:
                    pdf.add_paper_card_safe(title, summary, "출처: ISEF (International Science and Engineering Fair)")
            
            # arXiv 연구
            if data['arxiv_papers']:
                pdf.add_section_header("최신 연구논문 분석", level=2)
                for title, summary in data['arxiv_papers']:
                    pdf.add_paper_card_safe(title, summary, "출처: arXiv (프리프린트 논문저장소)")
            
            # 4. 연구 계획서
            if data['generated_paper']:
                pdf.add_section_header("📝 연구 계획서")
                
                section_order = ['초록', '서론', '실험 방법', '예상 결과', '결론', '참고문헌']
                section_english = {
                    '초록': 'Abstract',
                    '서론': 'Introduction', 
                    '실험 방법': 'Methods',
                    '예상 결과': 'Expected Results',
                    '결론': 'Conclusion',
                    '참고문헌': 'References'
                }
                
                for section_name in section_order:
                    if section_name in data['generated_paper']:
                        english_name = section_english.get(section_name, section_name)
                        title = f"{section_name} ({english_name})"
                        content_text = data['generated_paper'][section_name]
                        
                        if section_name == '참고문헌':
                            pdf.add_research_section_safe(title, "실제 연구 수행 시 관련 논문들을 찾아 APA 스타일로 작성하시기 바랍니다.")
                        else:
                            pdf.add_research_section_safe(title, content_text)
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            pdf.output(output_path)
        
        # 검증
        if os.path.exists(output_path) and os.path.getsize(output_path) > 3000:
            file_size = os.path.getsize(output_path)
            print(f"✅ 안전한 PDF 생성 성공: {output_path} ({file_size:,} bytes)")
            return output_path
        else:
            raise Exception("PDF 파일이 올바르게 생성되지 않음")
            
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        
        # 실패시 텍스트 파일로 백업
        try:
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {topic} 연구탐색보고서 ===\n")
                f.write(f"생성일: {datetime.now()}\n\n")
                f.write("PDF 생성에 실패하여 텍스트로 저장합니다.\n\n")
                f.write(content)
            print(f"📄 텍스트 백업 파일 생성: {txt_path}")
            return txt_path
        except Exception as txt_error:
            print(f"텍스트 백업도 실패: {txt_error}")
            return None

# 기존 함수 이름 호환성
def generate_pdf(content, filename="research_report.pdf"):
    """기존 함수명 호환성"""
    return generate_safe_pdf(content, filename)

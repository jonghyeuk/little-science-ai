# utils/beautiful_pdf_generator.py
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

class BeautifulSciencePDF(FPDF):
    def __init__(self, topic="과학 연구"):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.topic = self.clean_text_minimal(topic)
        self.setup_fonts()
        self.current_section = 0
        
        # 🎨 색상 팔레트 (현대적)
        self.colors = {
            'primary': (59, 130, 246),      # 파란색 (블루)
            'secondary': (16, 185, 129),    # 초록색 (그린)
            'accent': (139, 92, 246),       # 보라색 (퍼플)
            'warning': (245, 158, 11),      # 주황색 (오렌지)
            'text_dark': (17, 24, 39),      # 진한 텍스트
            'text_medium': (55, 65, 81),    # 중간 텍스트
            'text_light': (107, 114, 128),  # 연한 텍스트
            'bg_light': (249, 250, 251),    # 연한 배경
            'border': (229, 231, 235)       # 테두리
        }
        
    def setup_fonts(self):
        """폰트 설정"""
        self.korean_available = False
        try:
            with suppress_warnings():
                if os.path.exists(FONT_REGULAR):
                    self.add_font('Korean', '', FONT_REGULAR, uni=True)
                    self.korean_available = True
                if os.path.exists(FONT_BOLD):
                    self.add_font('KoreanBold', '', FONT_BOLD, uni=True)
        except:
            pass
            
    def set_font_beautiful(self, weight='normal', size=10, color='text_dark'):
        """이쁜 폰트 설정"""
        try:
            if self.korean_available:
                font_name = 'KoreanBold' if weight == 'bold' else 'Korean'
                self.set_font(font_name, size=size)
            else:
                style = 'B' if weight == 'bold' else ''
                self.set_font('Arial', style, size)
            
            # 색상 설정
            if color in self.colors:
                r, g, b = self.colors[color]
                self.set_text_color(r, g, b)
            else:
                self.set_text_color(55, 65, 81)  # 기본색
        except:
            self.set_font('Arial', '', size)
            self.set_text_color(55, 65, 81)
    
    def header(self):
        if self.page_no() > 1:
            self.set_font_beautiful('normal', 8, 'text_light')
            header_text = f'{self.topic} - 연구탐색보고서'
            if len(header_text) > 40:
                header_text = header_text[:37] + "..."
            
            # 헤더 라인
            r, g, b = self.colors['border']
            self.set_draw_color(r, g, b)
            self.line(20, 25, 190, 25)
            
            self.set_y(15)
            self.cell(0, 8, header_text, align='R', ln=True)
            self.ln(5)
            
    def footer(self):
        self.set_y(-20)
        
        # 푸터 라인
        r, g, b = self.colors['border']
        self.set_draw_color(r, g, b)
        self.line(20, self.get_y(), 190, self.get_y())
        
        self.ln(5)
        self.set_font_beautiful('normal', 8, 'text_light')
        self.cell(0, 10, f'- {self.page_no()} -', align='C')
    
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
        common_emojis = r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖]'
        text = re.sub(common_emojis, '', text)
        
        # 공백 정리
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def add_beautiful_cover(self):
        """현대적이고 이쁜 표지"""
        self.add_page()
        
        # 🎨 그라데이션 효과 (박스들로 구현)
        for i in range(5):
            alpha = 255 - (i * 30)
            gray = 240 + (i * 3)
            self.set_fill_color(gray, gray, gray)
            self.rect(20 + i, 30 + i, 170 - (i*2), 200 - (i*2), 'F')
        
        # 메인 배경
        r, g, b = self.colors['bg_light']
        self.set_fill_color(r, g, b)
        self.rect(25, 35, 160, 190, 'F')
        
        # 상단 색상 바
        r, g, b = self.colors['primary']
        self.set_fill_color(r, g, b)
        self.rect(25, 35, 160, 8, 'F')
        
        # 내용 시작
        self.set_y(60)
        
        # 메인 제목
        self.set_font_beautiful('bold', 24, 'text_dark')
        title_lines = self.split_text_to_lines(self.topic, 35)
        for line in title_lines:
            self.cell(0, 15, line, align='C', ln=True)
        
        self.ln(10)
        
        # 장식 라인
        r, g, b = self.colors['accent']
        self.set_draw_color(r, g, b)
        self.set_line_width(2)
        center_x = 105
        self.line(center_x - 30, self.get_y(), center_x + 30, self.get_y())
        self.set_line_width(0.2)  # 원래대로
        
        self.ln(15)
        
        # 부제목
        self.set_font_beautiful('normal', 16, 'text_medium')
        self.cell(0, 10, '과학 연구 탐색 보고서', align='C', ln=True)
        
        self.ln(20)
        
        # 설명 박스
        r, g, b = self.colors['bg_light']
        self.set_fill_color(255, 255, 255)  # 흰색 박스
        self.set_draw_color(*self.colors['border'])
        self.rect(40, self.get_y(), 130, 40, 'FD')
        
        self.ln(5)
        self.set_font_beautiful('normal', 10, 'text_medium')
        description = "AI를 활용한 과학 연구 주제 탐색,\n관련 문헌 조사 및 연구 계획 수립"
        lines = description.split('\n')
        for line in lines:
            self.cell(0, 8, line, align='C', ln=True)
        
        # 하단 정보
        self.set_y(200)
        self.set_font_beautiful('normal', 9, 'text_light')
        today = datetime.now().strftime("%Y년 %m월 %d일")
        self.cell(0, 6, f'생성일: {today}', align='C', ln=True)
        self.ln(2)
        self.cell(0, 6, 'LittleScienceAI', align='C', ln=True)
    
    def split_text_to_lines(self, text, max_chars):
        """텍스트를 적절한 길이로 분할"""
        if len(text) <= max_chars:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def add_section_header(self, title, icon="📌", level=1):
        """이쁜 섹션 헤더"""
        # 페이지 하단에서 시작하지 않도록
        if self.get_y() > 240:
            self.add_page()
        
        self.ln(8)
        
        if level == 1:
            self.current_section += 1
            # 섹션 배경 박스
            r, g, b = self.colors['bg_light']
            self.set_fill_color(r, g, b)
            self.rect(15, self.get_y()-2, 180, 20, 'F')
            
            # 사이드 컬러 바
            colors = [self.colors['primary'], self.colors['secondary'], 
                     self.colors['accent'], self.colors['warning']]
            color_idx = (self.current_section - 1) % len(colors)
            r, g, b = colors[color_idx]
            self.set_fill_color(r, g, b)
            self.rect(15, self.get_y()-2, 4, 20, 'F')
            
            self.ln(3)
            self.set_font_beautiful('bold', 16, 'text_dark')
            self.cell(10, 10, icon, align='C')
            self.cell(0, 10, title, align='L', ln=True)
            self.ln(2)
        else:
            self.set_font_beautiful('bold', 13, 'text_medium')
            self.cell(5, 8, icon, align='C')
            self.cell(0, 8, title, align='L', ln=True)
            self.ln(2)
    
    def add_content_block(self, content, preserve_length=True):
        """이쁜 내용 블록"""
        if not content:
            return
            
        self.set_font_beautiful('normal', 10, 'text_medium')
        
        cleaned_content = self.clean_text_minimal(content)
        
        # 자연스러운 길이 조정
        if preserve_length and len(cleaned_content) > 1800:
            paragraphs = cleaned_content.split('\n\n')
            kept_paragraphs = []
            total_length = 0
            
            for para in paragraphs:
                if total_length + len(para) < 1600:
                    kept_paragraphs.append(para)
                    total_length += len(para)
                else:
                    # 마지막 문장까지 완전히 포함
                    sentences = para.split('. ')
                    for sent in sentences:
                        if total_length + len(sent) < 1700:
                            kept_paragraphs.append(sent + '.')
                            total_length += len(sent)
                        else:
                            break
                    break
            
            cleaned_content = '\n\n'.join(kept_paragraphs)
        
        # 배경 박스
        content_height = len(cleaned_content) // 80 * 6 + 10  # 대략적 높이 계산
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*self.colors['border'])
        
        # 문단별로 출력
        paragraphs = cleaned_content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                self.multi_cell(0, 6, para.strip(), align='L')
                self.ln(3)
    
    def add_beautiful_paper_card(self, title, summary, source="", card_type="default"):
        """이쁜 논문 카드"""
        # 페이지 끝에서 카드가 시작되지 않도록
        if self.get_y() > 220:
            self.add_page()
        
        card_start_y = self.get_y()
        
        # 카드 타입별 색상
        if card_type == "isef":
            border_color = self.colors['primary']
            bg_color = (239, 246, 255)  # 연한 파란색
            icon = "🏆"
        elif card_type == "arxiv":
            border_color = self.colors['secondary']
            bg_color = (236, 253, 245)  # 연한 초록색
            icon = "📚"
        else:
            border_color = self.colors['text_light']
            bg_color = self.colors['bg_light']
            icon = "📄"
        
        # 카드 배경
        self.set_fill_color(*bg_color)
        self.set_draw_color(*self.colors['border'])
        card_height = 45  # 기본 높이
        self.rect(20, card_start_y, 170, card_height, 'FD')
        
        # 사이드 컬러 바
        self.set_fill_color(*border_color)
        self.rect(20, card_start_y, 3, card_height, 'F')
        
        # 내용
        self.ln(4)
        self.set_x(28)
        
        # 아이콘과 제목
        self.set_font_beautiful('bold', 11, 'text_dark')
        clean_title = self.clean_text_minimal(title)
        if len(clean_title) > 65:
            clean_title = clean_title[:62] + "..."
        
        title_text = f"{icon} {clean_title}"
        self.multi_cell(165, 6, title_text, align='L')
        
        # 출처
        if source:
            self.set_x(28)
            self.set_font_beautiful('normal', 8, 'text_light')
            self.multi_cell(165, 4, source, align='L')
        
        # 요약
        self.set_x(28)
        self.set_font_beautiful('normal', 9, 'text_medium')
        clean_summary = self.clean_text_minimal(summary)
        
        # 요약 자연스럽게 줄이기
        if len(clean_summary) > 250:
            sentences = clean_summary.split('. ')
            kept_sentences = []
            total_len = 0
            for sent in sentences:
                if total_len + len(sent) < 230:
                    kept_sentences.append(sent)
                    total_len += len(sent)
                else:
                    break
            clean_summary = '. '.join(kept_sentences)
            if not clean_summary.endswith('.'):
                clean_summary += '.'
        
        self.multi_cell(165, 5, clean_summary, align='L')
        self.ln(8)
    
    def add_research_section(self, title, content, section_type="default"):
        """연구 계획 섹션"""
        self.ln(5)
        
        # 섹션별 아이콘
        icons = {
            '초록': '📋', '서론': '📖', '실험 방법': '🔬', 
            '예상 결과': '📊', '시각자료': '📈', '결론': '🎯', '참고문헌': '📚'
        }
        icon = icons.get(title.split(' ')[0], '📌')
        
        # 섹션 박스
        section_start_y = self.get_y()
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*self.colors['border'])
        
        # 제목
        self.set_font_beautiful('bold', 12, 'text_dark')
        title_with_icon = f"{icon} {title}"
        self.cell(0, 8, title_with_icon, align='L', ln=True)
        
        # 제목 아래 라인
        r, g, b = self.colors['primary']
        self.set_draw_color(r, g, b)
        self.set_line_width(1)
        self.line(20, self.get_y(), 60, self.get_y())
        self.set_line_width(0.2)  # 원래대로
        
        self.ln(5)
        
        # 내용
        self.set_font_beautiful('normal', 10, 'text_medium')
        cleaned_content = self.clean_text_minimal(content)
        
        # 연구 계획은 더 자세히 보존
        if len(cleaned_content) > 1200:
            paragraphs = cleaned_content.split('\n')
            kept_paragraphs = []
            total_length = 0
            
            for para in paragraphs:
                if total_length + len(para) < 1100:
                    kept_paragraphs.append(para)
                    total_length += len(para)
                else:
                    break
            
            cleaned_content = '\n'.join(kept_paragraphs)
        
        self.multi_cell(0, 6, cleaned_content, align='L')
        self.ln(6)

def extract_topic_from_content(content):
    """내용에서 주제 추출"""
    try:
        patterns = [
            r'# 📘\s*([^\n-]+?)(?:\s*-|$)',
            r'주제[:\s]*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                topic = re.sub(r'주제\s*해설', '', topic).strip()
                if len(topic) > 3:
                    return topic[:50] if len(topic) > 50 else topic
        
        return "과학 연구 탐색"
    except:
        return "과학 연구 탐색"

def parse_content_smart(content):
    """스마트한 내용 파싱"""
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
        
        # ISEF 논문 추출
        if "ISEF" in content:
            isef_section = content[content.find("ISEF"):content.find("arXiv") if "arXiv" in content else len(content)]
            
            # 제목 패턴 찾기
            title_pattern = r'📌\s*([^\n]+)'
            titles = re.findall(title_pattern, isef_section)
            
            for title in titles[:3]:
                # 각 제목 다음의 내용 찾기
                title_pos = isef_section.find(title)
                next_title_pos = isef_section.find('📌', title_pos + 1)
                if next_title_pos == -1:
                    next_title_pos = len(isef_section)
                
                section_content = isef_section[title_pos:next_title_pos]
                lines = section_content.split('\n')[1:4]  # 제목 다음 3줄
                summary = ' '.join([line.strip() for line in lines if line.strip() and not line.strip().startswith('📅')])
                
                if len(summary) > 20:
                    result['isef_papers'].append((title.strip(), summary))
        
        # arXiv 논문 추출
        if "arXiv" in content:
            arxiv_section = content[content.find("arXiv"):]
            
            title_pattern = r'🌐\s*([^\n]+)'
            titles = re.findall(title_pattern, arxiv_section)
            
            for title in titles[:3]:
                title_pos = arxiv_section.find(title)
                next_title_pos = arxiv_section.find('🌐', title_pos + 1)
                if next_title_pos == -1:
                    next_title_pos = len(arxiv_section)
                
                section_content = arxiv_section[title_pos:next_title_pos]
                lines = section_content.split('\n')[1:4]
                summary = ' '.join([line.strip() for line in lines if line.strip() and '출처:' not in line])
                
                if len(summary) > 20:
                    result['arxiv_papers'].append((title.strip(), summary))
        
        # 생성된 논문 추출
        if "생성된 연구 논문" in content:
            paper_section = content[content.find("생성된 연구 논문"):]
            
            sections = {
                '초록': r'초록[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)',
                '서론': r'서론[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)',
                '실험 방법': r'실험\s*방법[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)',
                '예상 결과': r'예상\s*결과[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)',
                '시각자료': r'시각자료[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)',
                '결론': r'결론[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)',
                '참고문헌': r'참고문헌[^\n]*(?:\([^)]*\))?[^\n]*\n([^#]+?)(?=###|$)'
            }
            
            for section_name, pattern in sections.items():
                match = re.search(pattern, paper_section, re.DOTALL | re.IGNORECASE)
                if match:
                    content_text = match.group(1).strip()
                    if len(content_text) > 20:
                        result['generated_paper'][section_name] = content_text
        
        return result
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """이쁜 PDF 생성 (Streamlit Cloud 안정성 보장)"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 데이터 추출
        topic = extract_topic_from_content(content)
        data = parse_content_smart(content)
        
        print(f"🎨 이쁜 PDF 생성 시작: {topic}")
        print(f"   - 주제해설: {len(data['topic_explanation'])}자")
        print(f"   - ISEF 논문: {len(data['isef_papers'])}개")
        print(f"   - arXiv 논문: {len(data['arxiv_papers'])}개") 
        print(f"   - 생성된 논문: {len(data['generated_paper'])}개 섹션")
        
        # PDF 생성
        with suppress_warnings():
            pdf = BeautifulSciencePDF(topic)
            
            # 1. 이쁜 표지
            pdf.add_beautiful_cover()
            
            # 2. 주제 탐색
            pdf.add_page()
            pdf.add_section_header("주제 탐색 및 분석", "🔬")
            
            if data['topic_explanation']:
                explanation = data['topic_explanation']
                
                # 개념 정의
                if '개념' in explanation or '정의' in explanation:
                    concept_section = explanation.split('응용')[0] if '응용' in explanation else explanation[:900]
                    if len(concept_section) > 100:
                        pdf.add_section_header("개념 정의 및 원리", "💡", level=2)
                        pdf.add_content_block(concept_section)
                
                # 연구 아이디어
                if '확장 가능한 탐구' in explanation:
                    ideas_start = explanation.find('확장 가능한 탐구')
                    ideas_section = explanation[ideas_start:]
                    if len(ideas_section) > 100:
                        pdf.add_section_header("연구 아이디어", "🎯", level=2)
                        pdf.add_content_block(ideas_section)
            
            # 3. 관련 연구 조사
            pdf.add_section_header("관련 연구 문헌 조사", "📚")
            
            # ISEF 연구
            if data['isef_papers']:
                pdf.add_section_header("ISEF 프로젝트 분석", "🏆", level=2)
                for title, summary in data['isef_papers']:
                    pdf.add_beautiful_paper_card(title, summary, "출처: ISEF (International Science and Engineering Fair)", "isef")
            
            # arXiv 연구
            if data['arxiv_papers']:
                pdf.add_section_header("최신 연구논문 분석", "📚", level=2)
                for title, summary in data['arxiv_papers']:
                    pdf.add_beautiful_paper_card(title, summary, "출처: arXiv (프리프린트 논문저장소)", "arxiv")
            
            # 4. 연구 계획서
            if data['generated_paper']:
                pdf.add_section_header("연구 계획서", "📝")
                
                section_order = ['초록', '서론', '실험 방법', '예상 결과', '시각자료', '결론', '참고문헌']
                section_english = {
                    '초록': 'Abstract',
                    '서론': 'Introduction',
                    '실험 방법': 'Methods',
                    '예상 결과': 'Expected Results',
                    '시각자료': 'Visualizations',
                    '결론': 'Conclusion',
                    '참고문헌': 'References'
                }
                
                for section_name in section_order:
                    if section_name in data['generated_paper']:
                        english_name = section_english.get(section_name, section_name)
                        title = f"{section_name} ({english_name})"
                        content_text = data['generated_paper'][section_name]
                        
                        if section_name == '참고문헌':
                            pdf.add_research_section(title, "실제 연구 수행 시 관련 논문들을 찾아 APA 스타일로 작성하시기 바랍니다.")
                        else:
                            pdf.add_research_section(title, content_text)
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            pdf.output(output_path)
        
        # 검증
        if os.path.exists(output_path) and os.path.getsize(output_path) > 5000:
            print(f"✅ 이쁜 PDF 생성 완료: {output_path}")
            return output_path
        else:
            raise Exception("PDF 생성 실패")
            
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        
        # 실패시 텍스트 파일로 백업
        try:
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== {topic} 연구탐색보고서 ===\n")
                f.write(f"생성일: {datetime.now()}\n\n")
                f.write("PDF 생성 실패로 텍스트로 저장합니다.\n\n")
                f.write(content)
            return txt_path
        except:
            return None

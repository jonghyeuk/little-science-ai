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

class RobustKoreanPDF(FPDF):
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
        """매우 견고한 폰트 설정"""
        font_status = {
            'korean_available': False,
            'fallback_only': False
        }
        
        try:
            print("견고한 폰트 설정 시작...")
            
            # 완전히 조용하게 폰트 로딩
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Regular 폰트만 성공하면 됨
                if os.path.exists(FONT_REGULAR):
                    try:
                        self.add_font('Korean', '', FONT_REGULAR, uni=True)
                        font_status['korean_available'] = True
                        print("✅ 한글 폰트 로드 성공")
                    except Exception as e:
                        print(f"한글 폰트 실패: {e}")
                
                # Bold 시도 (실패해도 무관)
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
        """안전한 폰트 설정 (단순화)"""
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
                # Arial 폴백
                style = 'B' if weight == 'bold' else ''
                self.set_font('Arial', style, size)
        except Exception as e:
            print(f"폰트 설정 오류, Arial 사용: {e}")
            self.set_font('Arial', '', size)
    
    def header(self):
        """간단한 헤더"""
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
        """간단한 푸터"""
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
    
    def add_paragraph(self, text):
        """문단 추가 (단순화)"""
        try:
            self.set_safe_font('normal', 10)
            self.set_text_color(70, 70, 70)
            
            clean_text = self.clean_text(text)
            if clean_text and len(clean_text.strip()) > 5:
                # 긴 문단은 나누어서 처리
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
            # 오류가 나도 계속 진행
    
    def add_paper_item(self, title, summary, source=""):
        """논문 항목 추가 (단순화)"""
        try:
            # 제목
            self.set_safe_font('bold', 10)
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            if len(clean_title) > 80:
                clean_title = clean_title[:77] + "..."
            
            self.multi_cell(0, 7, f"• {clean_title}", align='L')
            
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
            
            self.ln(3)
            
        except Exception as e:
            print(f"논문 항목 오류: {e}")
    
    def clean_text(self, text):
        """강력한 텍스트 정리"""
        try:
            if not text:
                return ""
            
            # 문자열로 변환
            text = str(text)
            
            # URL 완전 제거
            text = re.sub(r'https?://[^\s\]\)\n]+', '', text)
            text = re.sub(r'www\.[^\s\]\)\n]+', '', text)
            
            # 마크다운 제거
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'[*_`#\[\]<>]', '', text)
            
            # 이모지 제거
            emoji_pattern = r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅🔍❗🚀✅📌🎉🔧🛠️]'
            text = re.sub(emoji_pattern, '', text)
            
            # 특수 문자 정리
            text = re.sub(r'DOI\s*:\s*', '', text)
            text = re.sub(r'&[a-zA-Z]+;', '', text)  # HTML 엔티티 제거
            
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
        # 첫 번째 제목 찾기
        title_match = re.search(r'# 📘\s*([^\n-]+)', content)
        if title_match:
            topic = title_match.group(1).strip()
            return topic[:50] if len(topic) > 50 else topic
        
        # 백업: 다른 패턴들
        patterns = [
            r'주제.*?:\s*([^\n]+)',
            r'제목.*?:\s*([^\n]+)',
            r'연구.*?:\s*([^\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()[:50]
        
        return "과학 연구 탐색"
        
    except:
        return "과학 연구 탐색"

def parse_content_safely(content):
    """안전한 내용 파싱"""
    result = {
        'topic_explanation': '',
        'isef_papers': [],
        'arxiv_papers': [],
        'generated_paper': {}
    }
    
    try:
        print("내용 파싱 시작...")
        
        # 1. 주제 해설 추출
        explanation_patterns = [
            r'# 📘[^\n]*\n(.*?)(?=## 📄|## 🌐|$)',
            r'주제 해설[^\n]*\n(.*?)(?=## |$)',
        ]
        
        for pattern in explanation_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                result['topic_explanation'] = match.group(1).strip()
                break
        
        # 2. ISEF 논문들
        isef_section = ''
        if "ISEF" in content or "내부 DB" in content:
            isef_match = re.search(r'## 📄[^\n]*\n(.*?)(?=## 🌐|## 📄 생성|$)', content, re.DOTALL)
            if isef_match:
                isef_section = isef_match.group(1)
        
        # ISEF 논문 파싱
        if isef_section:
            papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^_\n]*)', isef_section)
            result['isef_papers'] = [(title, summary) for title, summary in papers if len(title) > 5][:3]
        
        # 3. arXiv 논문들
        arxiv_section = ''
        if "arXiv" in content:
            arxiv_match = re.search(r'## 🌐[^\n]*\n(.*?)(?=## 📄 생성|$)', content, re.DOTALL)
            if arxiv_match:
                arxiv_section = arxiv_match.group(1)
        
        if arxiv_section:
            papers = re.findall(r'- \*\*([^*\n]+)\*\*[^\n]*\n([^[\n]*)', arxiv_section)
            result['arxiv_papers'] = [(title, summary) for title, summary in papers if len(title) > 5][:3]
        
        # 4. 생성된 논문
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
        
        print(f"파싱 완료 - 주제해설: {bool(result['topic_explanation'])}, ISEF: {len(result['isef_papers'])}, arXiv: {len(result['arxiv_papers'])}, 논문: {len(result['generated_paper'])}")
        return result
        
    except Exception as e:
        print(f"내용 파싱 오류: {e}")
        return result

def generate_pdf(content, filename="research_report.pdf"):
    """견고한 PDF 생성"""
    try:
        print("=== 견고한 PDF 생성 시작 ===")
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 주제 추출
        topic = extract_topic_from_content(content)
        print(f"추출된 주제: {topic}")
        
        # 내용 파싱
        sections = parse_content_safely(content)
        
        # PDF 생성 (경고 완전 억제)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            pdf = RobustKoreanPDF(topic)
            
            # 1. 표지 페이지
            pdf.add_title_page(topic)
            
            # 2. 내용 페이지
            pdf.add_page()
            
            # 3. 주제 개요
            if sections['topic_explanation']:
                pdf.add_section_title("주제 개요")
                
                # 문단별로 나누어 추가
                paragraphs = sections['topic_explanation'].split('\n\n')
                for para in paragraphs:
                    if para.strip() and len(para.strip()) > 10:
                        pdf.add_paragraph(para.strip())
            
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
            
            # 5. 생성된 논문 (있는 경우)
            if sections['generated_paper']:
                pdf.add_section_title("연구 논문")
                
                paper_order = ['초록', '서론', '실험 방법', '예상 결과', '결론', '참고문헌']
                for section_key in paper_order:
                    if section_key in sections['generated_paper']:
                        pdf.add_section_title(section_key, level=2)
                        pdf.add_paragraph(sections['generated_paper'][section_key])
            
            # 저장
            output_path = os.path.join(OUTPUT_DIR, filename)
            pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 2000:
                print(f"✅ PDF 생성 성공: {output_path} ({file_size:,} bytes)")
                
                # 내용 검증 (간단히)
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
        
        # 실패시 디버그 정보와 함께 텍스트 파일 생성
        print("PDF 생성 실패, 백업 텍스트 파일 생성...")
        txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_debug.txt'))
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"=== {topic} 연구보고서 (디버그 버전) ===\n\n")
            f.write(f"생성 시간: {datetime.now()}\n")
            f.write(f"원본 내용 길이: {len(content)} 문자\n\n")
            
            # 파싱된 섹션들 저장
            f.write("=== 파싱된 섹션들 ===\n")
            f.write(f"주제 해설: {len(sections['topic_explanation'])} 문자\n")
            f.write(f"ISEF 논문: {len(sections['isef_papers'])}개\n")
            f.write(f"arXiv 논문: {len(sections['arxiv_papers'])}개\n")
            f.write(f"생성된 논문 섹션: {len(sections['generated_paper'])}개\n\n")
            
            # 정리된 원본 내용
            f.write("=== 정리된 원본 내용 ===\n")
            clean_content = re.sub(r'https?://[^\s]+', '[링크제거]', content)
            f.write(clean_content)
        
        print(f"✅ 백업 파일 생성: {txt_path}")
        return txt_path
            
    except Exception as e:
        print(f"❌ PDF 생성 중 치명적 오류: {e}")
        return None

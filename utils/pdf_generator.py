from fpdf import FPDF
import os
import re

# 폰트 경로 (사용자가 제공한 3가지)
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
FONT_EXTRABOLD = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")
OUTPUT_DIR = "outputs"

class SafeKoreanPDF(FPDF):
    def __init__(self):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.fonts_loaded = self.setup_fonts()
        
    def setup_fonts(self):
        """3가지 나눔고딕 폰트 안전하게 로드"""
        try:
            fonts_count = 0
            
            print("폰트 파일 확인 중...")
            print(f"Regular: {os.path.exists(FONT_REGULAR)} - {FONT_REGULAR}")
            print(f"Bold: {os.path.exists(FONT_BOLD)} - {FONT_BOLD}")
            print(f"ExtraBold: {os.path.exists(FONT_EXTRABOLD)} - {FONT_EXTRABOLD}")
            
            # Regular 폰트
            if os.path.exists(FONT_REGULAR):
                self.add_font('NanumRegular', '', FONT_REGULAR, uni=True)
                fonts_count += 1
                print("✅ Regular 폰트 로드 성공")
            
            # Bold 폰트
            if os.path.exists(FONT_BOLD):
                self.add_font('NanumBold', '', FONT_BOLD, uni=True)
                fonts_count += 1
                print("✅ Bold 폰트 로드 성공")
                
            # ExtraBold 폰트
            if os.path.exists(FONT_EXTRABOLD):
                self.add_font('NanumExtraBold', '', FONT_EXTRABOLD, uni=True)
                fonts_count += 1
                print("✅ ExtraBold 폰트 로드 성공")
            
            if fonts_count >= 2:
                print(f"✅ {fonts_count}개 폰트 로드 완료")
                return True
            else:
                print("❌ 충분한 폰트를 로드하지 못함")
                return False
                
        except Exception as e:
            print(f"❌ 폰트 로드 중 오류: {e}")
            return False
    
    def header(self):
        try:
            if self.fonts_loaded:
                self.set_font('NanumBold', size=14)
            else:
                self.set_font('Arial', 'B', 14)
            
            self.set_text_color(70, 70, 70)
            self.cell(0, 12, 'LittleScienceAI 연구 보고서', align='C', ln=True)
            self.ln(8)
        except Exception as e:
            print(f"헤더 오류: {e}")
            
    def footer(self):
        try:
            self.set_y(-15)
            if self.fonts_loaded:
                self.set_font('NanumRegular', size=9)
            else:
                self.set_font('Arial', '', 9)
            
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'페이지 {self.page_no()}', align='C')
        except Exception as e:
            print(f"푸터 오류: {e}")
    
    def write_content(self, content):
        """안전한 내용 작성 - 🔥 리스트 처리 추가"""
        self.add_page()
        
        lines = content.split('\n')
        list_counter = 0  # 🔥 틈새주제 번호 카운터 추가
        
        for i, line in enumerate(lines):
            try:
                line = line.strip()
                
                if not line:  # 빈 줄
                    self.ln(3)
                    list_counter = 0  # 카운터 리셋
                    continue
                
                # 제목별 처리
                if line.startswith('# '):
                    self.add_main_title(line[2:])
                    list_counter = 0
                elif line.startswith('## '):
                    self.add_section_title(line[3:])
                    list_counter = 0
                elif line.startswith('### '):
                    self.add_sub_title(line[4:])
                    list_counter = 0
                # 🔥 리스트 항목 처리 추가
                elif line.startswith('- ') or line.startswith('• '):
                    list_counter += 1
                    item_text = line[2:].strip()
                    self.add_list_item(item_text, list_counter)
                else:
                    self.add_normal_text(line)
                    if not any(line.startswith(prefix) for prefix in ['- ', '• ']):
                        list_counter = 0
                    
            except Exception as e:
                print(f"라인 {i} 처리 오류: {e}")
                # 오류가 나도 계속 진행
                continue
    
    def add_main_title(self, title):
        """큰 제목 (ExtraBold 사용)"""
        try:
            self.ln(8)
            if self.fonts_loaded:
                self.set_font('NanumExtraBold', size=16)
            else:
                self.set_font('Arial', 'B', 16)
            
            self.set_text_color(40, 40, 40)
            title = self.clean_text(title)
            self.multi_cell(0, 12, title, align='L')
            self.ln(6)
        except Exception as e:
            print(f"메인 제목 오류: {e}")
    
    def add_section_title(self, title):
        """섹션 제목 (Bold 사용)"""
        try:
            self.ln(6)
            if self.fonts_loaded:
                self.set_font('NanumBold', size=13)
            else:
                self.set_font('Arial', 'B', 13)
            
            self.set_text_color(60, 60, 60)
            title = self.clean_text(title)
            self.multi_cell(0, 10, title, align='L')
            self.ln(4)
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
    
    def add_sub_title(self, title):
        """소제목 (Bold 사용)"""
        try:
            self.ln(4)
            if self.fonts_loaded:
                self.set_font('NanumBold', size=11)
            else:
                self.set_font('Arial', 'B', 11)
            
            self.set_text_color(80, 80, 80)
            title = self.clean_text(title)
            self.multi_cell(0, 8, title, align='L')
            self.ln(3)
        except Exception as e:
            print(f"소제목 오류: {e}")
    
    def add_normal_text(self, text):
        """일반 텍스트 (Regular 사용)"""
        try:
            if self.fonts_loaded:
                self.set_font('NanumRegular', size=10)
            else:
                self.set_font('Arial', '', 10)
            
            self.set_text_color(90, 90, 90)
            text = self.clean_text(text)
            
            if text:  # 빈 텍스트가 아니면
                self.multi_cell(0, 7, text, align='L')
                self.ln(2)
        except Exception as e:
            print(f"일반 텍스트 오류: {e}")
    
    # 🔥 추가: 리스트 항목 처리 함수
    def add_list_item(self, text, number):
        """리스트 항목 - 번호 포함"""
        try:
            if self.fonts_loaded:
                self.set_font('NanumRegular', size=10)
            else:
                self.set_font('Arial', '', 10)
            
            self.set_text_color(90, 90, 90)
            clean_text = self.clean_text(text)
            
            if clean_text:
                formatted_text = f"{number}. {clean_text}"
                self.multi_cell(0, 7, formatted_text, align='L')
                self.ln(2)
        except Exception as e:
            print(f"리스트 항목 오류: {e}")
    
    def clean_text(self, text):
        """텍스트 정리 (마크다운 기호 제거 등) - 🔥 링크 간소화 추가"""
        try:
            # 🔥 복잡한 검색 링크 섹션 간소화
            if "https://" in text and len(text) > 500:
                if any(keyword in text for keyword in ["scholar.google.com", "academic.naver.com", "riss.kr", "dbpia.co.kr"]):
                    return "추가 연구를 위한 검색 가이드\n\n관련 키워드로 Google Scholar, 네이버 학술정보, RISS, DBpia 등에서 논문을 검색해보세요."
            
            # 🔥 URL 링크 제거 (PDF에서는 클릭 불가하므로)
            text = re.sub(r'https?://[^\s\]]+', '', text)
            
            # 마크다운 기호 제거 (v5 원본과 동일)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = text.replace('**', '')
            text = re.sub(r'[*_`]', '', text)
            
            # 일부 이모지 제거 (PDF에서 문제가 될 수 있음)
            text = re.sub(r'[📘📄🌐🔬💡⚙️🌍📊🎯📋📖🔗📚📈🏆📅]', '', text)
            
            # 앞뒤 공백 제거
            text = text.strip()
            
            return text
            
        except Exception as e:
            print(f"텍스트 정리 오류: {e}")
            return "[텍스트 처리 오류]"

def generate_pdf(content, filename="research_report.pdf"):
    """PDF 생성 메인 함수 (v5 원본과 동일)"""
    try:
        print("=== PDF 생성 시작 ===")
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"출력 디렉토리: {OUTPUT_DIR}")
        
        # PDF 생성
        pdf = SafeKoreanPDF()
        pdf.write_content(content)
        
        # 저장
        output_path = os.path.join(OUTPUT_DIR, filename)
        pdf.output(output_path)
        
        # 파일 확인
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"생성된 파일 크기: {file_size} bytes")
            
            if file_size > 2000:  # 최소 2KB
                print(f"✅ PDF 생성 성공: {output_path}")
                return output_path
            else:
                raise Exception(f"PDF 파일이 너무 작음 ({file_size} bytes)")
        else:
            raise Exception("PDF 파일이 생성되지 않음")
            
    except Exception as e:
        print(f"❌ PDF 생성 실패: {str(e)}")
        
        # 실패시 텍스트 파일로 저장
        try:
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '_backup.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== LittleScienceAI 연구 보고서 ===\n")
                f.write("(PDF 생성 실패로 텍스트 버전으로 저장)\n\n")
                f.write(content)
            
            print(f"✅ 백업 텍스트 파일 저장: {txt_path}")
            return txt_path
            
        except Exception as txt_error:
            print(f"❌ 텍스트 파일 저장도 실패: {txt_error}")
            return None

from fpdf import FPDF
import os
import re

# 폰트 경로
FONT_DIR = "fonts"
OUTPUT_DIR = "outputs"

class LittleSciencePDF(FPDF):
    def __init__(self):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.fonts_ready = False
        self.setup_fonts()
        
    def setup_fonts(self):
        try:
            # 3가지 폰트 등록
            regular_path = os.path.join(FONT_DIR, "NanumGothic-Regular.ttf")
            bold_path = os.path.join(FONT_DIR, "NanumGothic-Bold.ttf")
            extrabold_path = os.path.join(FONT_DIR, "NanumGothic-ExtraBold.ttf")
            
            if os.path.exists(regular_path):
                self.add_font('NanumRegular', '', regular_path, uni=True)
                
            if os.path.exists(bold_path):
                self.add_font('NanumBold', '', bold_path, uni=True)
                
            if os.path.exists(extrabold_path):
                self.add_font('NanumExtra', '', extrabold_path, uni=True)
                
            self.fonts_ready = True
            print("✅ 폰트 로드 완료")
            
        except Exception as e:
            print(f"❌ 폰트 로드 실패: {e}")
            self.fonts_ready = False
    
    def header(self):
        # 헤더 - 간단하게
        if self.fonts_ready:
            self.set_font('NanumBold', size=12)
        else:
            self.set_font('Arial', 'B', 12)
        
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'LittleScienceAI Research Report', align='C', ln=True)
        self.ln(5)
        
    def footer(self):  
        self.set_y(-15)
        if self.fonts_ready:
            self.set_font('NanumRegular', size=9)
        else:
            self.set_font('Arial', '', 9)
        
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
    
    def write_content(self, content):
        self.add_page()
        
        # 텍스트를 줄 단위로 분리
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line:  # 빈 줄
                self.ln(4)
                continue
                
            # 제목 처리
            if line.startswith('# '):
                self.add_main_title(line[2:])
                
            elif line.startswith('## '):
                self.add_section_title(line[3:])
                
            elif line.startswith('### '):
                self.add_sub_title(line[4:])
                
            # 볼드 텍스트 처리
            elif line.startswith('**') and line.endswith('**'):
                self.add_bold_text(line[2:-2])
                
            # 일반 텍스트
            else:
                self.add_normal_text(line)
    
    def add_main_title(self, title):
        self.ln(8)
        if self.fonts_ready:
            self.set_font('NanumExtra', size=16)
        else:
            self.set_font('Arial', 'B', 16)
        
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 12, title, align='L')
        self.ln(6)
    
    def add_section_title(self, title):
        self.ln(6)
        if self.fonts_ready:
            self.set_font('NanumBold', size=13)
        else:
            self.set_font('Arial', 'B', 13)
        
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 10, title, align='L')
        self.ln(4)
    
    def add_sub_title(self, title):
        self.ln(4)
        if self.fonts_ready:
            self.set_font('NanumBold', size=11)
        else:
            self.set_font('Arial', 'B', 11)
        
        self.set_text_color(70, 70, 70)
        self.multi_cell(0, 8, title, align='L')
        self.ln(3)
    
    def add_bold_text(self, text):
        if self.fonts_ready:
            self.set_font('NanumBold', size=10)
        else:
            self.set_font('Arial', 'B', 10)
        
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 7, text, align='L')
        self.ln(2)
    
    def add_normal_text(self, text):
        if self.fonts_ready:
            self.set_font('NanumRegular', size=10)
        else:
            self.set_font('Arial', '', 10)
        
        self.set_text_color(80, 80, 80)
        
        # 긴 텍스트는 자동 줄바꿈
        self.multi_cell(0, 6, text, align='L')
        self.ln(2)

def generate_pdf(content, filename="research_report.pdf"):
    """PDF 생성 메인 함수"""
    try:
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # PDF 생성
        pdf = LittleSciencePDF()
        pdf.write_content(content)
        
        # 저장
        output_path = os.path.join(OUTPUT_DIR, filename)
        pdf.output(output_path)
        
        # 파일 존재 확인
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"✅ PDF 생성 성공: {output_path}")
            return output_path
        else:
            raise Exception("PDF 파일이 생성되지 않음")
            
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        
        # 실패시 텍스트 파일로 저장
        try:
            txt_path = os.path.join(OUTPUT_DIR, filename.replace('.pdf', '.txt'))
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== LittleScienceAI 연구 보고서 ===\n\n")
                f.write(content)
            
            print(f"✅ 텍스트 파일로 저장: {txt_path}")
            return txt_path
            
        except Exception as txt_error:
            print(f"❌ 텍스트 파일 저장도 실패: {txt_error}")
            return None

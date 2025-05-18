# utils/pdf_generator.py

from fpdf import FPDF
import os

FONT_PATH = os.path.join("fonts", "NanumGothic-Regular.ttf")

class PDF(FPDF):
    def header(self):
        self.set_font("Nanum", 'B', 16)
        self.cell(0, 10, 'LittleScienceAI 가상 논문 자료', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font("Nanum", '', 10)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

def generate_pdf(content, filename="output.pdf"):
    pdf = PDF()
    
    # ✅ 폰트 등록 먼저
    pdf.add_font('Nanum', '', FONT_PATH, uni=True)
    pdf.add_font('Nanum', 'B', FONT_PATH, uni=True)
    
    pdf.set_font("Nanum", '', 12)
    pdf.add_page()  # ⚠️ 폰트 등록 이후에 add_page() 호출해야 header가 정상 작동함

    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    pdf.output(output_path)
    return output_path

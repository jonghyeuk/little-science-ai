from fpdf import FPDF
import os

FONT_PATH = os.path.join("fonts", "NanumGothic-Regular.ttf")
OUTPUT_DIR = "outputs"

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('Nanum', '', FONT_PATH, uni=True)
        self.add_font('Nanum', 'B', FONT_PATH, uni=True)
        self.set_font("Nanum", size=12)
        self.set_margins(left=20, top=25, right=20)

    def header(self):
        self.set_font("Nanum", 'B', 14)
        self.cell(0, 10, 'LittleScienceAI 가상 논문 리포트', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Nanum", '', 10)
        self.cell(0, 10, f"Page {self.page_no()}", align='C')

    def write_content(self, text):
        self.set_font("Nanum", '', 12)
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                self.ln(5)
                continue
            if line.startswith("- **") and "**" in line[4:]:
                self.set_font("Nanum", 'B', 12)
                clean = line.replace("**", "").replace("- ", "")
                self.multi_cell(0, 8, f"▶ {clean}")
                self.set_font("Nanum", '', 12)
            elif line.startswith("🔗"):
                self.set_text_color(0, 102, 204)  # 링크 색상
                self.multi_cell(0, 8, line)
                self.set_text_color(0, 0, 0)
            else:
                self.multi_cell(0, 8, line)

def generate_pdf(content: str, filename="output.pdf") -> str:
    pdf = PDF()
    pdf.write_content(content)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(output_path)
    return output_path

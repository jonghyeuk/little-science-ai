from fpdf import FPDF
import os

# 📁 경로 설정
FONT_PATH = os.path.join("fonts", "NanumGothic-Regular.ttf")
OUTPUT_DIR = "outputs"

class PDF(FPDF):
    def __init__(self):  # ✅ 수정: **init** → __init__
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        
        # 🔧 폰트 등록 (안전하게 처리)
        try:
            if os.path.exists(FONT_PATH):
                # Regular 폰트 등록
                self.add_font('Nanum', '', FONT_PATH, uni=True)
                # Bold 폰트는 같은 파일 사용 (NanumGothic은 하나의 파일로 처리)
                self.add_font('Nanum', 'B', FONT_PATH, uni=True)
                self.font_available = True
                print("✅ 한글 폰트 로드 성공")
            else:
                print(f"❌ 폰트 파일 없음: {FONT_PATH}")
                self.font_available = False
        except Exception as e:
            print(f"❌ 폰트 등록 실패: {e}")
            self.font_available = False
        
        # 폰트 설정
        if self.font_available:
            self.set_font("Nanum", size=12)
        else:
            self.set_font("Arial", size=12)  # 대체 폰트
        
        self.set_margins(left=20, top=25, right=20)

    def header(self):
        if self.font_available:
            self.set_font("Nanum", 'B', 14)
        else:
            self.set_font("Arial", 'B', 14)
        self.cell(0, 10, 'LittleScienceAI 연구 리포트', ln=True, align='C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        if self.font_available:
            self.set_font("Nanum", '', 10)
        else:
            self.set_font("Arial", '', 10)
        self.cell(0, 10, f"Page {self.page_no()}", align='C')

    def write_content(self, text):
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                self.ln(4)
                continue
                
            # 📌 제목 스타일 처리
            if line.startswith("# "):
                if self.font_available:
                    self.set_font("Nanum", 'B', 16)
                else:
                    self.set_font("Arial", 'B', 16)
                self.multi_cell(0, 10, line.replace("# ", ""))
                self.ln(2)
                
            elif line.startswith("## "):
                if self.font_available:
                    self.set_font("Nanum", 'B', 14)
                else:
                    self.set_font("Arial", 'B', 14)
                self.multi_cell(0, 9, line.replace("## ", ""))
                self.ln(1)
                
            elif line.startswith("- **") and "**" in line[4:]:
                if self.font_available:
                    self.set_font("Nanum", 'B', 12)
                else:
                    self.set_font("Arial", 'B', 12)
                clean = line.replace("**", "").replace("- ", "")
                self.multi_cell(0, 8, f"▶ {clean}")
                # 다음 줄을 위해 regular 폰트로 복원
                if self.font_available:
                    self.set_font("Nanum", '', 12)
                else:
                    self.set_font("Arial", '', 12)
                    
            elif line.startswith("🔗"):
                self.set_text_color(0, 102, 204)  # 파란색
                if self.font_available:
                    self.set_font("Nanum", '', 12)
                else:
                    self.set_font("Arial", '', 12)
                self.multi_cell(0, 8, line)
                self.set_text_color(0, 0, 0)  # 검은색으로 복원
                
            else:
                if self.font_available:
                    self.set_font("Nanum", '', 12)
                else:
                    self.set_font("Arial", '', 12)
                self.multi_cell(0, 8, line)

def generate_pdf(content: str, filename="research_output.pdf") -> str:
    """PDF 생성 함수 - 에러 처리 강화"""
    try:
        pdf = PDF()
        pdf.write_content(content)
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = os.path.join(OUTPUT_DIR, filename)
        
        # PDF 저장
        pdf.output(path)
        print(f"✅ PDF 생성 완료: {path}")
        return path
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        # 에러가 나도 기본 경로 반환 (앱이 완전히 멈추지 않도록)
        return os.path.join(OUTPUT_DIR, filename)

from fpdf import FPDF
import os
import re
import warnings
from datetime import datetime

# 폰트 관련 경고 억제
warnings.filterwarnings("ignore", message="cmap value too big/small")
warnings.filterwarnings("ignore", category=UserWarning, module="fpdf")

# 폰트 경로
FONT_REGULAR = os.path.join("fonts", "NanumGothic-Regular.ttf")
FONT_BOLD = os.path.join("fonts", "NanumGothic-Bold.ttf")
FONT_EXTRABOLD = os.path.join("fonts", "NanumGothic-ExtraBold.ttf")
OUTPUT_DIR = "outputs"

class SafeKoreanPDF(FPDF):
    def __init__(self, topic=""):
        super().__init__(format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(20, 20, 20)
        self.topic = topic
        self.fonts_loaded = self.setup_fonts_safely()
        self.section_number = 0
        self.subsection_number = 0
        
    def setup_fonts_safely(self):
        """안전한 폰트 설정 (경고 최소화)"""
        try:
            print("폰트 설정 시작...")
            fonts_loaded = {}
            
            # 경고 임시 억제
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Regular 폰트 (필수)
                if os.path.exists(FONT_REGULAR):
                    try:
                        self.add_font('NanumRegular', '', FONT_REGULAR, uni=True)
                        fonts_loaded['regular'] = True
                        print("✅ Regular 폰트 로드 성공")
                    except Exception as e:
                        print(f"Regular 폰트 실패: {e}")
                        fonts_loaded['regular'] = False
                
                # Bold 폰트 (중요)
                if os.path.exists(FONT_BOLD):
                    try:
                        self.add_font('NanumBold', '', FONT_BOLD, uni=True)
                        fonts_loaded['bold'] = True
                        print("✅ Bold 폰트 로드 성공")
                    except Exception as e:
                        print(f"Bold 폰트 실패: {e}")
                        fonts_loaded['bold'] = False
                
                # ExtraBold는 선택사항 (실패해도 괜찮음)
                if os.path.exists(FONT_EXTRABOLD):
                    try:
                        self.add_font('NanumExtraBold', '', FONT_EXTRABOLD, uni=True)
                        fonts_loaded['extrabold'] = True
                        print("✅ ExtraBold 폰트 로드 성공")
                    except Exception as e:
                        print(f"ExtraBold 폰트 실패 (무시): {e}")
                        fonts_loaded['extrabold'] = False
            
            # 최소 Regular 폰트만 로드되면 성공
            success = fonts_loaded.get('regular', False)
            print(f"폰트 로딩 결과: {sum(fonts_loaded.values())}/3개, 사용 가능: {success}")
            
            return {
                'available': success,
                'regular': fonts_loaded.get('regular', False),
                'bold': fonts_loaded.get('bold', False),
                'extrabold': fonts_loaded.get('extrabold', False)
            }
                
        except Exception as e:
            print(f"폰트 설정 전체 실패: {e}")
            return {'available': False, 'regular': False, 'bold': False, 'extrabold': False}
    
    def set_safe_font(self, weight='regular', size=10):
        """안전한 폰트 설정"""
        try:
            if self.fonts_loaded['available']:
                if weight == 'extrabold' and self.fonts_loaded['extrabold']:
                    self.set_font('NanumExtraBold', size=size)
                elif weight == 'bold' and self.fonts_loaded['bold']:
                    self.set_font('NanumBold', size=size)
                elif self.fonts_loaded['regular']:
                    self.set_font('NanumRegular', size=size)
                else:
                    # 대체 폰트
                    self.set_font('Arial', 'B' if weight in ['bold', 'extrabold'] else '', size)
            else:
                # Arial 대체
                style = 'B' if weight in ['bold', 'extrabold'] else ''
                self.set_font('Arial', style, size)
        except Exception as e:
            print(f"폰트 설정 오류: {e}")
            # 최종 대체
            self.set_font('Arial', '', size)
    
    def header(self):
        """페이지 헤더"""
        if self.page_no() > 1:  # 첫 페이지 제외
            try:
                self.set_safe_font('regular', 9)
                self.set_text_color(120, 120, 120)
                self.cell(0, 10, f'{self.topic} - 연구보고서', align='R', ln=True)
                self.ln(3)
            except:
                pass
            
    def footer(self):
        """페이지 푸터"""
        try:
            self.set_y(-15)
            self.set_safe_font('regular', 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'- {self.page_no()} -', align='C')
        except:
            pass
    
    def add_title_page(self, topic):
        """표지 페이지 생성"""
        self.add_page()
        
        # 상단 여백
        self.ln(40)
        
        try:
            # 메인 제목
            self.set_safe_font('extrabold', 24)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 15, f'{topic}', align='C')
            self.ln(10)
            
            # 부제목
            self.set_safe_font('bold', 16)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 12, '연구 탐색 보고서', align='C')
            self.ln(40)
            
            # 생성 정보
            self.set_safe_font('regular', 12)
            sel

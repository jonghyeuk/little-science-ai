# utils/pdf_generator.py (개선된 버전)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, black, darkblue
import os
import re
import streamlit as st

# 출력 디렉토리
OUTPUT_DIR = "outputs"

class ImprovedPDFGenerator:
    def __init__(self):
        self.setup_fonts()
        self.setup_styles()
        
    def setup_fonts(self):
        """폰트 설정 - 더 안전한 방식"""
        self.font_loaded = False
        try:
            # 나눔고딕 폰트 경로들
            font_paths = [
                os.path.join("fonts", "NanumGothic-Regular.ttf"),
                os.path.join("fonts", "NanumGothic-Bold.ttf"),
                "NanumGothic.ttf",  # 시스템 폰트
                "/System/Library/Fonts/AppleGothic.ttf",  # macOS
                "C:/Windows/Fonts/malgun.ttf"  # Windows 맑은고딕
            ]
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                        self.font_loaded = True
                        print(f"✅ 폰트 로드 성공: {font_path}")
                        break
                except Exception as e:
                    print(f"폰트 로드 시도 실패: {font_path} - {e}")
                    continue
                    
            if not self.font_loaded:
                print("⚠️ 한글 폰트 로드 실패, 기본 폰트 사용")
                
        except Exception as e:
            print(f"폰트 설정 오류: {e}")
            self.font_loaded = False
    
    def setup_styles(self):
        """스타일 설정"""
        self.styles = getSampleStyleSheet()
        
        # 한글 폰트가 로드되었으면 사용, 아니면 기본 폰트
        font_name = 'NanumGothic' if self.font_loaded else 'Helvetica'
        
        # 커스텀 스타일 정의
        self.styles.add(ParagraphStyle(
            name='KoreanTitle',
            parent=self.styles['Title'],
            fontName=font_name,
            fontSize=18,
            spaceAfter=20,
            textColor=darkblue,
            alignment=1  # 중앙 정렬
        ))
        
        self.styles.add(ParagraphStyle(
            name='KoreanHeading1',
            parent=self.styles['Heading1'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            textColor=darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='KoreanHeading2',
            parent=self.styles['Heading2'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8,
            textColor=Color(0.2, 0.2, 0.6)
        ))
        
        self.styles.add(ParagraphStyle(
            name='KoreanNormal',
            parent=self.styles['Normal'],
            fontName=font_name,
            fontSize=10,
            spaceAfter=6,
            leading=14,
            textColor=black
        ))
    
    def clean_text(self, text):
        """텍스트 정리"""
        # 마크다운 문법 제거
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)  # **굵게** → <b>굵게</b>
        text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)      # *기울임* → <i>기울임</i>
        
        # 이모지 제거 (PDF에서 문제 될 수 있음)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 감정
            "\U0001F300-\U0001F5FF"  # 기호
            "\U0001F680-\U0001F6FF"  # 교통
            "\U0001F1E0-\U0001F1FF"  # 국기
            "]+", flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        
        # 특수 문자 처리
        text = text.replace('📘', '').replace('📄', '').replace('🌐', '')
        text = text.replace('🔬', '').replace('💡', '').replace('⚙️', '')
        
        return text.strip()
    
    def generate_pdf(self, content, filename="research_report.pdf"):
        """PDF 생성 메인 함수"""
        try:
            print("=== 개선된 PDF 생성 시작 ===")
            
            # 출력 디렉토리 생성
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, filename)
            
            # PDF 문서 생성
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # 스토리 리스트 (PDF 내용)
            story = []
            
            # 제목 추가
            title = Paragraph("🧪 LittleScienceAI 연구 보고서", self.styles['KoreanTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # 내용 파싱 및 추가
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                    continue
                
                # 제목 레벨 구분
                if line.startswith('# '):
                    # 메인 제목
                    clean_line = self.clean_text(line[2:])
                    para = Paragraph(clean_line, self.styles['KoreanHeading1'])
                    story.append(Spacer(1, 12))
                    story.append(para)
                    
                elif line.startswith('## '):
                    # 섹션 제목
                    clean_line = self.clean_text(line[3:])
                    para = Paragraph(clean_line, self.styles['KoreanHeading2'])
                    story.append(Spacer(1, 10))
                    story.append(para)
                    
                elif line.startswith('### '):
                    # 소제목
                    clean_line = self.clean_text(line[4:])
                    para = Paragraph(f"<b>{clean_line}</b>", self.styles['KoreanNormal'])
                    story.append(Spacer(1, 8))
                    story.append(para)
                    
                else:
                    # 일반 텍스트
                    if line.startswith('- '):
                        # 리스트 항목
                        clean_line = self.clean_text(line[2:])
                        para = Paragraph(f"• {clean_line}", self.styles['KoreanNormal'])
                    else:
                        clean_line = self.clean_text(line)
                        para = Paragraph(clean_line, self.styles['KoreanNormal'])
                    
                    story.append(para)
            
            # PDF 빌드
            doc.build(story)
            
            # 파일 검증
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"생성된 PDF 크기: {file_size} bytes")
                
                if file_size > 1000:  # 최소 1KB
                    print(f"✅ PDF 생성 성공: {output_path}")
                    return output_path
                else:
                    raise Exception(f"PDF 파일이 너무 작음 ({file_size} bytes)")
            else:
                raise Exception("PDF 파일이 생성되지 않음")
                
        except Exception as e:
            print(f"❌ PDF 생성 실패: {str(e)}")
            return self.fallback_text_export(content, filename)
    
    def fallback_text_export(self, content, filename):
        """PDF 실패시 텍스트 파일로 저장"""
        try:
            txt_filename = filename.replace('.pdf', '_backup.txt')
            txt_path = os.path.join(OUTPUT_DIR, txt_filename)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("=== LittleScienceAI 연구 보고서 ===\n")
                f.write("(PDF 생성 실패로 텍스트 버전 제공)\n")
                f.write("=" * 50 + "\n\n")
                f.write(content)
            
            print(f"✅ 텍스트 파일 저장: {txt_path}")
            return txt_path
            
        except Exception as txt_error:
            print(f"❌ 텍스트 파일 저장 실패: {txt_error}")
            return None

# 기존 함수와 호환성을 위한 래퍼
def generate_pdf(content, filename="research_report.pdf"):
    """기존 코드와 호환되는 함수"""
    generator = ImprovedPDFGenerator()
    return generator.generate_pdf(content, filename)

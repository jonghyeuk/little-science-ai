# utils/pdf_generator.py (기존 fpdf 기반 수정 버전)
from fpdf import FPDF
import os
import re
import streamlit as st

# 폰트 경로 (기존과 동일)
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
        """3가지 나눔고딕 폰트 안전하게 로드 - 개선된 버전"""
        try:
            fonts_count = 0
            
            print("=== 폰트 로딩 시작 ===")
            
            # 폰트 파일 존재 확인
            font_files = [
                ("Regular", FONT_REGULAR, 'NanumRegular'),
                ("Bold", FONT_BOLD, 'NanumBold'), 
                ("ExtraBold", FONT_EXTRABOLD, 'NanumExtraBold')
            ]
            
            for font_type, font_path, font_id in font_files:
                if os.path.exists(font_path):
                    try:
                        # 파일 크기 확인 (손상된 폰트 파일 걸러내기)
                        file_size = os.path.getsize(font_path)
                        if file_size < 1000:  # 1KB 미만이면 손상됨
                            print(f"⚠️ {font_type} 폰트 파일이 너무 작음: {file_size} bytes")
                            continue
                            
                        self.add_font(font_id, '', font_path, uni=True)
                        fonts_count += 1
                        print(f"✅ {font_type} 폰트 로드 성공: {font_path}")
                        
                    except Exception as font_error:
                        print(f"❌ {font_type} 폰트 로드 실패: {font_error}")
                        continue
                else:
                    print(f"❌ {font_type} 폰트 파일 없음: {font_path}")
            
            success = fonts_count >= 1  # 최소 1개만 있어도 OK
            print(f"=== 폰트 로딩 완료: {fonts_count}/3개 성공 ===")
            
            return success
                
        except Exception as e:
            print(f"❌ 전체 폰트 설정 오류: {e}")
            return False
    
    def header(self):
        """헤더 - 에러 처리 강화"""
        try:
            if self.fonts_loaded:
                self.set_font('NanumBold', size=14)
            else:
                self.set_font('Arial', 'B', 14)
            
            self.set_text_color(70, 70, 70)
            self.cell(0, 12, 'LittleScienceAI 연구 보고서', align='C', ln=True)
            self.ln(8)
            
        except Exception as e:
            print(f"헤더 생성 오류: {e}")
            # 기본 헤더라도 만들기
            try:
                self.set_font('Arial', 'B', 12)
                self.cell(0, 10, 'Research Report', align='C', ln=True)
                self.ln(5)
            except:
                pass
            
    def footer(self):
        """푸터 - 에러 처리 강화"""
        try:
            self.set_y(-15)
            
            if self.fonts_loaded:
                self.set_font('NanumRegular', size=9)
            else:
                self.set_font('Arial', '', 9)
            
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'페이지 {self.page_no()}', align='C')
            
        except Exception as e:
            print(f"푸터 생성 오류: {e}")
            try:
                self.set_font('Arial', '', 8)
                self.cell(0, 10, f'Page {self.page_no()}', align='C')
            except:
                pass
    
    def write_content(self, content):
        """안전한 내용 작성 - 개선된 버전"""
        try:
            self.add_page()
            
            if not content or len(content.strip()) == 0:
                self.add_normal_text("내용이 비어있습니다.")
                return
            
            lines = content.split('\n')
            print(f"📄 총 {len(lines)}줄 처리 시작")
            
            processed_lines = 0
            error_lines = 0
            
            for i, line in enumerate(lines):
                try:
                    line = line.strip()
                    
                    if not line:  # 빈 줄
                        self.ln(3)
                        continue
                    
                    # 제목별 처리 - 더 안전하게
                    if line.startswith('# '):
                        self.add_main_title(line[2:])
                    elif line.startswith('## '):
                        self.add_section_title(line[3:])
                    elif line.startswith('### '):
                        self.add_sub_title(line[4:])
                    else:
                        self.add_normal_text(line)
                        
                    processed_lines += 1
                    
                    # 진행상황 출력 (큰 문서의 경우)
                    if (i + 1) % 50 == 0:
                        print(f"📝 {i + 1}/{len(lines)} 줄 처리 완료")
                        
                except Exception as line_error:
                    error_lines += 1
                    print(f"❌ 라인 {i+1} 처리 오류: {line_error}")
                    print(f"   문제 라인: {repr(line[:100])}")
                    
                    # 에러가 너무 많으면 중단
                    if error_lines > 10:
                        print("⚠️ 에러가 너무 많아 처리를 중단합니다.")
                        break
                    
                    continue
            
            print(f"✅ 처리 완료: {processed_lines}줄 성공, {error_lines}줄 실패")
            
        except Exception as e:
            print(f"❌ 전체 콘텐츠 작성 오류: {e}")
            # 최소한의 내용이라도 추가
            try:
                self.add_normal_text("콘텐츠 처리 중 오류가 발생했습니다.")
            except:
                pass
    
    def add_main_title(self, title):
        """큰 제목 - 길이 제한 없음"""
        try:
            self.ln(8)
            
            if self.fonts_loaded:
                self.set_font('NanumExtraBold', size=16)
            else:
                self.set_font('Arial', 'B', 16)
            
            self.set_text_color(40, 40, 40)
            clean_title = self.clean_text(title)
            
            # 길이에 관계없이 multi_cell 사용
            self.multi_cell(0, 12, clean_title, align='L')
            self.ln(6)
            
        except Exception as e:
            print(f"메인 제목 오류: {e}")
            # 기본 제목이라도 표시
            try:
                self.set_font('Arial', 'B', 14)
                self.multi_cell(0, 10, title, align='L')
                self.ln(4)
            except:
                pass
    
    def add_section_title(self, title):
        """섹션 제목 - 길이 제한 없음"""
        try:
            self.ln(6)
            
            if self.fonts_loaded:
                self.set_font('NanumBold', size=13)
            else:
                self.set_font('Arial', 'B', 13)
            
            self.set_text_color(60, 60, 60)
            clean_title = self.clean_text(title)
            
            # 길이에 관계없이 multi_cell 사용
            self.multi_cell(0, 10, clean_title, align='L')
            self.ln(4)
            
        except Exception as e:
            print(f"섹션 제목 오류: {e}")
            try:
                self.set_font('Arial', 'B', 12)
                self.multi_cell(0, 8, title, align='L')
                self.ln(3)
            except:
                pass
    
    def add_sub_title(self, title):
        """소제목 - 길이 제한 없음"""
        try:
            self.ln(4)
            
            if self.fonts_loaded:
                self.set_font('NanumBold', size=11)
            else:
                self.set_font('Arial', 'B', 11)
            
            self.set_text_color(80, 80, 80)
            clean_title = self.clean_text(title)
            
            # 길이에 관계없이 multi_cell 사용
            self.multi_cell(0, 8, clean_title, align='L')
            self.ln(3)
            
        except Exception as e:
            print(f"소제목 오류: {e}")
            try:
                self.set_font('Arial', 'B', 10)
                self.multi_cell(0, 7, title, align='L')
                self.ln(2)
            except:
                pass
    
    def add_normal_text(self, text):
        """일반 텍스트 - 긴 텍스트 완전 지원"""
        try:
            if not text or len(text.strip()) == 0:
                return
                
            if self.fonts_loaded:
                self.set_font('NanumRegular', size=10)
            else:
                self.set_font('Arial', '', 10)
            
            self.set_text_color(90, 90, 90)
            clean_text = self.clean_text(text)
            
            if len(clean_text) > 0:
                # 긴 텍스트는 무조건 multi_cell 사용 (길이 제한 없음)
                self.multi_cell(0, 7, clean_text, align='L')
                self.ln(2)
                
        except Exception as e:
            print(f"일반 텍스트 오류: {e}")
            # 영어로라도 출력 시도 (길이 제한 늘림)
            try:
                self.set_font('Arial', '', 9)
                safe_text = text.encode('ascii', 'ignore').decode('ascii')
                if safe_text:
                    self.multi_cell(0, 6, safe_text, align='L')
                    self.ln(1)
            except:
                pass
    
    def clean_text(self, text):
        """텍스트 정리 - PDF용으로 깔끔하게"""
        try:
            if not text:
                return ""
            
            # 1단계: 불필요한 링크 정보 제거 (PDF에서는 클릭 안되니까)
            # 최신논문검색 섹션의 복잡한 링크들 간소화
            if "https://" in text and ("scholar.google.com" in text or "academic.naver.com" in text):
                # 링크가 많은 검색 가이드는 간단하게 요약
                text = "📚 추가 연구를 위한 검색 가이드\n\n관련 키워드로 Google Scholar, 네이버 학술정보, RISS, DBpia 등에서 논문을 검색해보세요."
            
            # URL 링크들 제거 (PDF에서는 의미없음)
            text = re.sub(r'https?://[^\s]+', '', text)
            
            # 2단계: 마크다운 기호 정리
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **굵게** → 굵게
            text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *기울임* → 기울임
            text = text.replace('**', '').replace('*', '')
            
            # 3단계: 이모지는 일부만 유지 (PDF에서 의미있는 것들)
            # 유지할 이모지들
            keep_emojis = ['📚', '🔍', '💡', '📊', '🎯', '📋']
            
            # 제거할 이모지들
            remove_emojis = ['📘', '📄', '🌐', '🔬', '⚙️', '🌍', '📈', '🏆', '📅', '🤖', '🧠']
            
            for emoji in remove_emojis:
                text = text.replace(emoji, '')
            
            # 4단계: 공백 정리
            text = re.sub(r'\s+', ' ', text)  # 연속 공백 제거
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # 과도한 줄바꿈 정리
            text = text.strip()
            
            return text
            
        except Exception as e:
            print(f"텍스트 정리 오류: {e}")
            try:
                # 기본적인 정리만
                clean = text.replace('**', '').replace('*', '')
                # URL만 제거
                clean = re.sub(r'https?://[^\s]+', '', clean)
                return clean.strip()
            except:
                return text if text else "[텍스트 처리 실패]"

def generate_pdf(content, filename="research_report.pdf"):
    """PDF 생성 메인 함수 - 개선된 버전"""
    try:
        print("=== PDF 생성 시작 ===")
        
        # 출력 디렉토리 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"출력 디렉토리: {OUTPUT_DIR}")
        
        # 내용 검증
        if not content or len(content.strip()) == 0:
            print("⚠️ 빈 내용으로 기본 PDF 생성")
            content = "# 연구 보고서\n\n내용이 생성되지 않았습니다.\n잠시 후 다시 시도해주세요."
        
        # PDF 생성
        pdf = SafeKoreanPDF()
        
        # 폰트 로딩 확인
        if not pdf.fonts_loaded:
            print("⚠️ 한글 폰트 없이 PDF 생성 (영어/숫자만 표시됨)")
            if 'st' in globals():
                st.warning("한글 폰트를 찾을 수 없어 일부 텍스트가 영어로 표시됩니다.")
        
        # 내용 작성
        pdf.write_content(content)
        
        # 저장
        output_path = os.path.join(OUTPUT_DIR, filename)
        pdf.output(output_path)
        
        # 파일 검증
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"생성된 파일 크기: {file_size:,} bytes")
            
            if file_size > 1000:  # 최소 1KB
                print(f"✅ PDF 생성 성공: {output_path}")
                return output_path
            else:
                print(f"⚠️ PDF 파일이 너무 작음 ({file_size} bytes)")
                raise Exception(f"PDF 파일 크기 이상: {file_size} bytes")
        else:
            raise Exception("PDF 파일이 생성되지 않음")
            
    except Exception as e:
        print(f"❌ PDF 생성 실패: {str(e)}")
        
        # 실패시 텍스트 파일로 저장
        return create_fallback_file(content, filename)

def create_fallback_file(content, filename):
    """PDF 실패시 텍스트 파일 생성"""
    try:
        txt_filename = filename.replace('.pdf', '_fallback.txt')
        txt_path = os.path.join(OUTPUT_DIR, txt_filename)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("LittleScienceAI 연구 보고서\n")
            f.write("(PDF 생성 실패로 텍스트 파일 제공)\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)
            f.write("\n\n" + "=" * 50)
            f.write("\n생성 시간: " + str(os.path.getctime))
        
        print(f"✅ 대체 텍스트 파일 생성: {txt_path}")
        
        if 'st' in globals():
            st.warning("PDF 생성에 실패하여 텍스트 파일로 저장됩니다.")
            
        return txt_path
        
    except Exception as txt_error:
        print(f"❌ 텍스트 파일 생성도 실패: {txt_error}")
        return None

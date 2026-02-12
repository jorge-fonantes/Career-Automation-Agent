import re
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

class PDFResumeBuilder:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # ESTILOS COMPACTOS (Para caber em 1 página)
        if 'JobTitleCustom' not in self.styles:
            self.styles.add(ParagraphStyle(name='JobTitleCustom', parent=self.styles['Heading3'], fontSize=10, textColor=colors.darkblue, spaceAfter=1, leading=12))
        if 'CompanyCustom' not in self.styles:
            self.styles.add(ParagraphStyle(name='CompanyCustom', parent=self.styles['BodyText'], fontSize=10, fontName='Helvetica-Bold', spaceAfter=1, leading=12))
        if 'BulletCustom' not in self.styles:
            self.styles.add(ParagraphStyle(name='BulletCustom', parent=self.styles['BodyText'], fontSize=9, bulletIndent=10, leftIndent=20, spaceAfter=1, leading=10))
        if 'CompactNormal' not in self.styles:
            self.styles.add(ParagraphStyle(name='CompactNormal', parent=self.styles['Normal'], fontSize=10, leading=12))

    def clean_text(self, text):
        if not text: return ""
        text_str = str(text)
        text_str = re.sub(r'\\', '', text_str)
        return " ".join(text_str.split())

    def build(self, data, filename, is_english=False):
        # Traduções de Cabeçalho
        headers = {
            "SUMMARY": "PROFESSIONAL SUMMARY" if is_english else "RESUMO PROFISSIONAL",
            "SKILLS": "TECHNICAL SKILLS" if is_english else "COMPETÊNCIAS TÉCNICAS",
            "EXP": "PROFESSIONAL EXPERIENCE" if is_english else "EXPERIÊNCIA PROFISSIONAL",
            "EDU": "EDUCATION" if is_english else "FORMAÇÃO ACADÊMICA",
            "HARD": "Hard Skills:" if is_english else "Hard Skills:",
            "SOFT": "Soft Skills:" if is_english else "Soft Skills:"
        }

        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)

        # Margens reduzidas para caber em 1 página
        doc = SimpleDocTemplate(filename, pagesize=A4,
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=30)
        story = []

        # 1. CABEÇALHO COMPACTO
        name = self.clean_text(data.get('name', 'JORGE LUCAS FONANTES')).upper()
        story.append(Paragraph(f"<b>{name}</b>", self.styles['Title']))
        
        contacts = [
            data['contact'].get('email', ''),
            data['contact'].get('phone', ''),
            data['contact'].get('location', '')
        ]
        story.append(Paragraph(" | ".join([c for c in contacts if c]), self.styles['CompactNormal']))
        
        links = f"LinkedIn: {data['contact'].get('linkedin', '')} | GitHub: {data['contact'].get('github', '')}"
        story.append(Paragraph(links, self.styles['CompactNormal']))
        
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 8))

        # 2. RESUMO
        story.append(Paragraph(headers["SUMMARY"], self.styles['Heading3']))
        summary = self.clean_text(data.get('selected_summary', ''))
        story.append(Paragraph(summary, self.styles['CompactNormal']))
        story.append(Spacer(1, 8))

        # 3. SKILLS
        story.append(Paragraph(headers["SKILLS"], self.styles['Heading3']))
        hard = ", ".join(data['skills'].get('hard', []))
        # Removemos Soft skills se precisar de espaço, ou mantemos em linha única
        story.append(Paragraph(f"<b>{headers['HARD']}</b> {self.clean_text(hard)}", self.styles['CompactNormal']))
        story.append(Spacer(1, 8))

        # 4. EXPERIÊNCIA (Limitada para caber)
        story.append(Paragraph(headers["EXP"], self.styles['Heading3']))
        
        seen_experiences = set()
        count_exp = 0
        
        for exp in data.get('sorted_experiences', []):
            if count_exp >= 4: break # Limita a 4 experiências mais recentes para garantir 1 página
            
            comp = self.clean_text(exp.get('company', ''))
            role = self.clean_text(exp.get('role', ''))
            key = f"{comp}-{role}"
            
            if key in seen_experiences or not comp: continue
            seen_experiences.add(key)
            count_exp += 1

            period = self.clean_text(exp.get('period', ''))
            story.append(Paragraph(f"{comp} | {period}", self.styles['CompanyCustom']))
            story.append(Paragraph(f"<i>{role}</i>", self.styles['JobTitleCustom']))
            
            bullets = exp.get('bullets', exp.get('raw_bullets', []))
            bullet_count = 0
            for b in bullets:
                if bullet_count >= 3: break # Máximo 3 bullets por vaga
                clean_b = self.clean_text(b)
                if len(clean_b) > 5:
                    story.append(Paragraph(f"• {clean_b}", self.styles['BulletCustom']))
                    bullet_count += 1
            
            story.append(Spacer(1, 4))

        # 5. FORMAÇÃO
        story.append(Paragraph(headers["EDU"], self.styles['Heading3']))
        for edu in data.get('education', []):
            inst = self.clean_text(edu.get('institution', ''))
            deg = self.clean_text(edu.get('degree', ''))
            story.append(Paragraph(f"<b>{inst}</b> - {deg}", self.styles['CompactNormal']))

        try:
            doc.build(story)
            return filename
        except Exception as e:
            print(f"Erro PDF: {e}")
            return None
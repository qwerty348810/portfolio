"""Build the public PDF and editable hh.ru exports from one factual source."""
from pathlib import Path
from html import escape
from io import BytesIO
import json
import os
import shutil
import zipfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((Path(__file__).parent/'resume.json').read_text(encoding='utf-8'))
EXPORT = ROOT/'.cache/resume-hh'
EXPORT.mkdir(parents=True, exist_ok=True)

font_candidates = [
    (Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/arial.ttf', Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/arialbd.ttf'),
    (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
]
regular, bold = next(((a,b) for a,b in font_candidates if a.exists() and b.exists()), (None,None))
if regular is None:
    raise RuntimeError('Install Arial or DejaVu Sans with Cyrillic support.')
pdfmetrics.registerFont(TTFont('Resume', str(regular)))
pdfmetrics.registerFont(TTFont('ResumeBold', str(bold)))
pdfmetrics.registerFontFamily('Resume', normal='Resume', bold='ResumeBold', italic='Resume', boldItalic='ResumeBold')
INK = colors.HexColor('#17263c')
ACCENT = colors.HexColor('#17668e')
MUTED = colors.HexColor('#526275')
styles = {
    'name': ParagraphStyle('name', fontName='ResumeBold', fontSize=25, leading=29, textColor=INK, spaceAfter=5),
    'title': ParagraphStyle('title', fontName='ResumeBold', fontSize=14, leading=18, textColor=ACCENT, spaceAfter=5),
    'sub': ParagraphStyle('sub', fontName='Resume', fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=5),
    'body': ParagraphStyle('body', fontName='Resume', fontSize=10, leading=13.5, textColor=INK, spaceAfter=5),
    'section': ParagraphStyle('section', fontName='ResumeBold', fontSize=10.7, leading=15, textColor=ACCENT, spaceBefore=13, spaceAfter=7, keepWithNext=True),
    'job': ParagraphStyle('job', fontName='ResumeBold', fontSize=10.5, leading=14, textColor=INK, spaceAfter=2, keepWithNext=True),
    'meta': ParagraphStyle('meta', fontName='Resume', fontSize=9, leading=12, textColor=MUTED, spaceAfter=5, keepWithNext=True),
    'bullet': ParagraphStyle('bullet', fontName='Resume', fontSize=9.7, leading=13, textColor=INK, leftIndent=10, firstLineIndent=-10, spaceAfter=4),
    'small': ParagraphStyle('small', fontName='Resume', fontSize=9.4, leading=12.5, textColor=INK, spaceAfter=4),
}
story=[]
def para(text, style='body'):
    return Paragraph(text, styles[style])
def add(text, style='body'):
    story.append(para(text, style))
def section(text):
    add(escape(text), 'section')
def bullet(text):
    add('• '+escape(text), 'bullet')
def link(url, label):
    return f'<link href="{escape(url,quote=True)}" color="#17668e">{escape(label)}</link>'
def job(item):
    story.append(KeepTogether([
        para(escape(item['role']), 'job'),
        para(escape(item['company'])+' · '+escape(item['period']), 'meta'),
    ]))
    for text in item['bullets']:
        bullet(text)

add(escape(DATA['name']), 'name')
add(escape(DATA['title']), 'title')
add(escape(DATA['subtitle']), 'sub')
add(escape(DATA['city'])+' · '+link('mailto:'+DATA['email'],DATA['email'])+' · '+link('tel:+375298555596',DATA['phone']), 'sub')
add(link(DATA['portfolio'],'dmitryyakovlev.by')+' · '+link(DATA['telegram'],'Telegram: DmitrYakovlevDev'), 'sub')
section('ПРОФИЛЬ')
for text in DATA['profile']:
    add(escape(text))
section('КЛЮЧЕВЫЕ НАВЫКИ')
for skill in DATA['skills']:
    add('<b>'+escape(skill['label'])+'.</b> '+escape(skill['value']), 'small')
section('ОПЫТ РАБОТЫ')
job(DATA['experience'][0])
add('<b>Дополнительно — автоматизация и интеграции:</b>', 'small')
for text in DATA['experience'][0]['additional']:
    bullet(text)

story.append(PageBreak())
add(escape(DATA['name']+' · '+DATA['title']), 'job')
section('ПРЕДЫДУЩИЙ ОПЫТ')
for item in DATA['experience'][1:]:
    job(item)
    story.append(Spacer(1,6))
section('ВЫБРАННЫЕ СОБСТВЕННЫЕ ПРОЕКТЫ')
for item in DATA['projects']:
    story.append(KeepTogether([
        para(link(item['url'],item['name']), 'job'),
        para(escape(item['description']), 'small'),
    ]))
    story.append(Spacer(1,6))
section('ОБРАЗОВАНИЕ И КУРСЫ')
for text in DATA['education']:
    add(escape(text), 'small')
section('ЯЗЫКИ')
add(escape(DATA['languages']), 'small')
add(escape(DATA['demo']), 'small')

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#d8e0e9'))
    canvas.line(40,31,A4[0]-40,31)
    canvas.setFont('Resume',8)
    canvas.setFillColor(MUTED)
    canvas.drawString(40,18,DATA['name']+' · '+DATA['title'])
    canvas.drawRightString(A4[0]-40,18,str(doc.page))
    canvas.restoreState()

doc=SimpleDocTemplate(str(ROOT/'resume.pdf'), pagesize=A4, rightMargin=40,leftMargin=40,topMargin=35,bottomMargin=43,
    title=DATA['name']+' — '+DATA['title'],author=DATA['name'],subject='Автоматизация тестирования, Playwright, TypeScript, REST API',
    pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
shutil.copy2(ROOT/'resume.pdf',EXPORT/'Резюме_hh_Дмитрий_Яковлев.pdf')

# The hh.ru text keeps field boundaries explicit and projects below paid work.
sections=[]
def hh_heading(title):
    sections.append((title, 'heading'))
def hh_text(text):
    sections.append((text, 'normal'))
hh_heading(DATA['name'])
hh_heading('Желаемая должность')
hh_text(DATA['title'])
hh_heading('Контакты')
for text in [DATA['city'],DATA['phone'],DATA['email'],DATA['telegram'],DATA['portfolio']]:
    hh_text(text)
hh_heading('Обо мне')
for text in DATA['profile']:
    hh_text(text)
hh_text(DATA['demo'])
hh_heading('Ключевые навыки')
hh_text('Playwright; TypeScript; JavaScript; REST API; тест-дизайн; E2E; регрессионное тестирование; приёмочное тестирование; GitHub Actions; YouTrack; Postman; DevTools; Git; SQL; Node.js; Python; Claude Code; Codex; Android-эмуляторы; iOS-симуляторы; TestFlight.')
hh_heading('Опыт работы')
for item in DATA['experience']:
    hh_heading(item['company'])
    hh_text(item['period']+((' · '+item['city']) if item['city'] else ''))
    hh_text(item['role'])
    if item.get('official_role'):
        hh_text(item['official_role'])
    for text in item['bullets']:
        hh_text('— '+text)
    if item.get('additional'):
        hh_text('Дополнительное направление — автоматизация и интеграции:')
        for text in item['additional']:
            hh_text('— '+text)
hh_heading('Собственные проекты и портфолио')
for item in DATA['projects']:
    hh_heading(item['name'])
    hh_text(item['description'])
    hh_text(item['url'])
hh_text('Полное портфолио: '+DATA['portfolio'])
hh_heading('Образование и курсы')
for text in DATA['education']:
    hh_text(text)
hh_heading('Языки')
hh_text(DATA['languages'])
(EXPORT/'Резюме_hh_по_разделам.txt').write_text('\n\n'.join(x[0] for x in sections)+'\n',encoding='utf-8-sig')

# A minimal, editable OOXML document without macros or external resources.
def word_p(text,heading=False):
    style='Heading1' if heading else 'Normal'
    return '<w:p><w:pPr><w:pStyle w:val="'+style+'"/></w:pPr><w:r><w:t xml:space="preserve">'+escape(text)+'</w:t></w:r></w:p>'
document='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+''.join(word_p(text,style=='heading') for text,style in sections)+'''<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="850" w:right="850" w:bottom="850" w:left="850"/></w:sectPr></w:body></w:document>'''
types='''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
rels='''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
docrels='''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
word_styles='''<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:sz w:val="21"/><w:lang w:val="ru-RU"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="100" w:line="260" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="100"/></w:pPr><w:rPr><w:b/><w:color w:val="17668E"/><w:sz w:val="24"/></w:rPr></w:style></w:styles>'''
with zipfile.ZipFile(EXPORT/'Резюме_hh_Дмитрий_Яковлев.docx','w',zipfile.ZIP_DEFLATED) as archive:
    for name,content in {'[Content_Types].xml':types,'_rels/.rels':rels,'word/document.xml':document,'word/_rels/document.xml.rels':docrels,'word/styles.xml':word_styles}.items():
        archive.writestr(name,content.encode('utf-8'))
print('Built resume.pdf and hh.ru PDF, TXT, DOCX exports.')

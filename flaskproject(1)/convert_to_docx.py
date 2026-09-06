#!/usr/bin/env python3
"""将演示演讲稿.md 转换为论文格式的 Word 文档"""
import re
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, color):
    """设置单元格底色"""
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), color)
    shading_elm.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_run_font(run, font_name_cn, font_name_en, size_pt, bold=False, color=None):
    """统一设置 run 字体"""
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.font.name = font_name_en
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:eastAsia'), font_name_cn)
    rFonts.set(qn('w:ascii'), font_name_en)
    rFonts.set(qn('w:hAnsi'), font_name_en)
    rPr.insert(0, rFonts)
    if color:
        run.font.color.rgb = RGBColor(*color)

def add_paragraph_with_style(doc, text, font_cn, font_en, size, bold=False,
                              alignment=None, space_before=0, space_after=0,
                              first_line_indent=None, color=None):
    """添加一个格式化段落"""
    p = doc.add_paragraph()
    if alignment is not None:
        p.alignment = alignment
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    if first_line_indent:
        pf.first_line_indent = Cm(first_line_indent)

    run = p.add_run(text)
    set_run_font(run, font_cn, font_en, size, bold, color)
    return p

def add_mixed_paragraph(doc, segments, alignment=None, space_before=0, space_after=0,
                         first_line_indent=None):
    """添加含多种格式的段落。segments = [(text, font_cn, font_en, size, bold, color), ...]"""
    p = doc.add_paragraph()
    if alignment is not None:
        p.alignment = alignment
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.5
    if first_line_indent:
        pf.first_line_indent = Cm(first_line_indent)

    for seg in segments:
        text, font_cn, font_en, size, bold, color = seg
        run = p.add_run(text)
        set_run_font(run, font_cn, font_en, size, bold, color)
    return p

def parse_bold_inline(text):
    """解析行内 **bold**，返回 segments 列表"""
    segments = []
    pattern = re.compile(r'\*\*(.+?)\*\*')
    last_end = 0
    for m in pattern.finditer(text):
        if m.start() > last_end:
            segments.append((text[last_end:m.start()], '宋体', 'Times New Roman', 12, False, None))
        segments.append((m.group(1), '黑体', 'Times New Roman', 12, True, None))
        last_end = m.end()
    if last_end < len(text):
        segments.append((text[last_end:], '宋体', 'Times New Roman', 12, False, None))
    return segments if segments else [(text, '宋体', 'Times New Roman', 12, False, None)]


def main():
    doc = Document()

    # --- 页面设置 ---
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    # ── 读取 md 文件 ──
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(script_dir, 'flaskproject', '演示演讲稿.md')
    output_path = os.path.join(script_dir, 'flaskproject', '演示演讲稿_论文格式.docx')
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # ========== 主标题 # ==========
        if line.startswith('# ') and not line.startswith('## '):
            text = line[2:].strip()
            add_paragraph_with_style(doc, text,
                font_cn='黑体', font_en='Times New Roman', size=22, bold=True,
                alignment=WD_ALIGN_PARAGRAPH.CENTER, space_before=24, space_after=18)
            i += 1
            continue

        # ========== 分隔线 --- ==========
        if line.strip() == '---':
            # 添加一条细线
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), '999999')
            pBdr.append(bottom)
            pPr.append(pBdr)
            i += 1
            continue

        # ========== 二级标题 ## ==========
        if line.startswith('## ') and not line.startswith('### '):
            text = line[3:].strip()
            add_paragraph_with_style(doc, text,
                font_cn='黑体', font_en='Times New Roman', size=16, bold=True,
                space_before=18, space_after=10)
            i += 1
            continue

        # ========== 三级标题 ### ==========
        if line.startswith('### '):
            text = line[4:].strip()
            add_paragraph_with_style(doc, text,
                font_cn='黑体', font_en='Times New Roman', size=14, bold=True,
                space_before=12, space_after=8)
            i += 1
            continue

        # ========== 引用块 > ==========
        if line.startswith('> '):
            quote_text = line[2:].strip()
            # 楷体, 灰色, 左侧缩进
            add_paragraph_with_style(doc, '▎' + quote_text,
                font_cn='楷体', font_en='Times New Roman', size=11, bold=False,
                space_before=2, space_after=2, color=(100, 100, 100))
            # 左缩进
            doc.paragraphs[-1].paragraph_format.left_indent = Cm(1.0)
            i += 1
            continue

        # ========== 表格行 | ... | ==========
        if line.startswith('|') and line.endswith('|'):
            # 收集整个表格
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1

            # 跳过表头分隔行（|---|---|）
            clean_lines = [l for l in table_lines if not re.match(r'^\|[\s\-:]+\|', l)]
            if not clean_lines:
                continue

            num_cols = len(clean_lines[0].split('|')) - 2  # 去掉首尾空的
            table = doc.add_table(rows=len(clean_lines), cols=num_cols)
            table.style = 'Table Grid'
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            for ri, tl in enumerate(clean_lines):
                cells = [c.strip() for c in tl.split('|')[1:-1]]
                for ci, cell_text in enumerate(cells):
                    if ci >= num_cols:
                        break
                    cell = table.rows[ri].cells[ci]
                    cell.text = ''
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run(cell_text)
                    if ri == 0:
                        set_run_font(run, '黑体', 'Times New Roman', 10, True)
                        set_cell_shading(cell, '2B579A')
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    else:
                        set_run_font(run, '宋体', 'Times New Roman', 10, False)
                        if ri % 2 == 0:
                            set_cell_shading(cell, 'F2F6FC')

            # 表格后空行
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            continue

        # ========== 编号列表项 - ==========
        if line.startswith('- ') or re.match(r'^\d+\.\s', line):
            text = re.sub(r'^[\-\d\.]+\s+', '', line).strip()
            segments = parse_bold_inline(text)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.5)
            p.paragraph_format.first_line_indent = Cm(-0.5)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.5

            # 前面加项目符号
            bullet_run = p.add_run('• ')
            set_run_font(bullet_run, '宋体', 'Times New Roman', 12, False)

            for seg in segments:
                t, fc, fe, s, b, c = seg
                run = p.add_run(t)
                set_run_font(run, fc, fe, s, b, c)
            i += 1
            continue

        # ========== 空行 ==========
        if line.strip() == '':
            i += 1
            continue

        # ========== 普通正文 ==========
        segments = parse_bold_inline(line.strip())
        if segments:
            add_mixed_paragraph(doc, segments,
                space_before=3, space_after=3, first_line_indent=0.74)
        i += 1

    # ── 保存 ──
    doc.save(output_path)
    print(f'已生成: {output_path}')
    print('   格式说明:')
    print('   - 论文标题: 黑体 二号(22pt) 居中')
    print('   - 一级标题: 黑体 三号(16pt) 加粗')
    print('   - 二级标题: 黑体 四号(14pt) 加粗')
    print('   - 正文内容: 宋体 小四(12pt) 1.5倍行距 首行缩进')
    print('   - 操作提示: 楷体 五号(11pt) 灰色 左缩进')
    print('   - 表格表头: 黑体 五号(10pt) 深蓝底白字')
    print('   - 表格内容: 宋体 五号(10pt) 隔行浅蓝底')

if __name__ == '__main__':
    main()

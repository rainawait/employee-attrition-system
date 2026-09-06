"""PDF 报告导出 —— 封面页 + 页眉页脚 + 图表内容"""
import os
from fpdf import FPDF

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'reports'))


class ReportPDF(FPDF):
    """自定义 PDF：封面页 + 带页眉页脚的内容页"""

    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=25)
        self.has_cover = False
        # 注册中文字体（SimHei）
        font_path = 'C:/Windows/Fonts/simhei.ttf'
        if os.path.exists(font_path):
            self.add_font('zh', '', font_path, uni=True)
            self.add_font('zh', 'B', font_path, uni=True)

    def header(self):
        if self.page_no() == 1:
            return
        fz = 'zh' if os.path.exists('C:/Windows/Fonts/simhei.ttf') else 'Helvetica'
        self.set_font(fz, '', 8)
        self.set_text_color(120, 120, 120)
        self.cell(95, 6, '员工离职综合分析报告', align='L')
        from datetime import datetime
        self.set_font('Helvetica', '', 8)
        self.cell(0, 6, datetime.now().strftime('%Y-%m-%d'), align='R', new_x="LMARGIN", new_y="NEXT")
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-20)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no() - 1} / {{nb}}', align='C')


def export_pdf(app, filters=None, save_path=None):
    """生成带封面、页眉、页脚的 PDF 报告"""
    from report.generate_analysis_report import generate
    from datetime import datetime

    # 先生成 PNG 报告图表
    png_path = generate(app, filters=filters)

    pdf = ReportPDF()
    pdf.alias_nb_pages()

    # ========== 封面页 ==========
    pdf.add_page()
    pdf.has_cover = True
    # 顶部装饰线
    pdf.set_fill_color(64, 158, 255)
    pdf.rect(0, 0, 210, 6, 'F')
    # 主标题（中文用 zh 字体）
    pdf.ln(55)
    font_zh = 'zh' if os.path.exists('C:/Windows/Fonts/simhei.ttf') else 'Helvetica'
    pdf.set_font(font_zh, 'B', 28)
    pdf.set_text_color(27, 58, 92)
    pdf.cell(0, 14, '员工离职综合分析报告', align='C', new_x="LMARGIN", new_y="NEXT")
    # 分隔线
    pdf.ln(8)
    pdf.set_draw_color(64, 158, 255)
    pdf.set_line_width(0.6)
    pdf.line(55, pdf.get_y(), 155, pdf.get_y())
    pdf.ln(10)
    # 副标题
    pdf.set_font(font_zh, '', 14)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(0, 10, f'生成日期：{datetime.now().strftime("%Y 年 %m 月 %d 日")}', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(14)
    # 筛选条件摘要
    if filters:
        parts = []
        if filters.get('departments'):
            parts.append('部门：' + ', '.join(filters['departments']))
        risk_map = {'high': '高风险', 'mid': '中风险', 'low': '低风险'}
        if filters.get('risk_level'):
            parts.append('风险：' + risk_map.get(filters['risk_level'], filters['risk_level']))
        if filters.get('date_start') or filters.get('date_end'):
            parts.append(f"{filters.get('date_start','')} ~ {filters.get('date_end','')}")
        if filters.get('compare_mode'):
            parts.append('环比对比')
        if parts:
            pdf.set_font(font_zh, '', 10)
            pdf.set_text_color(140, 140, 160)
            pdf.cell(0, 8, '筛选条件：' + '  |  '.join(parts), align='C', new_x="LMARGIN", new_y="NEXT")
    # 公司名 & 水印
    pdf.ln(35)
    pdf.set_font(font_zh, '', 12)
    pdf.set_text_color(160, 160, 170)
    pdf.cell(0, 10, 'XX 公司', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_zh, '', 8)
    pdf.cell(0, 6, '内部资料 - 仅限 HR 部门使用', align='C')

    # ========== 内容页 ==========
    pdf.add_page()
    # 图片限高，确保不溢出到额外页面（页眉~25 + 页脚~20 + 说明~20）
    max_img_h = 297 - 25 - 20 - 20  # 232mm
    img_w = 180
    img_h = min(max_img_h, img_w * (11.69 / 8.27))  # A4 比例
    pdf.image(png_path, x=(210 - img_w) / 2, y=25, w=img_w, h=img_h)

    # 正文说明
    pdf.set_y(25 + img_h + 4)
    pdf.set_font(font_zh, '', 9)
    pdf.set_text_color(100, 100, 110)
    pdf.multi_cell(0, 5,
        '说明：本报告基于员工历史数据与机器学习预测模型自动生成。'
        '部门离职率对比柱状图展示各部门离职比例，玫瑰图展示离职员工岗位分布，'
        '折线图反映各年龄段离职趋势。结论与建议部分为系统自动分析结果，供 HR 决策参考。')

    # ===== 保存 =====
    os.makedirs(REPORT_DIR, exist_ok=True)
    if save_path is None:
        save_path = os.path.join(REPORT_DIR, 'analysis_report.pdf')
    pdf.output(save_path)
    return save_path

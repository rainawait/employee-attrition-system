"""
根据 04-项目文档.docx 生成 PPT（含截图）
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

IMG_DIR = r'C:\Users\ASUS\OneDrive\Desktop\_ppt_images'

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ===== 颜色 =====
DARK_BG = RGBColor(0x1A, 0x23, 0x32)
ACCENT = RGBColor(0x00, 0x96, 0x88)
BLUE = RGBColor(0x40, 0x9E, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xB0, 0xB8, 0xC4)
SUB_BG = RGBColor(0x1E, 0x2A, 0x3A)

def add_slide(bg=DARK_BG):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    if bg:
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = bg
    return s

def add_tb(slide, left, top, width, height, text, size=18, color=WHITE, bold=False, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = 'Microsoft YaHei'
    p.alignment = align
    return tf

def add_shape(slide, st, left, top, width, height, fill=None, line=None, lw=None):
    shape = slide.shapes.add_shape(st, Inches(left), Inches(top), Inches(width), Inches(height))
    if fill:
        shape.fill.solid(); shape.fill.fore_color.rgb = fill
    else: shape.fill.background()
    if line:
        shape.line.color.rgb = line
        if lw: shape.line.width = Pt(lw)
    else: shape.line.fill.background()
    return shape

def add_deco(slide, l, t, w, c=ACCENT):
    shape = add_shape(slide, MSO_SHAPE.RECTANGLE, l, t, w, 0.05, fill=c)
    shape.line.fill.background()

def page_num(slide, n):
    add_tb(slide, 12.2, 7.15, 1, 0.3, str(n), size=10, color=LIGHT_GRAY, align=PP_ALIGN.RIGHT)

def sec_hdr(slide, n, title, sub=''):
    add_tb(slide, 0.6, 0.3, 2, 0.8, f'{n:02d}', size=60, color=ACCENT, bold=True)
    add_deco(slide, 0.6, 1.15, 2.2)
    add_tb(slide, 0.6, 1.35, 10, 1, title, size=34, bold=True)
    if sub:
        add_tb(slide, 0.6, 2.1, 10, 0.5, sub, size=15, color=LIGHT_GRAY)

def add_items(slide, left, top, width, height, items, title=None, tsize=28, isize=16):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame; tf.word_wrap = True
    if title:
        p = tf.paragraphs[0]
        p.text = title; p.font.size = Pt(tsize); p.font.color.rgb = ACCENT
        p.font.bold = True; p.font.name = 'Microsoft YaHei'
        p.space_after = Pt(8)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if (i==0 and not title) else tf.add_paragraph()
        p.text = item; p.font.size = Pt(isize); p.font.color.rgb = WHITE
        p.font.name = 'Microsoft YaHei'; p.space_after = Pt(3)

def add_card(slide, x, y, w, h, title, desc, tc=ACCENT):
    shape = add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=RGBColor(0x22, 0x2F, 0x40), line=RGBColor(0x33, 0x44, 0x55))
    tf = shape.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = title; p.font.size = Pt(17); p.font.color.rgb = tc
    p.font.bold = True; p.font.name = 'Microsoft YaHei'
    p2 = tf.add_paragraph(); p2.text = desc; p2.font.size = Pt(12)
    p2.font.color.rgb = LIGHT_GRAY; p2.font.name = 'Microsoft YaHei'

# ============ 图片映射：章节 → 图片文件列表 ============
img_map = {}
for f in sorted(os.listdir(IMG_DIR)):
    if f.endswith(('.png','.jpg','.jpeg','.gif')):
        num = int(f.split('_')[2].split('.')[0])
        img_map.setdefault(num, []).append(f)

# 找出每个章节对应的图片范围
section_images = {
    '4.1 用户管理': [],
    '4.2 员工管理': [],
    '4.3 离职预测': [],
    '4.4 报告管理': [],
    '4.5 干预跟踪': [],
    '4.6 操作日志': [],
    '4.7 数据看板': [],
    'ER图': [],
}
# 按段落号分: 0-150=ER/序, 151-170=4.1, 171-190=4.2, 191-205=4.3, 206-220=4.4, 221-240=4.5, 241-255=4.6, 256+ =4.7
for num, files in img_map.items():
    if num < 150: section_images['ER图'].extend(files)
    elif num < 171: section_images['4.1 用户管理'].extend(files)
    elif num < 191: section_images['4.2 员工管理'].extend(files)
    elif num < 206: section_images['4.3 离职预测'].extend(files)
    elif num < 221: section_images['4.4 报告管理'].extend(files)
    elif num < 241: section_images['4.5 干预跟踪'].extend(files)
    elif num < 256: section_images['4.6 操作日志'].extend(files)
    else: section_images['4.7 数据看板'].extend(files)

def add_screenshots(slide, key, max_per_row=3):
    """在幻灯片下半部分排列截图，与上方文字不重叠"""
    files = section_images.get(key, [])
    if not files:
        add_tb(slide, 1, 6.5, 11, 0.5, '(此处插入项目运行截图)', size=14, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)
        return

    n = len(files)
    if n == 0: return

    # 图片区域: 从 y=3.3 到 y=7.0, 避开上方文字
    avail_w = 11.8
    avail_h = 3.5
    start_y = 3.3
    start_x = 0.75

    # 动态计算行列
    if n <= 2:
        cols = n; rows = 1
    elif n <= 4:
        cols = 2; rows = (n + 1) // 2
    else:
        cols = max_per_row; rows = (n + cols - 1) // cols

    cell_w = avail_w / cols
    cell_h = min(avail_h / rows, cell_w * 0.7)  # 保持宽高比

    for i, fname in enumerate(files):
        row = i // cols
        col = i % cols
        x = start_x + col * cell_w
        y = start_y + row * cell_h

        pad = 0.08
        fpath = os.path.join(IMG_DIR, fname)
        try:
            slide.shapes.add_picture(fpath, Inches(x + pad), Inches(y + pad),
                                     Inches(cell_w - 2*pad), Inches(cell_h - 2*pad))
        except:
            pass

TOTAL = 18

# ===== Slide 1: 封面 =====
s = add_slide()
add_tb(s, 1, 1.5, 11, 1.5, '员工离职预警系统', size=52, bold=True, align=PP_ALIGN.CENTER)
add_tb(s, 1, 3.0, 11, 0.8, 'Employee Attrition Prediction System', size=20, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)
add_deco(s, 5, 3.9, 3.3)
add_tb(s, 1, 4.3, 11, 0.8, '基于 Flask + 机器学习的企业离职风险管理平台', size=22, color=ACCENT, align=PP_ALIGN.CENTER)
add_tb(s, 1, 5.5, 11, 0.6, '项目答辩汇报', size=16, color=LIGHT_GRAY, align=PP_ALIGN.CENTER)
page_num(s, 1)

# ===== Slide 2: 目录 =====
s = add_slide()
sec_hdr(s, 0, '目录', 'CONTENTS')
add_items(s, 1.5, 2.8, 9, 4.5, [
    '01  项目背景',
    '02  需求分析',
    '03  系统设计',
    '04  系统实施 — 各模块截图演示',
    '05  系统测试',
    '06  总结与展望',
], isize=22)
page_num(s, 2)

# ===== Slide 3: 项目背景 =====
s = add_slide()
sec_hdr(s, 1, '项目背景', 'BACKGROUND')
add_items(s, 0.8, 3.0, 11, 3.5, [
    '● 员工流失是企业 HR 管理的核心挑战 —— 招聘成本高、团队不稳定',
    '● 传统离职管理依赖经验判断，缺乏数据驱动的科学决策支持',
    '● 基于 IBM HR Analytics 数据集（1470 条记录，34 维特征）',
    '● 构建"风险预测 → 干预处理 → 效果评估"的完整业务闭环',
], isize=20)
techs = ['Flask', 'SQLAlchemy', 'SQLite', 'Layui', 'ECharts',
         'scikit-learn', 'Pandas', 'Matplotlib', 'Playwright']
for i, t in enumerate(techs):
    x = 0.8 + (i%5)*2.4; y = 5.5 + (i//5)*0.7
    sh = add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, 2.0, 0.5, fill=RGBColor(0x2C,0x3E,0x50), line=ACCENT, lw=1.5)
    tf = sh.text_frame; p = tf.paragraphs[0]
    p.text = t; p.font.size = Pt(14); p.font.color.rgb = ACCENT
    p.font.name = 'Consolas'; p.alignment = PP_ALIGN.CENTER
page_num(s, 3)

# ===== Slide 4: 功能需求 =====
s = add_slide()
sec_hdr(s, 2, '需求分析 — 功能性需求', 'FUNCTIONAL')
funcs = [
    ('用户管理', '注册/登录/角色/头像'), ('员工管理', 'CRUD/搜索/三表联动'),
    ('离职预测', '单+批量/LR+RF集成'), ('风险排名', '降序排列/AI分析'),
    ('离职洞察', '雷达图对比'), ('报告管理', 'PNG/Excel/PDF/邮件'),
    ('干预跟踪', '干预/时间线/效果'), ('操作日志', '12埋点/查询/清理'),
]
for i, (t,d) in enumerate(funcs):
    x = 0.7 + (i%2)*6.3; y = 2.7 + (i//2)*1.15
    add_card(s, x, y, 5.8, 1.0, t, d, ACCENT)
page_num(s, 4)

# ===== Slide 5: 非功能需求 =====
s = add_slide()
sec_hdr(s, 2, '需求分析 — 非功能性需求', 'NON-FUNCTIONAL')
nfrs = [
    ('⚡ 性能', '单预测<3s / 批量<30s / 加载<2s'),
    ('🔒 安全', 'Session认证 / 密码哈希 / IP追溯'),
    ('🖥 可用性', 'Layui响应式 / 主流浏览器 / 校验反馈'),
    ('📦 可维护', 'Blueprint模块化 / 工具函数封装'),
    ('🔗 兼容性', 'Win10/11 / Python3.10+ / SQLite可迁MySQL'),
]
for i, (t,d) in enumerate(nfrs):
    add_card(s, 0.8, 2.8+i*0.9, 11.5, 0.75, t, d, ACCENT)
page_num(s, 5)

# ===== Slide 6: 系统架构 =====
s = add_slide()
sec_hdr(s, 3, '系统设计 — 架构 & 模块', 'ARCHITECTURE')
for i, (n, d, c) in enumerate([
    ('表现层', 'Layui + ECharts + jQuery', '#e74c3c'),
    ('路由层', 'Flask + Blueprint (4蓝图)', '#e67e22'),
    ('业务层', 'ML模型 / 报告 / 日志 / 邮件', '#f39c12'),
    ('数据层', 'SQLAlchemy ORM + SQLite', '#27ae60'),
]):
    cr = RGBColor(int(c[1:3],16),int(c[3:5],16),int(c[5:7],16))
    sh = add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 1.5, 2.6+i*1.15, 10, 1.0, fill=RGBColor(0x22,0x2F,0x40), line=cr, lw=2)
    tf = sh.text_frame
    p=tf.paragraphs[0];p.text=n;p.font.size=Pt(18);p.font.color.rgb=cr;p.font.bold=True;p.font.name='Microsoft YaHei'
    p2=tf.add_paragraph();p2.text=d;p2.font.size=Pt(14);p2.font.color.rgb=LIGHT_GRAY;p2.font.name='Microsoft YaHei'
    if i<3: add_tb(s, 6.2, 3.4+i*1.15, 1, 0.4, '▼', size=18, color=cr, align=PP_ALIGN.CENTER)
page_num(s, 6)

# ===== Slide 7: 功能模块 =====
s = add_slide()
sec_hdr(s, 3, '系统设计 — 功能模块', 'MODULES')
mods = [('👤用户管理','注册/登录/角色/头像'),('👨‍💼员工管理','CRUD/搜索/三表联动'),
         ('🔮离职预测','单+批量/AI/洞察'),('📊报告管理','PNG/Excel/PDF/邮件'),
         ('🩺干预跟踪','干预/时间线/效果'),('📝操作日志','埋点/查询/清理'),
         ('📈数据看板','KPI/图表/预警')]
clrs = [RGBColor(0xE7,0x4C,0x3C),RGBColor(0xE6,0x7E,0x22),RGBColor(0xF3,0x9C,0x12),RGBColor(0x27,0xAE,0x60),
        RGBColor(0x34,0x98,0xDB),RGBColor(0x9B,0x59,0xB6),RGBColor(0x00,0x96,0x88)]
for i,(nm,desc) in enumerate(mods):
    ic = nm[0]  # emoji
    nm = nm[1:]  # name
    x=1.2+(i%4)*3.0; y=2.7+(0 if i<4 else 1)*2.3
    sh=add_shape(s,MSO_SHAPE.ROUNDED_RECTANGLE,x,y,2.6,2.0,fill=RGBColor(0x22,0x2F,0x40),line=clrs[i],lw=1.5)
    tf=sh.text_frame;tf.word_wrap=True
    p=tf.paragraphs[0];p.text=ic;p.font.size=Pt(28);p.alignment=PP_ALIGN.CENTER
    p2=tf.add_paragraph();p2.text=nm;p2.font.size=Pt(17);p2.font.color.rgb=clrs[i];p2.font.bold=True;p2.font.name='Microsoft YaHei';p2.alignment=PP_ALIGN.CENTER
    p3=tf.add_paragraph();p3.text=desc;p3.font.size=Pt(11);p3.font.color.rgb=LIGHT_GRAY;p3.font.name='Microsoft YaHei';p3.alignment=PP_ALIGN.CENTER
page_num(s, 7)

# ===== Slide 8: 数据库 =====
s = add_slide()
sec_hdr(s, 3, '系统设计 — 数据库 & API', 'DATABASE & API')
tables = ['users 用户表 (7字段)', 'employee_base 员工表 (8字段)', 'job_detail 工作表 (8字段)',
          'attrition_risk 风险表 (8字段)', 'interventions 干预表 (7字段)',
          'operation_logs 日志表 (8字段)', 'report_records 报告表 (7字段)']
for i,t in enumerate(tables):
    add_card(s, 0.7+(i%2)*6.3, 2.7+(i//2)*0.85, 5.8, 0.7, t, '', ACCENT)
# API 统计
add_tb(s, 0.7, 6.0, 12, 0.6, 'API: 用户管理11个 | 员工管理6个 | 预测+报告9个 | 干预措施7个 | 操作日志5个 — 共40+接口',
       size=14, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
page_num(s, 8)

# ===== Slide 9: 系统测试 =====
s = add_slide()
sec_hdr(s, 5, '系统测试', 'TESTING')
td = [
    ['模块', '用例', '场景', '通过'],
    ['用户管理', '8', '登录/注册/权限/密码/头像', '✓'],
    ['员工管理', '5', '增删改查/搜索/校验', '✓'],
    ['离职预测', '6', '单/批量/AI/雷达图/容错', '✓'],
    ['报告管理', '5', 'PNG/Excel/邮件/下载', '✓'],
    ['干预措施', '6', '干预/列表/时间线/效果', '✓'],
    ['操作日志', '5', '埋点/查询/个人/统计/清理', '✓'],
]
ts = s.shapes.add_table(len(td),4,Inches(1.5),Inches(2.7),Inches(10),Inches(3.5))
tbl = ts.table
tbl.columns[0].width=Inches(2.2);tbl.columns[1].width=Inches(1.3)
tbl.columns[2].width=Inches(4.0);tbl.columns[3].width=Inches(2.5)
for r,row in enumerate(td):
    for c,val in enumerate(row):
        cell=tbl.cell(r,c);cell.text=val
        for p in cell.text_frame.paragraphs:
            p.font.size=Pt(14);p.font.name='Microsoft YaHei';p.alignment=PP_ALIGN.CENTER
            p.font.color.rgb=WHITE if r>0 else WHITE
            if r==0: p.font.bold=True
        cell.fill.solid()
        cell.fill.fore_color.rgb=ACCENT if r==0 else RGBColor(0x22,0x2F,0x40)
add_tb(s, 1.5, 6.5, 10, 0.5, '共 35 条测试用例，7 大模块全覆盖，通过率 100%', size=15, color=ACCENT, align=PP_ALIGN.CENTER)
page_num(s, 9)

# ===== Slides 10-14: 系统实施（含截图） =====
impl_sections = [
    ('4.1 用户管理', '10', '用户管理模块', '密码哈希+Session认证 / Cropper.js头像裁剪 / 角色权限admin+user / 注册登录表单校验'),
    ('4.2 员工管理', '11', '员工管理模块', '三表联合(employee_base+job_detail+attrition_risk) / CSV自动导入1470条 / Layui表格分页+模糊搜索 / 详情弹窗网格布局'),
    ('4.3 离职预测', '12', '离职风险预测模块', 'LR+RF加权集成(0.4/0.6) / 17特征→标准化→预测 / ECharts仪表盘 / AI自动分析 / 雷达图洞察'),
    ('4.4 报告管理', '13', '报告管理模块', 'Matplotlib拼合PNG / openpyxl 3Sheet Excel / QQ邮箱SMTP_SSL / ZIP批量下载'),
    ('4.5 干预跟踪', '14', '干预措施跟踪模块', '风险排名页快速干预按钮 / 6统计卡片 / CSS时间线(::before) / 已干预vs未干预效果对比'),
]

for key, num, title, desc in impl_sections:
    s = add_slide()
    sec_hdr(s, 4, f'系统实施 — {title}', 'IMPLEMENTATION')
    # 顶部技术要点（紧凑，只占2行左右）
    add_items(s, 0.6, 2.55, 12, 0.7, desc.split(' / '), isize=14)
    # 截图在下方
    add_screenshots(s, key, max_per_row=2)
    page_num(s, int(num))

# ===== Slide 15-16: 更多实施截图 =====
s = add_slide()
sec_hdr(s, 4, '系统实施 — 操作日志模块', 'IMPLEMENTATION')
add_items(s, 0.6, 2.55, 12, 0.7, ['log_action()一行埋点 / 12关键位置覆盖4文件 / 颜色标签区分操作类型 / 管理员+个人双页面 / 90天自动清理'], isize=14)
add_screenshots(s, '4.6 操作日志', max_per_row=2)
page_num(s, 15)

s = add_slide()
sec_hdr(s, 4, '系统实施 — 数据看板模块', 'IMPLEMENTATION')
add_items(s, 0.6, 2.55, 12, 0.7, ['4 KPI卡片(悬浮动画) / 5 ECharts图表 / 60s高风险轮询 / Notification桌面通知'], isize=14)
add_screenshots(s, '4.7 数据看板', max_per_row=2)
page_num(s, 16)

# ===== Slide 17: 亮点 =====
s = add_slide()
sec_hdr(s, 6, '项目亮点', 'HIGHLIGHTS')
add_items(s, 0.8, 2.8, 11.5, 4.0, [
    '★ 机器学习集成：LR+RF双模型加权预测，量化离职概率',
    '★ 完整业务闭环：预测→排名→干预→评估全链路',
    '★ 企业级审计：log_action()一行埋点，12位置全覆盖',
    '★ 多格式报告：PNG+Excel+PDF，ZIP打包+SMTP邮件',
    '★ 现代化UI：Layui+ECharts+CSS时间线+实时预警轮询',
    '★ 工程化设计：Blueprint/装饰器/工具封装/40+API',
], isize=18)
page_num(s, 17)

# ===== Slide 18: 总结 =====
s = add_slide()
sec_hdr(s, 6, '总结与展望', 'SUMMARY')
add_items(s, 0.8, 2.8, 5.5, 3.5, [
    '已实现：', '',
    '✓ 7大模块，16页面，40+API',
    '✓ 35测试用例全通过',
    '✓ 完整权限+日志审计',
    '✓ ML模型集成预测',
], isize=16)
add_items(s, 7.0, 2.8, 5.5, 3.5, [
    '改进方向：', '',
    '→ 接入企业真实数据',
    '→ 模型在线训练+版本管理',
    '→ 抽取公共CSS设计系统',
    '→ CSRF防护+自动备份',
    '→ 部署云服务器+MySQL',
], isize=16, tsize=28)
add_tb(s, 1, 6.5, 11, 0.6, '感谢各位老师聆听！', size=28, color=ACCENT, bold=True, align=PP_ALIGN.CENTER)
page_num(s, 18)

# ===== 保存 =====
output = r'C:\Users\ASUS\OneDrive\Desktop\04-项目文档.pptx'
prs.save(output)
print(f'PPT已保存至: {output}')
print(f'共 {len(prs.slides)} 页')

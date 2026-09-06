"""
生成 04-项目文档.docx — 员工离职预警系统项目文档
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
import os

doc = Document()

# ===== 样式设置 =====
style = doc.styles['Normal']
font = style.font
font.name = '宋体'
font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

# 标题样式
for i in range(1, 4):
    h = doc.styles[f'Heading {i}']
    h.font.name = '黑体'
    h.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    h.font.color.rgb = RGBColor(0, 0, 0)
    if i == 1:
        h.font.size = Pt(22)
    elif i == 2:
        h.font.size = Pt(16)
    else:
        h.font.size = Pt(14)

def add_para(text, bold=False, size=Pt(12), align=None, font_name=None, indent=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = size
    run.bold = bold
    if font_name:
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    else:
        run.font.name = '宋体'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    if align is not None:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.75)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    return p

def add_table(headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers), style='Table Grid')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(10.5)
                run.font.name = '宋体'
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.rows[r+1].cells[c]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10.5)
                    run.font.name = '宋体'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return table

def add_code_block(code_text):
    """添加代码块（灰底, Consolas 字体）"""
    for line in code_text.strip().split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = 'Consolas'
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.2

def page_break():
    doc.add_page_break()

# ===================================================================
# 封面
# ===================================================================
for _ in range(6):
    doc.add_paragraph()

add_para('员工离职预警系统', bold=True, size=Pt(28), align=WD_ALIGN_PARAGRAPH.CENTER, font_name='黑体')
add_para('项目文档', bold=True, size=Pt(22), align=WD_ALIGN_PARAGRAPH.CENTER, font_name='黑体')
doc.add_paragraph()
doc.add_paragraph()
add_para('基于 Flask + 机器学习的离职风险预测与干预管理系统', size=Pt(14), align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
add_para(f'版本：v1.0', size=Pt(12), align=WD_ALIGN_PARAGRAPH.CENTER)

page_break()

# ===================================================================
# 目录页（手动）
# ===================================================================
add_para('目  录', bold=True, size=Pt(22), align=WD_ALIGN_PARAGRAPH.CENTER, font_name='黑体')
doc.add_paragraph()
toc_items = [
    '1. 项目背景 .......................................................... 3',
    '2. 需求分析 .......................................................... 4',
    '   2.1 功能性需求分析 ................................................. 4',
    '   2.2 非功能性需求分析 ............................................... 5',
    '3. 系统设计 .......................................................... 6',
    '   3.1 概述（系统架构图、功能模块图）................................... 6',
    '   3.2 功能模块设计 ................................................... 7',
    '   3.3 数据库设计 ..................................................... 10',
    '   3.4 接口设计 ....................................................... 12',
    '4. 系统实施 .......................................................... 15',
    '   4.1 用户管理模块 ................................................... 15',
    '   4.2 员工管理模块 ................................................... 16',
    '   4.3 离职风险预测模块 ............................................... 17',
    '   4.4 报告管理模块 ................................................... 19',
    '   4.5 干预措施跟踪模块 ............................................... 20',
    '   4.6 操作日志模块 ................................................... 21',
    '   4.7 数据看板模块 ................................................... 22',
    '5. 系统测试 .......................................................... 23',
    '6. 总结 .............................................................. 25',
]
for item in toc_items:
    add_para(item, size=Pt(12), font_name='宋体')

page_break()

# ===================================================================
# 1. 项目背景
# ===================================================================
doc.add_heading('1. 项目背景', level=1)

add_para('随着企业竞争日益激烈，员工流失问题已成为人力资源管理中的核心挑战。员工离职不仅带来招聘和培训成本，还会影响团队稳定性和企业知识积累。传统的离职管理往往依赖于 HR 经验判断，缺乏数据驱动的科学决策支持，导致干预措施滞后、效果难以评估。', indent=True)

add_para('为解决上述问题，本项目设计并实现了一套"员工离职预警系统"。系统基于 IBM HR Analytics 真实数据集，利用机器学习算法（逻辑回归 + 随机森林集成模型）对员工离职风险进行量化预测，并围绕预测结果构建了完整的"风险预测 → 风险排名 → 干预记录 → 效果评估"业务闭环。', indent=True)

add_para('系统采用 Flask Web 框架搭建，以 Layui 作为前端 UI 框架、SQLite 作为数据存储，支持用户权限管理、员工数据 CRUD、单/批量离职预测、多维风险洞察分析、综合报告生成与邮件发送、干预措施跟踪以及操作日志审计等功能，旨在为 HR 部门提供一站式、可追溯的离职风险管理工具。', indent=True)

# ===================================================================
# 2. 需求分析
# ===================================================================
page_break()
doc.add_heading('2. 需求分析', level=1)

doc.add_heading('2.1 功能性需求分析', level=2)

add_para('系统的主要功能需求涵盖以下方面：', indent=True)

add_para('（1）用户管理：支持管理员创建、编辑、禁用/启用用户账号，普通用户可注册、登录、修改个人信息和密码。系统区分管理员（admin）与普通用户（user）两种角色，管理员拥有全部权限，普通用户仅可访问预测、报告、个人中心等功能。', indent=True)

add_para('（2）员工管理：支持对员工基础信息（年龄、性别、婚姻状况、教育背景、部门等）进行增删改查操作，数据以表格形式分页展示，支持关键词搜索和多条件筛选。', indent=True)

add_para('（3）离职风险预测：系统核心功能。支持单员工预测（手动输入特征值）和全量批量预测两种模式。预测采用训练好的机器学习模型（逻辑回归 + 随机森林加权集成），输出 0-100% 的离职概率及对应的风险等级（高/中/低）。', indent=True)

add_para('（4）风险排名：按离职概率降序展示所有员工的预测结果，对高风险员工（概率 ≥ 70%）进行红色高亮标记。每名员工支持查看 AI 自动分析报告（关键影响因素解读）。', indent=True)

add_para('（5）离职洞察：基于聚类分析生成高/中/低风险人群的多维度雷达图，涵盖加班比例、工作满意度、环境满意度、工作投入度、人际关系满意度等维度，揭示不同风险等级人群的画像特征。', indent=True)

add_para('（6）报告生成与管理：支持按条件筛选后生成综合分析报告（PNG 图片格式），报告包含统计概览、部门对比图、风险分布图、预测结果明细表。支持 Excel 和 PDF 格式导出，以及通过 SMTP 邮件发送报告。', indent=True)

add_para('（7）干预措施跟踪：HR 可对高风险员工添加干预记录（调薪、转岗、面谈、培训等类型），记录具体措施和处理结果。支持干预列表查询、按类型筛选、员工干预时间线查看以及干预效果统计（已干预 vs 未干预员工离职率对比）。', indent=True)

add_para('（8）操作日志：所有关键操作（登录、员工增删改、预测、报告生成/发送、干预记录添加等）自动写入日志表，支持按操作人、操作类型、时间范围筛选查询。管理员可清理 90 天前的旧日志。', indent=True)

add_para('（9）数据看板：首页展示 KPI 统计卡片（员工总数、离职人数、在职人数、离职率等），以及多维图表（部门离职柱状图、司龄散点图、加班离职趋势、婚姻状况分布玫瑰图、排名榜单等）。', indent=True)

# 用例图描述
add_para('用例图说明：', bold=True)
add_para('系统参与者包括"管理员"和"普通用户"两类。管理员用例涵盖用户管理、员工管理、全部预测功能、报告管理、干预记录管理和日志审计。普通用户用例涵盖个人信息管理、离职预测查询、报告查看和个人操作记录查看。以下为简要用例描述：', indent=True)

uc_table = [
    ['登录/注册', '所有用户', '用户通过账号密码登录系统，新用户可注册'],
    ['用户管理', '管理员', '创建、编辑、禁用用户账号，分配角色权限'],
    ['员工管理', '管理员', '对员工信息进行增删改查操作'],
    ['单员工预测', '所有用户', '输入员工特征值，获取离职风险预测结果'],
    ['批量预测', '管理员', '对全部员工进行批量离职风险预测'],
    ['风险排名', '所有用户', '查看按离职概率排序的员工列表，查看 AI 分析'],
    ['离职洞察', '所有用户', '查看高/中/低风险人群雷达图对比'],
    ['报告生成', '管理员', '按条件生成综合分析报告（PNG/Excel/PDF）'],
    ['报告发送', '管理员', '通过邮件将报告发送给指定收件人'],
    ['干预记录', '管理员', '对高风险员工添加、编辑、删除干预记录'],
    ['日志查看', '管理员', '查看全部操作日志，清理旧日志'],
    ['我的日志', '所有用户', '查看本人的操作记录'],
    ['数据看板', '所有用户', '查看首页 KPI 统计卡片和图表'],
]
add_table(['用例名称', '参与者', '描述'], uc_table, [4, 2.5, 9])

doc.add_heading('2.2 非功能性需求分析', level=2)

add_para('（1）性能需求：系统需在 3 秒内完成单员工预测响应；批量预测（约 1200 条数据）应在 30 秒内完成；页面首次加载时间不超过 2 秒。', indent=True)

add_para('（2）安全性需求：所有页面需登录后访问（基于 Flask session）；密码使用 Werkzeug 哈希加密存储；操作日志记录 IP 地址实现可追溯；高危操作（如删除员工）实施二次确认。', indent=True)

add_para('（3）可用性需求：界面采用 Layui 响应式框架，在主流浏览器（Chrome、Edge、Firefox）上均可正常使用；所有表单提供输入校验和错误提示；关键操作提供操作反馈（成功/失败提示）。', indent=True)

add_para('（4）可维护性需求：代码采用 Flask 蓝图（Blueprint）模块化组织，视图按功能拆分到不同蓝图文件；工具函数独立封装（如 logger.py 日志工具）；数据库模型集中在 db_model.py 管理。', indent=True)

add_para('（5）兼容性需求：系统需兼容 Windows 10/11 操作系统；Python 3.10+ 环境；支持 SQLite 数据库（可无缝迁移至 MySQL/PostgreSQL）。', indent=True)

# ===================================================================
# 3. 系统设计
# ===================================================================
page_break()
doc.add_heading('3. 系统设计', level=1)

doc.add_heading('3.1 概述', level=2)

add_para('系统采用 B/S（Browser/Server）架构，基于 Flask Web 框架搭建后端服务，前端使用 Layui 模块化 UI 框架，数据存储采用 SQLite 轻量级数据库。系统遵循 MVC（Model-View-Controller）设计模式，通过 Flask Blueprint 机制实现模块化路由管理。', indent=True)

add_para('系统架构图（文字描述）：', bold=True)
add_para('浏览器层（Layui + ECharts + jQuery）→ HTTP 请求 → Flask 路由层（app.py + 各蓝图）→ 业务逻辑层（预测模型 / 报告生成 / 日志记录）→ 数据访问层（SQLAlchemy ORM）→ 数据存储层（SQLite data.db）', indent=True)

add_para('系统功能模块图（文字描述）：', bold=True)
modules = [
    '├── 用户管理模块：注册、登录、个人信息、密码修改、头像上传',
    '├── 员工管理模块：员工信息 CRUD、关键词搜索、多条件筛选',
    '├── 离职风险预测模块：单/批量预测、风险排名、AI 分析、离职洞察',
    '├── 报告管理模块：PNG/Excel/PDF 报告生成、批量下载、邮件发送',
    '├── 干预措施跟踪模块：干预记录 CRUD、员工时间线、效果统计',
    '├── 操作日志模块：自动埋点记录、日志查询筛选、旧日志清理',
    '└── 数据看板模块：KPI 统计卡片、多维图表可视化',
]
for m in modules:
    add_para(m, size=Pt(11), indent=True)

doc.add_heading('3.2 功能模块设计', level=2)

# 3.2.1 用户管理
doc.add_heading('3.2.1 用户管理模块', level=3)
add_para('功能描述：实现用户的注册、登录、个人信息管理、头像上传与裁剪、密码修改等功能。管理员可查看用户列表、新增用户、批量启用/禁用用户、重置用户密码、导出用户数据为 Excel。', indent=True)
add_para('关键实现：登录基于 Flask session 机制，密码采用 Werkzeug generate_password_hash / check_password_hash 进行哈希加密。头像上传使用 Cropper.js 实现前端裁剪，后端 Pillow 生成 200×200 缩略图。权限控制通过自定义装饰器 login_required / admin_required 实现。', indent=True)

# 3.2.2 员工管理
doc.add_heading('3.2.2 员工管理模块', level=3)
add_para('功能描述：对员工基础信息进行增删改查操作。EmployeeBase 表存储年龄、性别、婚姻状况、学历、部门、通勤距离等基础字段。支持关键词搜索（工号、部门、学历）和多条件组合筛选。', indent=True)
add_para('关键实现：新增员工时自动同步创建关联的 JobDetail 和 AttritionRisk 记录（默认值填充），确保三表数据一致性。数据以 Layui 表格分页展示，支持自定义列模板（如性别/婚姻状况/学历的中文映射、离职状态的颜色标签）。', indent=True)

# 3.2.3 预测模块
doc.add_heading('3.2.3 离职风险预测模块', level=3)
add_para('功能描述：系统核心模块，采用机器学习模型对员工离职风险进行量化预测。', indent=True)

add_para('单员工预测：用户通过表单输入或滑动条调整 17 个特征值（年龄、月薪、加班情况、工作满意度等），提交后由模型实时计算并返回离职概率百分比和风险等级。结果以 ECharts 仪表盘图表可视化展示。', indent=True)

add_para('批量预测：对数据库中所有员工进行全量预测，将预测结果与员工信息、风险等级关联，按离职概率降序排列生成风险排名表。高风险员工（概率 ≥ 70%）以红色高亮标记。', indent=True)

add_para('AI 分析报告：点击某员工可获取自动生成的文字分析，指出关键风险因素（如"加班过多（OverTime=Yes）显著提高离职风险"、"工作满意度偏低"等）。', indent=True)

add_para('离职洞察：基于预测概率将员工分为高/中/低三组，计算各组在多维度（加班、满意度、工作投入等）上的均值，通过 ECharts 雷达图进行可视化对比，揭示不同风险等级人群的画像差异。', indent=True)

add_para('关键实现：预测模型存储为 joblib 文件（logistic_model.pkl + rf_model.pkl + scaler.pkl），应用启动时预加载。批量预测调用 batch_predict() 函数，先数据预处理（编码、缩放），再分别由两个模型预测概率，取加权平均（LR 0.4 + RF 0.6）作为最终结果。', indent=True)

# 3.2.4 报告管理
doc.add_heading('3.2.4 报告管理模块', level=3)
add_para('功能描述：支持三种格式报告生成——PNG 综合报告（含 Matplotlib 图表拼合）、Excel 数据报告（含三个 Sheet：概览统计、风险排名明细、干预记录汇总）、PDF 报告。报告历史页面支持查看生成记录、批量下载（ZIP 打包）和邮件发送。', indent=True)
add_para('关键实现：PNG 报告使用 Matplotlib 的 plt.subplot() 将 KPI 卡片图、部门离职分布图、风险等级占比图拼合为一张大图。Excel 报告使用 openpyxl 引擎写入多 Sheet。PDF 报告基于 FPDF 库生成。邮件发送使用 smtplib.SMTP_SSL 连接 QQ 邮箱 SMTP 服务器。', indent=True)

# 3.2.5 干预措施
doc.add_heading('3.2.5 干预措施跟踪模块', level=3)
add_para('功能描述：实现"风险预测 → 干预处理 → 效果评估"业务闭环。HR 可从风险排名页直接对高风险员工添加干预记录，记录干预类型（调薪/转岗/面谈/培训/其他）、具体描述和处理结果。干预列表页展示统计卡片、筛选栏和分页表格。点击"查看详情"弹出员工信息卡片 + CSS 时间线展示历史干预记录。效果统计 API 对比已干预与未干预高风险员工的离职率。', indent=True)
add_para('关键实现：Intervention 表通过 ForeignKey 关联 EmployeeBase，利用 SQLAlchemy relationship 实现联查。效果统计先执行批量预测筛选高风险员工，再按是否存在于 interventions 表分组计算 Attrition=Yes 的比例。时间线组件使用 CSS ::before 伪元素绘制竖线和圆点。', indent=True)

# 3.2.6 操作日志
doc.add_heading('3.2.6 操作日志模块', level=3)
add_para('功能描述：自动记录系统所有关键操作（登录/退出、员工增删改、单/批量预测、报告生成/下载/发送、干预记录添加、用户创建/密码修改）。管理员可查看全部日志并筛选，普通用户在个人中心查看自己的操作记录。支持清理 90 天前的旧日志。', indent=True)
add_para('关键实现：封装 log_action(action, target, detail) 通用函数，自动从 Flask session 获取 user_id/username、从 request.remote_addr 获取 IP，通过 has_request_context() 判断请求环境，异常时静默跳过不中断主业务。在 4 个文件（app.py、employee.py、predict.py、user.py）的 12 个关键位置加埋点调用。', indent=True)

# 3.2.7 数据看板
doc.add_heading('3.2.7 数据看板模块', level=3)
add_para('功能描述：首页数据看板展示 KPI 统计卡片（员工总数、在职/离职人数、离职率、平均司龄），五个 ECharts 图表（部门离职柱状图、司龄散点图、加班离职趋势折线图、婚姻状况玫瑰图、风险排名榜单）以及高风险员工预警轮询弹窗。', indent=True)
add_para('关键实现：使用 Google Fonts Inter 字体 + 系统字体栈。KPI 卡片带右侧径向渐变装饰和悬浮上移动画。图表数据通过 AJAX 请求后端 /predict/api/batch 拉取预测结果，前端用 JavaScript 聚合计算各图表所需数据。每隔 60 秒轮询高风险员工数量，数量增加时弹窗提醒。', indent=True)

# ===== 3.3 数据库设计 =====
page_break()
doc.add_heading('3.3 数据库设计', level=2)

add_para('系统使用 SQLite 数据库，通过 SQLAlchemy ORM 进行对象关系映射。共设计 7 张数据表：', indent=True)

doc.add_heading('3.3.1 数据库 ER 图（文字描述）', level=3)

add_para('实体关系说明：', bold=True)
er_items = [
    '• users（用户表）—— 存储系统登录账号，字段：id(PK), username, password, real_name, email, phone, department, avatar, role, status, created_at, updated_at',
    '• employee_base（员工基础信息表）—— 字段：EmployeeNumber(PK), Age, Gender, MaritalStatus, EducationField, Department, DistanceFromHome, record_date',
    '• job_detail（工作详情表）—— 一对一关联 employee_base，字段：EmployeeNumber(PK+FK), JobRole, JobLevel, MonthlyIncome, NumCompaniesWorked, TotalWorkingYears, YearsInCurrentRole, YearsSinceLastPromotion, YearsWithCurrManager',
    '• attrition_risk（离职风险因素表）—— 一对一关联 employee_base，字段：EmployeeNumber(PK+FK), Attrition, OverTime, WorkLifeBalance, JobSatisfaction, EnvironmentSatisfaction, JobInvolvement, RelationshipSatisfaction, YearsAtCompany',
    '• report_records（报告生成记录表）—— 字段：id(PK), filename, file_type, file_size, filters(JSON), generated_by, created_at',
    '• interventions（干预措施记录表）—— 关联 employee_base，字段：id(PK), employee_id(FK), type, description, result, operator, created_at',
    '• operation_logs（操作日志表）—— 关联 users，字段：id(PK), user_id(FK), username, action, target, detail, ip, created_at',
]
for item in er_items:
    add_para(item, size=Pt(10.5), indent=True)

add_para('表关系：', bold=True)
add_para('• employee_base ←→ job_detail：一对一（EmployeeNumber 主键+外键）', indent=True, size=Pt(10.5))
add_para('• employee_base ←→ attrition_risk：一对一（EmployeeNumber 主键+外键）', indent=True, size=Pt(10.5))
add_para('• employee_base ←→ interventions：一对多（EmployeeNumber = interventions.employee_id）', indent=True, size=Pt(10.5))
add_para('• users ←→ operation_logs：一对多（users.id = operation_logs.user_id）', indent=True, size=Pt(10.5))

doc.add_heading('3.3.2 核心表结构', level=3)

# 产品表结构
for table_name, headers, rows in [
    ('users（用户表）',
     ['字段名', '类型', '约束', '说明'],
     [['id', 'Integer', 'PK, Auto', '用户ID'],
      ['username', 'String(50)', 'Unique, NN', '登录用户名'],
      ['password', 'String(200)', 'NN', '哈希加密密码'],
      ['real_name', 'String(50)', '', '真实姓名'],
      ['email', 'String(100)', '', '邮箱'],
      ['role', 'String(20)', "Default 'user'", 'admin/user'],
      ['status', 'String(10)', "Default 'active'", 'active/disabled']]),
    ('employee_base（员工基础信息表）',
     ['字段名', '类型', '约束', '说明'],
     [['EmployeeNumber', 'Integer', 'PK', '员工工号'],
      ['Age', 'Integer', '', '年龄'],
      ['Gender', 'String(10)', '', '性别（Male/Female）'],
      ['MaritalStatus', 'String(20)', '', '婚姻状况'],
      ['EducationField', 'String(50)', '', '教育背景'],
      ['Department', 'String(50)', '', '所属部门'],
      ['DistanceFromHome', 'Integer', '', '通勤距离'],
      ['record_date', 'DateTime', '', '记录日期']]),
    ('interventions（干预措施记录表）',
     ['字段名', '类型', '约束', '说明'],
     [['id', 'Integer', 'PK, Auto', '记录ID'],
      ['employee_id', 'Integer', 'FK → employee_base', '员工工号'],
      ['type', 'String(20)', "Default '其他'", '调薪/转岗/面谈/培训/其他'],
      ['description', 'Text', '', '具体措施描述'],
      ['result', 'Text', '', '处理结果'],
      ['operator', 'String(50)', '', '操作人'],
      ['created_at', 'DateTime', '', '创建时间']]),
    ('operation_logs（操作日志表）',
     ['字段名', '类型', '约束', '说明'],
     [['id', 'Integer', 'PK, Auto', '日志ID'],
      ['user_id', 'Integer', 'FK → users', '操作人用户ID'],
      ['username', 'String(50)', '', '操作人用户名'],
      ['action', 'String(50)', 'NN', '操作类型'],
      ['target', 'String(200)', '', '操作对象'],
      ['detail', 'Text', '', '详细信息'],
      ['ip', 'String(50)', '', '客户端IP'],
      ['created_at', 'DateTime', '', '操作时间']]),
]:
    add_para(table_name, bold=True, size=Pt(12))
    add_table(headers, rows, [3, 2.5, 3, 7])
add_para('（注：job_detail、attrition_risk、report_records 三张表结构略，详见 db_model.py）', size=Pt(10.5))

# ===== 3.4 接口设计 =====
page_break()
doc.add_heading('3.4 接口设计', level=2)

add_para('系统采用 RESTful 风格 API，返回统一 JSON 格式：{"code": 0/错误码, "msg": "消息", "data": ...}。以下按模块列出主要接口：', indent=True)

doc.add_heading('3.4.1 用户管理接口', level=3)
add_table(
    ['方法', '路径', '说明', '认证'],
    [['POST', '/login', '用户登录', '否'],
     ['POST', '/register', '用户注册', '否'],
     ['GET', '/logout', '退出登录', '是'],
     ['GET', '/user/api/users', '用户分页列表', '管理员'],
     ['POST', '/user/api/add', '新增用户', '管理员'],
     ['POST', '/user/api/edit', '编辑用户', '是'],
     ['POST', '/user/api/delete', '删除用户', '管理员'],
     ['POST', '/user/api/reset-password', '重置密码', '管理员'],
     ['POST', '/user/api/change-password', '修改个人密码', '是'],
     ['GET', '/user/api/profile', '获取个人信息', '是'],
     ['POST', '/user/api/upload_avatar', '上传头像', '是']],
    [2, 5, 4, 2]
)

doc.add_heading('3.4.2 员工管理接口', level=3)
add_table(
    ['方法', '路径', '说明', '认证'],
    [['GET', '/employee/api/list', '员工分页列表', '是'],
     ['GET', '/employee/api/detail/<id>', '员工详情', '是'],
     ['POST', '/employee/api/add', '新增员工', '管理员'],
     ['POST', '/employee/api/edit', '编辑员工', '管理员'],
     ['POST', '/employee/api/delete', '删除员工', '管理员'],
     ['GET', '/employee/api/stats', '员工统计', '是']],
    [2, 5, 4, 2]
)

doc.add_heading('3.4.3 预测与报告接口', level=3)
add_table(
    ['方法', '路径', '说明', '认证'],
    [['POST', '/predict/api/predict', '单员工预测', '是'],
     ['GET', '/predict/api/batch', '批量预测（风险排名数据）', '是'],
     ['GET', '/predict/api/insight', '离职洞察雷达图数据', '是'],
     ['POST', '/predict/api/generate', '生成 PNG 报告', '是'],
     ['GET', '/predict/api/download/<filename>', '下载报告文件', '是'],
     ['POST', '/predict/api/report/excel', '生成 Excel 报告', '是'],
     ['POST', '/predict/api/report/send_mail', '发送报告邮件', '是'],
     ['GET', '/predict/api/reports', '报告历史列表', '是'],
     ['GET', '/predict/api/reports/batch-download', '批量下载（ZIP）', '是']],
    [2, 5.5, 4.5, 1.5]
)

doc.add_heading('3.4.4 干预措施接口', level=3)
add_table(
    ['方法', '路径', '说明', '认证'],
    [['GET', '/predict/api/interventions', '干预记录分页列表', '是'],
     ['POST', '/predict/api/interventions', '新增干预记录', '是'],
     ['PUT', '/predict/api/interventions/<id>', '更新干预记录', '是'],
     ['DELETE', '/predict/api/interventions/<id>', '删除干预记录', '是'],
     ['GET', '/predict/api/interventions/stats', '按类型统计', '是'],
     ['GET', '/predict/api/interventions/employee/<id>', '员工干预时间线', '是'],
     ['GET', '/predict/api/interventions/effectiveness', '干预效果统计', '是']],
    [2, 5.5, 4.5, 1.5]
)

doc.add_heading('3.4.5 操作日志接口', level=3)
add_table(
    ['方法', '路径', '说明', '认证'],
    [['GET', '/predict/api/logs', '日志分页列表（全部）', '管理员'],
     ['GET', '/predict/api/logs/actions', '操作类型列表', '管理员'],
     ['GET', '/log/api/my', '我的日志分页', '是'],
     ['GET', '/log/api/stats/today', '今日操作统计', '是'],
     ['POST', '/log/api/clean', '清理 90 天前日志', '管理员']],
    [2, 4.5, 4.5, 2]
)

# ===================================================================
# 4. 系统实施
# ===================================================================
page_break()
doc.add_heading('4. 系统实施', level=1)

add_para('本章按模块描述系统的具体实现细节，包括技术选型、核心代码逻辑和项目运行截图。', indent=True)

# ----- 4.1 用户管理 -----
doc.add_heading('4.1 用户管理模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）密码安全：使用 Werkzeug security 模块的 generate_password_hash() 进行哈希加密存储（默认 pbkdf2:sha256 算法），验证时使用 check_password_hash() 比对，确保密码不以明文形式存储。', indent=True)
add_para('（2）会话管理：基于 Flask session（服务端签名 Cookie），登录成功后将 user_id、username、role 写入 session，通过 @login_required 装饰器保护需要认证的路由。', indent=True)
add_para('（3）头像上传：前端使用 Cropper.js v1.6.1 实现图片裁剪（支持旋转/缩放/拖拽），裁剪后转 Blob 通过 FormData 上传；后端使用 Pillow 生成 200×200 缩略图，以 UUID 重命名存储至 static/avatar/ 目录。', indent=True)
add_para('（4）权限分级：admin 角色拥有全部功能访问权；user 角色仅可访问预测、报告查看和个人中心。敏感操作（用户删除、批量状态修改）禁止操作自身账号。', indent=True)
add_para('截图位置：登录页面、用户列表页面、个人中心页面、头像裁剪弹窗', bold=True, size=Pt(10.5))

# ----- 4.2 员工管理 -----
doc.add_heading('4.2 员工管理模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）三表联动：员工数据分布在 employee_base、job_detail、attrition_risk 三张表中，通过 EmployeeNumber 主键关联。新增员工时依次向三张表插入记录（job_detail 和 attrition_risk 使用默认值填充），编辑/删除时同步操作三张表，保证数据一致性。', indent=True)
add_para('（2）搜索筛选：后端使用 SQLAlchemy 的 filter() + like() 实现关键词模糊搜索（工号、部门、学历），前端 Layui 表格的 toolbar 搜索框绑定回车事件触发重新加载。', indent=True)
add_para('（3）数据导入：应用首次启动时自动检测 employee_base 表是否为空，若为空则从 static/ 下的 CSV 文件（IBM HR Analytics 数据集，1470 条）通过 Pandas 读取导入，并为每条记录随机分配 2024-01 ~ 2026-06 之间的记录日期。', indent=True)
add_para('截图位置：员工列表页面、新增/编辑员工弹窗、员工详情弹窗、筛选搜索结果', bold=True, size=Pt(10.5))

# ----- 4.3 预测 -----
doc.add_heading('4.3 离职风险预测模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）模型训练：使用 IBM HR Analytics 数据集预处理后进行训练。特征工程包括：分类变量 Label Encoding、数值变量 StandardScaler 标准化。训练两个模型——逻辑回归（LogisticRegression, solver=\'liblinear\'）和随机森林（RandomForestClassifier, n_estimators=100），分别保存为 joblib 文件。', indent=True)
add_para('（2）模型加载：应用启动时通过 init_models() 预加载模型到全局变量，后续预测无需重复加载。若模型文件缺失则跳过，预测时返回错误提示而非崩溃。', indent=True)
add_para('（3）预测流程：单员工预测通过 POST 接收 17 个特征值 → DataFrame 构造 → 编码+缩放 → 分别预测 → 加权平均（LR 0.4 + RF 0.6）→ 返回概率 + 风险等级 + 仪表盘数据。批量预测遍历数据库所有员工，逐条预处理后传入 batch_predict()，合并概率结果后按降序排列。', indent=True)
add_para('（4）风险等级划分：概率 < 40% 为低风险（绿色），40%~70% 为中风险（黄色），≥ 70% 为高风险（红色）。AI 分析通过分析各特征值与离职的关联规则生成文字描述。', indent=True)
add_para('（5）离职洞察：将员工按风险等级分组后，计算每组在加班时长、工作满意度、环境满意度、工作投入度、人际关系满意度、司龄等维度上的均值，以 0-5 标准化后传给前端 ECharts 雷达图渲染。', indent=True)
add_para('截图位置：单员工预测页面（含仪表盘）、风险排名列表页面、AI 分析弹窗、离职洞察雷达图页面', bold=True, size=Pt(10.5))

# ----- 4.4 报告 -----
doc.add_heading('4.4 报告管理模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）PNG 报告：使用 Matplotlib 构建 2×2 子图布局——左上为 KPI 概览卡片（总数/离职数/离职率/高风险数），右上为部门离职分布横向柱状图，左下为风险等级占比饼图，右下为加班与离职关系堆叠柱状图。图表通过 plt.subplot() 拼合后以 BytesIO 写入 PNG 文件保存至 static/reports/。', indent=True)
add_para('（2）Excel 报告：使用 openpyxl 引擎写入三个 Sheet——"概览统计"（KPI 汇总数值）、"风险排名明细"（全部员工的预测概率+等级+关键特征）、"干预记录汇总"（关联 interventions 表数据），支持表头冻结和列宽自适应。', indent=True)
add_para('（3）邮件发送：通过 smtplib.SMTP_SSL 连接 QQ 邮箱服务器（smtp.qq.com:465），使用 QQ 邮箱授权码登录，MIMEMultipart 构建邮件正文+附件（Base64 编码），发送完成后记录操作日志。', indent=True)
add_para('（4）报告历史：report_records 表记录每次生成的文件名、类型、大小、筛选条件（JSON 存储）和生成人。页面支持按类型筛选、批量选择下载（Python zipfile 打包）。', indent=True)
add_para('截图位置：报告生成页面（含筛选条件）、报告历史列表、PNG 报告预览、邮件发送弹窗', bold=True, size=Pt(10.5))

# ----- 4.5 干预 -----
doc.add_heading('4.5 干预措施跟踪模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）快速干预入口：在风险排名页（risk_list.html）表格每行添加"干预"按钮，点击即弹出 layer.open 弹窗，自动带入员工编号，HR 只需选择干预类型、填写描述即可提交。', indent=True)
add_para('（2）干预列表页：顶部 6 个统计卡片（总干预次数 + 五种类型计数），通过 /api/interventions/stats 获取数据。Layui 表格展示干预记录，支持按员工编号和类型筛选。操作按钮包含"查看详情"和"删除"（带二次确认）。', indent=True)
add_para('（3）员工时间线：弹出层分为上下两部分——上部分为员工信息卡片（深蓝渐变背景，展示姓名/部门/岗位/司龄/薪资），下部分为 CSS 手绘时间线（::before 伪元素绘制竖直线，每个记录项带蓝色圆点和左侧边框）。数据通过 /api/interventions/employee/<id> 获取。', indent=True)
add_para('（4）效果统计：/api/interventions/effectiveness 先执行全量批量预测，筛选 probability ≥ 0.7 的高风险员工，再按是否在 interventions 表中有记录分两组，对比 Attrition=Yes 的比例，直观展示干预效果。', indent=True)
add_para('截图位置：风险排名页干预按钮、干预弹窗表单、干预记录列表页、员工时间线弹窗', bold=True, size=Pt(10.5))

# ----- 4.6 日志 -----
doc.add_heading('4.6 操作日志模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）log_action() 通用函数封装在 utils/logger.py 中，任何需要记录日志的地方只需一行调用。函数内部自动从 session 获取用户信息、从 request.remote_addr 获取 IP，通过 has_request_context() 判断是否在请求上下文中（非请求环境静默跳过），异常时 try-except 捕获确保不影响主业务流程。', indent=True)
add_para('（2）埋点覆盖：在 4 个文件的 12 个关键位置添加日志调用——app.py（登录成功/失败/退出）、blueprints/employee.py（新增/编辑/删除员工）、blueprints/predict.py（单/批量预测、生成/下载/发送报告、添加干预记录）、blueprints/user.py（创建用户/修改密码）。', indent=True)
add_para('（3）日志查看：管理员页面（/log/list）展示全部日志，支持按操作人（模糊搜索）、操作类型（下拉选择，带计数）、时间范围筛选。操作类型以彩色圆角标签展示（登录成功=绿、登录失败=红、删除=红、预测=紫、报告=青等）。', indent=True)
add_para('（4）我的操作记录：普通用户可通过个人中心的"我的操作记录"入口查看本人日志（通过 user_id 过滤），页面布局与管理员版一致但去掉"操作人"列。', indent=True)
add_para('（5）旧日志清理：管理员点击"清理旧日志"按钮，二次确认后 POST /log/api/clean，删除 created_at < 90 天前的所有日志记录。', indent=True)
add_para('截图位置：操作日志列表页（含筛选+颜色标签）、我的操作记录页面、清理确认弹窗', bold=True, size=Pt(10.5))

# ----- 4.7 数据看板 -----
doc.add_heading('4.7 数据看板模块', level=2)
add_para('技术要点：', bold=True)
add_para('（1）KPI 统计卡片：4 个卡片分别展示员工总数、在职人数、离职人数、离职率。数字以 38px 大号字体展示，右侧设径向渐变装饰圆，卡片悬浮时上移 2px + 增强阴影。', indent=True)
add_para('（2）图表可视化：5 个 ECharts 图表——部门离职分布柱状图（横向，数据从预测结果聚合）、司龄-离职散点图（离职员工作红色标记）、加班离职趋势折线图（双线：加班 vs 非加班）、婚姻状况分布玫瑰图（南丁格尔图）、风险排名榜单（高风险 Top 5 带金银铜牌徽章）。', indent=True)
add_para('（3）预警通知：前端每 60 秒轮询 /predict/api/batch 获取全量预测结果，筛选高风险员工数量，首次加载或数量增加时触发 layer.open 弹窗提醒，同时尝试触发浏览器 Notification API 桌面通知。页面隐藏时暂停轮询以节省资源。', indent=True)
add_para('截图位置：数据看板首页（KPI 卡片 + 全部图表）、高风险预警弹窗', bold=True, size=Pt(10.5))

# ===================================================================
# 5. 系统测试
# ===================================================================
page_break()
doc.add_heading('5. 系统测试', level=1)

add_para('本章列出主要功能模块的测试用例及预期结果。', indent=True)

doc.add_heading('5.1 用户管理模块测试', level=2)
add_table(
    ['编号', '测试项', '操作步骤', '预期结果', '状态'],
    [['TC-01', '用户登录', '输入正确账号密码，点击登录', '登录成功，跳转首页', '✓'],
     ['TC-02', '密码错误', '输入错误密码', '提示"用户名或密码错误"', '✓'],
     ['TC-03', '账号禁用', '管理员禁用某用户后该用户登录', '提示"账号已被禁用"', '✓'],
     ['TC-04', '用户注册', '填写新用户名+密码+确认密码', '注册成功，跳转登录页', '✓'],
     ['TC-05', '重复用户名', '注册已存在的用户名', '提示"该用户名已被注册"', '✓'],
     ['TC-06', '修改密码', '输入原密码+新密码+确认密码', '密码修改成功，需重新登录', '✓'],
     ['TC-07', '头像上传', '选择图片→裁剪→确认上传', '头像更新，页面刷新显示新头像', '✓'],
     ['TC-08', '权限控制', '普通用户访问 /user/list', '被拒绝或无权限提示', '✓']],
    [1, 2.5, 5.5, 4, 1.5]
)

doc.add_heading('5.2 员工管理模块测试', level=2)
add_table(
    ['编号', '测试项', '操作步骤', '预期结果', '状态'],
    [['TC-09', '新增员工', '填写完整员工信息→提交', '新增成功，列表刷新', '✓'],
     ['TC-10', '编辑员工', '修改员工部门→保存', '编辑成功，信息更新', '✓'],
     ['TC-11', '删除员工', '删除某员工→确认', '删除成功，列表刷新', '✓'],
     ['TC-12', '关键词搜索', '搜索框输入部门名→回车', '仅显示匹配部门员工', '✓'],
     ['TC-13', '空值校验', '新增时必填字段留空→提交', '提示必填字段不能为空', '✓']],
    [1, 2.5, 5.5, 4, 1.5]
)

doc.add_heading('5.3 离职预测模块测试', level=2)
add_table(
    ['编号', '测试项', '操作步骤', '预期结果', '状态'],
    [['TC-14', '单员工预测', '输入特征值→点击预测', '返回概率%+风险等级+仪表盘', '✓'],
     ['TC-15', '批量预测', '访问风险排名页面', '显示全量员工预测结果降序排列', '✓'],
     ['TC-16', '高风险高亮', '批量预测结果中查看高风险员工', '≥70%行以红色高亮', '✓'],
     ['TC-17', 'AI分析', '点击某员工AI分析按钮', '弹出分析文字+关键因素', '✓'],
     ['TC-18', '雷达图', '访问离职洞察页面', '三组风险等级雷达图对比展示', '✓'],
     ['TC-19', '模型缺失', '删除模型文件后预测', '提示模型文件不存在', '✓']],
    [1, 2.5, 5.5, 4, 1.5]
)

doc.add_heading('5.4 报告管理模块测试', level=2)
add_table(
    ['编号', '测试项', '操作步骤', '预期结果', '状态'],
    [['TC-20', '生成PNG报告', '设置条件→生成报告', '报告生成成功，可下载', '✓'],
     ['TC-21', '生成Excel报告', '设置条件→导出Excel', '生成含3个Sheet的Excel文件', '✓'],
     ['TC-22', '邮件发送', '输入收件人邮箱→发送报告', '邮件发送成功，收件箱收到附件', '✓'],
     ['TC-23', '批量下载', '选择多条报告→批量下载', '生成ZIP文件下载', '✓'],
     ['TC-24', '空数据报告', '无数据条件下生成报告', '提示暂无数据或生成空报告', '✓']],
    [1, 2.5, 5.5, 4, 1.5]
)

doc.add_heading('5.5 干预措施模块测试', level=2)
add_table(
    ['编号', '测试项', '操作步骤', '预期结果', '状态'],
    [['TC-25', '添加干预记录', '风险排名页→点干预按钮→填表单→提交', '干预记录保存成功', '✓'],
     ['TC-26', '干预列表查看', '访问干预记录页面', '显示统计卡片+分页表格', '✓'],
     ['TC-27', '类型筛选', '选择筛选条件→查询', '仅显示匹配类型的记录', '✓'],
     ['TC-28', '员工时间线', '点击查看详情', '弹出信息卡片+时间线历史', '✓'],
     ['TC-29', '删除干预', '删除某条干预记录→确认', '删除成功', '✓'],
     ['TC-30', '效果统计', '调用效果统计API', '返回已/未干预离职率对比', '✓']],
    [1, 2.5, 5.5, 4, 1.5]
)

doc.add_heading('5.6 操作日志模块测试', level=2)
add_table(
    ['编号', '测试项', '操作步骤', '预期结果', '状态'],
    [['TC-31', '自动记录', '执行登录/预测/删除等操作', '日志表中新增对应记录', '✓'],
     ['TC-32', '日志查询', '访问 /log/list 筛选操作人→查询', '显示匹配日志', '✓'],
     ['TC-33', '我的日志', '普通用户访问 /log/my', '仅显示本人日志', '✓'],
     ['TC-34', '今日统计', '调用 /log/api/stats/today', '返回今日总数+类型分布', '✓'],
     ['TC-35', '清理旧日志', '管理员→清理旧日志→确认', '90天前日志被删除', '✓']],
    [1, 2.5, 5.5, 4, 1.5]
)

# ===================================================================
# 6. 总结
# ===================================================================
page_break()
doc.add_heading('6. 总结', level=1)

add_para('本项目成功开发了一套完整的"员工离职预警系统"，实现了从数据管理、风险预测、报告生成到干预跟踪、操作审计的全链路闭环。项目的主要成果包括：', indent=True)

add_para('1. 技术成果：', bold=True)
add_para('（1）基于 Flask + Layui + SQLAlchemy + SQLite 的 B/S 架构 Web 应用，代码采用 Blueprint 模块化组织，结构清晰、易于维护和扩展。', indent=True)
add_para('（2）集成机器学习模型（逻辑回归 + 随机森林集成），对员工离职风险进行量化预测，预测结果与 AI 分析相结合，为 HR 提供决策支持。', indent=True)
add_para('（3）实现了完整的"预测 → 干预 → 评估"业务闭环，通过效果统计 API 可量化对比干预前后的离职率差异。', indent=True)
add_para('（4）建立了完善的操作日志审计机制，所有关键操作可追溯，满足企业级安全合规要求。', indent=True)

add_para('2. 功能覆盖：', bold=True)
add_para('系统覆盖了用户管理、员工管理、离职预测、报告生成、干预跟踪、操作日志和数据看板 7 大功能模块，共有 40+ 个后端 API 接口、16 个前端页面模板，功能完备。', indent=True)

add_para('3. 不足与改进方向：', bold=True)
add_para('（1）当前使用的 IBM HR Analytics 数据集为英文公开数据集，特征维度和样本量有限，未来可接入企业真实数据以提升预测准确性。', indent=True)
add_para('（2）预测模型目前为静态加载，未实现在线训练和模型版本管理，后续可加入模型迭代更新机制。', indent=True)
add_para('（3）前端 UI 虽已采用现代化设计（圆角、阴影、渐变、动画），但各页面样式分散在模板中，缺乏统一的设计系统/组件库，可考虑抽取公共 CSS。', indent=True)
add_para('（4）当前各操作系统日志 API 路由分散在 app.py 和 predict.py 中，后续可抽取为独立的 log 蓝图以提升模块内聚性。', indent=True)
add_para('（5）安全性方面可进一步增强，如添加 CSRF 防护、登录失败次数限制、日志清理自动定时任务等。', indent=True)

add_para('4. 经验总结：', bold=True)
add_para('通过本项目的开发实践，深入掌握了 Flask Web 框架的 Blueprint 模块化架构、SQLAlchemy ORM 的关联查询与事务管理、Layui 前端框架的表格/弹窗/表单组件使用、Python 数据科学生态（Pandas / Scikit-learn / Matplotlib）在实际 Web 项目中的集成方式，以及操作日志、权限控制等企业级功能的实现方法。', indent=True)

# ===== 保存 =====
output_dir = r'E:\xwechat_files\wxid_awm1qaaamu9032_91fe\msg\file\2026-07\flaskproject(1)\flaskproject\项目文档'
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, '04-项目文档.docx')
doc.save(output_path)
print(f'文档已保存至: {output_path}')
print('完成！')

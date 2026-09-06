"""
在需求任务.docx 每个任务截图后插入核心代码
"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn

DOC_PATH = r'C:/Users/ASUS/OneDrive/Desktop/需求任务.docx'


def make_code_para(doc, text, bold=False, color=None, font_size=Pt(10.5)):
    p = doc.add_paragraph('')
    if p.runs:
        p.runs[0].text = ''
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    run.font.size = font_size
    if bold:
        run.bold = True
    if color:
        run.font.color.rgb = color
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    return p


def insert_before(doc, target_para, new_paragraphs):
    for p in reversed(new_paragraphs):
        target_para._element.addprevious(p._element)


def insert_after_last(doc, new_paragraphs):
    last_p = doc.paragraphs[-1]
    for p in reversed(new_paragraphs):
        last_p._element.addnext(p._element)


def add_section(doc, anchor_text, lines, title='【核心代码】'):
    """lines: list of (style, text) where style is 'title','fe','be','file','comment',None"""
    target = None
    for p in doc.paragraphs:
        if p.text.strip() == anchor_text:
            target = p
            break
    if target is None:
        print(f'  !! anchor not found: {anchor_text}')
        return False

    paras = []
    # empty line
    pe = make_code_para(doc, '')
    pe.paragraph_format.space_before = Pt(6)
    paras.append(pe)
    # title
    paras.append(make_code_para(doc, title, bold=True, color=RGBColor(0x00, 0x96, 0x88)))

    for style, text in lines:
        if style == 'fe':
            paras.append(make_code_para(doc, text, bold=True, color=RGBColor(0x40, 0x9E, 0xFF)))
        elif style == 'be':
            paras.append(make_code_para(doc, text, bold=True, color=RGBColor(0xE6, 0xA2, 0x3C)))
        elif style == 'file':
            paras.append(make_code_para(doc, text, bold=True, color=RGBColor(0x78, 0x78, 0x78)))
        elif style == 'comment':
            paras.append(make_code_para(doc, text, color=RGBColor(0x90, 0x93, 0x99)))
        elif style == 'sep':
            p = make_code_para(doc, '')
            p.paragraph_format.space_before = Pt(2)
            paras.append(p)
        else:
            paras.append(make_code_para(doc, text))

    insert_before(doc, target, paras)
    return True


def add_section_end(doc, lines, title='【核心代码】'):
    paras = []
    pe = make_code_para(doc, '')
    pe.paragraph_format.space_before = Pt(6)
    paras.append(pe)
    paras.append(make_code_para(doc, title, bold=True, color=RGBColor(0x00, 0x96, 0x88)))

    for style, text in lines:
        if style == 'fe':
            paras.append(make_code_para(doc, text, bold=True, color=RGBColor(0x40, 0x9E, 0xFF)))
        elif style == 'be':
            paras.append(make_code_para(doc, text, bold=True, color=RGBColor(0xE6, 0xA2, 0x3C)))
        elif style == 'file':
            paras.append(make_code_para(doc, text, bold=True, color=RGBColor(0x78, 0x78, 0x78)))
        elif style == 'comment':
            paras.append(make_code_para(doc, text, color=RGBColor(0x90, 0x93, 0x99)))
        elif style == 'sep':
            p = make_code_para(doc, '')
            p.paragraph_format.space_before = Pt(2)
            paras.append(p)
        else:
            paras.append(make_code_para(doc, text))

    insert_after_last(doc, paras)
    return True


# ====================================================================
print('Opening document...')
doc = Document(DOC_PATH)
print(f'Paragraphs: {len(doc.paragraphs)}')

# ---------- 2.1 ----------
print('2.1 Adding intervention record...')
add_section(doc, '2.2 干预记录列表页', [
    ('file', '📄 前端位置: templates/risk_list.html —— 干预按钮 + 弹窗表单'),
    (None, '<!-- 操作列新增干预按钮 -->'),
    (None, '<button class="layui-btn layui-btn-xs btn-intervene"'),
    (None, '   data-id="{{d.EmployeeNumber}}" data-name="{{d.real_name}}"'),
    (None, '   style="background:#ff9800;border-color:#ff9800;">'),
    (None, '  <i class="layui-icon layui-icon-edit"></i> 干预'),
    (None, '</button>'),
    ('sep', ''),
    (None, '<!-- 隐藏表单弹窗容器（type:1 方式渲染） -->'),
    (None, '<div id="interveneFormBox" style="display:none;padding:18px 20px 0;">'),
    (None, '  <div class="layui-form">'),
    (None, '    <div class="layui-form-item">'),
    (None, '      <label class="layui-form-label">员工编号</label>'),
    (None, '      <input id="iv-employee_id" class="layui-input" readonly>'),
    (None, '    </div>'),
    (None, '    <div class="layui-form-item">'),
    (None, '      <label class="layui-form-label">干预类型</label>'),
    (None, '      <select id="iv-type">'),
    (None, '        <option value="调薪">调薪</option>'),
    (None, '        <option value="转岗">转岗</option>'),
    (None, '        <option value="面谈">面谈</option>'),
    (None, '        <option value="培训">培训</option>'),
    (None, '        <option value="其他">其他</option>'),
    (None, '      </select>'),
    (None, '    </div>'),
    (None, '    <div class="layui-form-item">'),
    (None, '      <label class="layui-form-label">具体描述</label>'),
    (None, '      <textarea id="iv-description" class="layui-textarea"'),
    (None, '          placeholder="记录原因和措施内容"></textarea>'),
    (None, '    </div>'),
    (None, '    <div class="layui-form-item">'),
    (None, '      <label class="layui-form-label">处理结果</label>'),
    (None, '      <textarea id="iv-result" class="layui-textarea"'),
    (None, '          placeholder="可选，处理后补充"></textarea>'),
    (None, '    </div>'),
    (None, '  </div>'),
    (None, '</div>'),
    ('sep', ''),
    (None, '/* JS: 点击干预按钮 -> layer.open 弹窗 -> AJAX POST */'),
    (None, '$(document).on("click", ".btn-intervene", function() {'),
    (None, '  var empId = $(this).data("id");'),
    (None, '  var empName = $(this).data("name") || "";'),
    (None, '  $("#iv-employee_id").val(empId);'),
    (None, '  layer.open({'),
    (None, '    type: 1, title: "添加干预记录 - " + empName,'),
    (None, '    area: ["500px", "420px"],'),
    (None, '    content: $("#interveneFormBox"),'),
    (None, '    btn: ["确认提交", "取消"],'),
    (None, '    yes: function(idx) {'),
    (None, '      $.post("/predict/api/interventions", {'),
    (None, '        employee_id: $("#iv-employee_id").val(),'),
    (None, '        type: $("#iv-type").val(),'),
    (None, '        description: $("#iv-description").val(),'),
    (None, '        result: $("#iv-result").val(),'),
    (None, '        operator: "{{ username }}"'),
    (None, '      }, function(r) {'),
    (None, '        if(r.code === 0) {'),
    (None, '          layer.msg("干预记录已保存", {icon:1});'),
    (None, '          layer.close(idx);'),
    (None, '        } else { layer.msg(r.msg, {icon:2}); }'),
    (None, '      });'),
    (None, '    }'),
    (None, '  });'),
    (None, '});'),
    ('sep', ''),
    ('be', '【后端代码】'),
    ('file', '📄 后端位置: blueprints/predict.py —— POST /predict/api/interventions'),
    (None, '@predict_bp.route("/api/interventions", methods=["POST"])'),
    (None, 'def api_interventions_create():'),
    (None, '    data = request.get_json(silent=True) or request.form'),
    (None, "    emp_id = data.get('employee_id', type=int)"),
    (None, "    itype = data.get('type', '其他')"),
    (None, "    desc = data.get('description', '')"),
    (None, "    result = data.get('result', '')"),
    (None, "    operator = data.get('operator', session.get('username', ''))"),
    (None, "    if not emp_id:"),
    (None, "        return jsonify({'code': 1, 'msg': '缺少员工编号'})"),
    (None, "    intervention = Intervention("),
    (None, "        employee_id=emp_id, type=itype,"),
    (None, "        description=desc, result=result, operator=operator"),
    (None, "    )"),
    (None, "    db.session.add(intervention)"),
    (None, "    db.session.commit()"),
    (None, "    from utils.logger import log_action"),
    (None, "    log_action('添加干预记录', f'员工#{emp_id}', desc[:60])"),
    (None, "    return jsonify({'code': 0, 'msg': '添加成功'})"),
], title='【核心代码】')

# ---------- 2.2 ----------
print('2.2 Intervention list page...')
add_section(doc, '2.3 员工干预时间线', [
    ('file', '📄 前端位置: templates/interventions.html —— 统计卡片 + 筛选 + Layui 表格'),
    (None, '<!-- 6 个统计卡片 -->'),
    (None, '<div class="stat-grid">'),
    (None, '  <div class="stat-card">'),
    (None, '    <div class="stat-num" id="stat-total">0</div>'),
    (None, '    <div class="stat-label">总干预次数</div>'),
    (None, '  </div>'),
    (None, '  <div class="stat-card salary">'),
    (None, '    <div class="stat-num" id="stat-salary">0</div>'),
    (None, '    <div class="stat-label">调薪</div>'),
    (None, '  </div>'),
    (None, '  <!-- 同样结构: 转岗 | 面谈 | 培训 | 其他 -->'),
    (None, '</div>'),
    ('sep', ''),
    (None, '<!-- 筛选栏 -->'),
    (None, '<div class="filter-bar">'),
    (None, '  <input id="filter-emp-id" placeholder="员工编号">'),
    (None, '  <select id="filter-type">'),
    (None, '    <option value="">全部类型</option>'),
    (None, '    <option value="调薪">调薪</option>'),
    (None, '    ...'),
    (None, '  </select>'),
    (None, '  <button id="btn-query">查询</button>'),
    (None, '</div>'),
    ('sep', ''),
    (None, '<!-- Layui 表格 (注意: 模板用 {% raw %} 包裹, 避免 Jinja2 冲突) -->'),
    (None, 'table.render({'),
    (None, "  elem:'#interv-table', url:'/predict/api/interventions',"),
    (None, "  page:true, limit:15,"),
    (None, '  cols:[[ '),
    (None, "    {field:'employee_id', title:'员工编号', width:100},"),
    (None, "    {field:'department', title:'部门', width:100},"),
    (None, "    {field:'type', title:'干预类型', width:90, templet:'#typeTpl'},"),
    (None, "    {field:'description_short', title:'摘要', minWidth:160},"),
    (None, "    {field:'result', title:'处理结果', width:100},"),
    (None, "    {field:'operator', title:'操作人', width:80},"),
    (None, "    {field:'created_at', title:'时间', width:160},"),
    (None, "    {title:'操作', width:160, templet:'#actionTpl'}"),
    (None, '  ]]'),
    (None, '});'),
    ('sep', ''),
    (None, '{% raw %}  <!-- 类型彩色标签模板 -->'),
    (None, '<script type="text/html" id="typeTpl">'),
    (None, '  <span class="type-tag type-{{d.type}}">{{d.type}}</span>'),
    (None, '</script>'),
    (None, '{% endraw %}'),
    ('sep', ''),
    ('be', '【后端代码】'),
    ('file', '📄 后端位置: blueprints/predict.py —— GET /predict/api/interventions'),
    (None, '@predict_bp.route("/api/interventions", methods=["GET"])'),
    (None, 'def api_interventions_list():'),
    (None, "    page = request.args.get('page', 1, type=int)"),
    (None, "    limit = request.args.get('limit', 15, type=int)"),
    (None, "    emp_id = request.args.get('employee_id', type=int)"),
    (None, "    itype = request.args.get('type', '')"),
    (None, '    query = Intervention.query'),
    (None, '    if emp_id:'),
    (None, '        query = query.filter(Intervention.employee_id == emp_id)'),
    (None, '    if itype:'),
    (None, '        query = query.filter(Intervention.type == itype)'),
    (None, '    pagination = query.order_by(Intervention.created_at.desc())'),
    (None, '        .paginate(page=page, per_page=limit, error_out=False)'),
    (None, '    data = []'),
    (None, '    for inv in pagination.items:'),
    (None, '        emp = inv.employee  # relationship 联查 EmployeeBase'),
    (None, '        data.append({'),
    (None, "            'id': inv.id,"),
    (None, "            'employee_id': inv.employee_id,"),
    (None, "            'employee_name': emp.EmployeeNumber if emp else '',"),
    (None, "            'department': emp.Department if emp else '',"),
    (None, "            'type': inv.type,"),
    (None, "            'description': inv.description or '',"),
    (None, "            'description_short': (inv.description or '')[:30],"),
    (None, "            'result': inv.result or '',"),
    (None, "            'operator': inv.operator,"),
    (None, "            'created_at': inv.created_at.strftime('%Y-%m-%d %H:%M')"),
    (None, '        })'),
    (None, "    return jsonify({'code': 0, 'data': data, 'count': pagination.total})"),
    ('sep', ''),
    ('file', '📄 后端位置: blueprints/predict.py —— GET /predict/api/interventions/stats'),
    (None, '@predict_bp.route("/api/interventions/stats", methods=["GET"])'),
    (None, 'def api_interventions_stats():'),
    (None, '    """按类型统计干预次数"""'),
    (None, '    from sqlalchemy import func'),
    (None, '    counts = db.session.query('),
    (None, '        Intervention.type, func.count(Intervention.id)'),
    (None, '    ).group_by(Intervention.type).all()'),
    (None, "    total = Intervention.query.count()"),
    (None, "    result = {'total': total}"),
    (None, "    for name, cnt in counts:"),
    (None, "        result[name] = cnt"),
    (None, "    return jsonify({'code': 0, 'data': result})"),
], title='【核心代码】')

# ---------- 2.3 ----------
print('2.3 Employee timeline...')
add_section(doc, '2.4 干预效果统计 API', [
    ('file', '📄 前端位置: templates/interventions.html —— 员工信息卡片 + CSS 时间线'),
    (None, '<!-- 员工信息卡片（深色渐变） -->'),
    (None, '<div class="emp-card" style="background:linear-gradient(135deg,#1e3a5f,#2d5a87);'),
    (None, '     color:#fff; border-radius:12px; padding:20px; margin-bottom:18px;">'),
    (None, '  <div class="emp-avatar" id="emp-avatar"></div>'),
    (None, '  <div class="emp-info">'),
    (None, '    <h3 id="emp-name-role"></h3>'),
    (None, '    <div class="emp-detail" id="emp-meta"></div>'),
    (None, '  </div>'),
    (None, '</div>'),
    ('sep', ''),
    (None, '<!-- CSS 时间线（伪元素实现竖线+圆点） -->'),
    (None, '.timeline {'),
    (None, '  position: relative;'),
    (None, '  padding-left: 30px;'),
    (None, '}'),
    (None, '.timeline::before {  /* 竖线 */'),
    (None, "  content: '';"),
    (None, '  position: absolute;'),
    (None, '  left: 10px;'),
    (None, '  top: 0;'),
    (None, '  bottom: 0;'),
    (None, '  width: 2px;'),
    (None, '  background: #e4e7ed;'),
    (None, '}'),
    (None, '.timeline-item {'),
    (None, '  position: relative;'),
    (None, '  margin-bottom: 20px;'),
    (None, '  padding: 10px 14px;'),
    (None, '  background: #f9fafb;'),
    (None, '  border-radius: 8px;'),
    (None, '}'),
    (None, '.timeline-item::before {  /* 圆点 */'),
    (None, "  content: '';"),
    (None, '  position: absolute;'),
    (None, '  left: -24px;'),
    (None, '  top: 12px;'),
    (None, '  width: 10px;'),
    (None, '  height: 10px;'),
    (None, '  border-radius: 50%;'),
    (None, '  background: #409eff;'),
    (None, '  border: 2px solid #fff;'),
    (None, '  box-shadow: 0 0 0 2px #409eff;'),
    (None, '}'),
    ('sep', ''),
    (None, '/* JS: 点击查看详情 -> AJAX 获取员工数据 + 干预历史 */'),
    (None, 'function showEmployeeTimeline(empId) {'),
    (None, '  $.get("/predict/api/interventions/employee/" + empId, function(r) {'),
    (None, '    if(r.code !== 0) return layer.msg("加载失败");'),
    (None, '    var emp = r.data.employee;'),
    (None, '    // 渲染员工信息卡片'),
    (None, "    $('#emp-name-role').text(emp.dept + ' - ' + emp.role);"),
    (None, "    $('#emp-meta').html('司龄:' + emp.tenure + '年 | 薪资:' + emp.income);"),
    (None, '    // 渲染时间线'),
    (None, '    var html = "";'),
    (None, '    r.data.interventions.forEach(function(item) {'),
    (None, '      html += "<div class=\'timeline-item\'>" +'),
    (None, '        "<strong>" + item.type + "</strong>" +'),
    (None, '        "<small> " + item.created_at + " | 操作人: " + item.operator + "</small>" +'),
    (None, '        "<p>" + (item.description || "") + "</p>" +'),
    (None, '        "</div>";'),
    (None, '    });'),
    (None, "    $('#timeline-container').html(html);"),
    (None, '  });'),
    (None, '}'),
    ('sep', ''),
    ('be', '【后端代码】'),
    ('file', '📄 后端位置: blueprints/predict.py —— GET /predict/api/interventions/employee/<id>'),
    (None, '@predict_bp.route("/api/interventions/employee/<int:emp_id>",'),
    (None, '    methods=["GET"])'),
    (None, 'def api_interventions_employee(emp_id):'),
    (None, '    emp = EmployeeBase.query.get(emp_id)'),
    (None, '    if not emp:'),
    (None, "        return jsonify({'code': 1, 'msg': '员工不存在'})"),
    (None, '    job = JobDetail.query.get(emp_id)'),
    (None, '    risk = AttritionRisk.query.get(emp_id)'),
    (None, '    records = Intervention.query'),
    (None, '        .filter_by(employee_id=emp_id)'),
    (None, '        .order_by(Intervention.created_at.desc()).all()'),
    (None, "    return jsonify({'code': 0, 'data': {"),
    (None, "        'employee': {"),
    (None, "            'id': emp.EmployeeNumber,"),
    (None, "            'age': emp.Age,"),
    (None, "            'dept': emp.Department,"),
    (None, "            'role': job.JobRole if job else '',"),
    (None, "            'income': job.MonthlyIncome if job else 0,"),
    (None, "            'tenure': risk.YearsAtCompany if risk else 0,"),
    (None, "            'attrition': risk.Attrition if risk else ''"),
    (None, '        },'),
    (None, "        'interventions': [{"),
    (None, "            'id': r.id, 'type': r.type,"),
    (None, "            'description': r.description, 'result': r.result,"),
    (None, "            'operator': r.operator,"),
    (None, "            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')"),
    (None, '        } for r in records]'),
    (None, '    }})'),
], title='【核心代码】')

# ---------- 2.4 ----------
print('2.4 Effectiveness stats API...')
add_section(doc, '任务三：操作日志系统', [
    ('file', '📄 后端位置: blueprints/predict.py —— GET /predict/api/interventions/effectiveness'),
    (None, '@predict_bp.route("/api/interventions/effectiveness",'),
    (None, '    methods=["GET"])'),
    (None, 'def api_interventions_effectiveness():'),
    (None, '    """'),
    (None, '    统计逻辑:'),
    (None, '    1. 批量预测所有员工, 筛选 probability >= 0.7 的高风险员工'),
    (None, '    2. 查询已有干预的员工 ID 集合'),
    (None, '    3. 分已干预/未干预两组, 对比 Attrition=Yes 的比例'),
    (None, '    """'),
    (None, '    # 1. 联查三表获取完整数据'),
    (None, '    results = db.session.query('),
    (None, '        EmployeeBase, JobDetail, AttritionRisk'),
    (None, '    ).join(...).all()'),
    (None, '    df = pd.DataFrame([{...} for r in results])'),
    (None, '    # 补充默认特征列, 调用 ML 批量预测'),
    (None, '    probs = batch_predict(df)'),
    (None, "    df['probability'] = probs"),
    (None, '    high_risk = df[df["probability"] >= 0.7]'),
    (None, '    '),
    (None, '    # 2. 干预员工 ID 集合'),
    (None, '    intervened_ids = set(r[0] for r in'),
    (None, '        db.session.query(Intervention.employee_id).distinct().all())'),
    (None, '    '),
    (None, '    # 3. 分组计算'),
    (None, '    intervened = high_risk[high_risk["EmployeeNumber"].isin(intervened_ids)]'),
    (None, '    not_intervened = high_risk[~high_risk["EmployeeNumber"].isin(intervened_ids)]'),
    (None, '    '),
    (None, '    def calc(df_group):'),
    (None, '        t = len(df_group)'),
    (None, "        a = int((df_group['Attrition'].astype(str).str.lower() == 'yes').sum())"),
    (None, '        return {"total": t, "attrition": a,'),
    (None, '                "rate": round(a/t*100, 1) if t > 0 else 0}'),
    (None, '    '),
    (None, "    return jsonify({'code': 0, 'data': {"),
    (None, "        'high_risk_total': len(high_risk),"),
    (None, "        'intervened': calc(intervened),"),
    (None, "        'not_intervened': calc(not_intervened)"),
    (None, '    }})'),
    ('sep', ''),
    (None, '# 返回示例:'),
    (None, '# {'),
    (None, "#   'high_risk_total': 52,"),
    (None, "#   'intervened':     {'total': 5,  'attrition': 0,  'rate': 0.0},"),
    (None, "#   'not_intervened': {'total': 47, 'attrition': 38, 'rate': 80.8}"),
    (None, '# }'),
], title='【核心代码】')

# ---------- 3.1 ----------
print('3.1 Log utility function...')
add_section(doc, '3.2 关键操作埋点', [
    ('file', '📄 文件位置: utils/logger.py —— 封装通用日志函数, 一行调用即可'),
    (None, '"""'),
    (None, '操作日志工具函数 —— 一行代码记录日志'),
    (None, '用法: from utils.logger import log_action'),
    (None, "      log_action('删除员工', '员工编号1001', '姓名：张三，部门：研发部')"),
    (None, '"""'),
    (None, 'from flask import session, request, has_request_context'),
    (None, 'from db_model import db, OperationLog'),
    (None, ''),
    (None, "def log_action(action, target='', detail=''):"),
    (None, '    """'),
    (None, '    记录操作日志。'),
    (None, '    自动从 session 获取 user_id/username，'),
    (None, '    从 request.remote_addr 获取 IP 地址。'),
    (None, '    若不在请求上下文中则静默跳过。'),
    (None, '    """'),
    (None, '    if not has_request_context():'),
    (None, '        return  # 非请求环境（命令行、定时任务）静默跳过'),
    (None, ''),
    (None, '    try:'),
    (None, "        user_id = session.get('user_id')"),
    (None, "        username = session.get('username', '')"),
    (None, "        ip = request.remote_addr or ''"),
    (None, ''),
    (None, '        log_entry = OperationLog('),
    (None, '            user_id=user_id,'),
    (None, '            username=username,'),
    (None, '            action=action,'),
    (None, '            target=str(target),'),
    (None, '            detail=str(detail),'),
    (None, '            ip=ip,'),
    (None, '        )'),
    (None, '        db.session.add(log_entry)'),
    (None, '        db.session.commit()'),
    (None, '    except Exception:'),
    (None, '        # 日志记录失败不应影响主业务流程'),
    (None, '        pass'),
    ('sep', ''),
    (None, '# ======== 调用示例 ========'),
    (None, "log_action('删除员工', '员工编号1001', '姓名：张三，部门：研发部')"),
    (None, "log_action('登录成功', username, f'角色: {user.role}')"),
    (None, "log_action('批量预测', '', f'共 {len(results)} 名员工')"),
    ('sep', ''),
    ('file', '📄 新增模型: db_model.py —— OperationLog 表'),
    (None, 'class OperationLog(db.Model):'),
    (None, "    __tablename__ = 'operation_logs'"),
    (None, '    id = db.Column(db.Integer, primary_key=True, autoincrement=True)'),
    (None, "    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),"),
    (None, '        nullable=True, comment="操作人用户ID")'),
    (None, "    username = db.Column(db.String(50), default='',"),
    (None, '        comment="操作人姓名（冗余,便于查询）")'),
    (None, "    action = db.Column(db.String(50), nullable=False,"),
    (None, '        comment="操作类型: 登录成功/删除员工/批量预测...")'),
    (None, "    target = db.Column(db.String(200), default='',"),
    (None, '        comment="操作对象: 员工编号/用户名/文件名")'),
    (None, "    detail = db.Column(db.Text, default='',"),
    (None, '        comment="详细信息")'),
    (None, "    ip = db.Column(db.String(50), default='',"),
    (None, '        comment="客户端IP地址")'),
    (None, '    created_at = db.Column(db.DateTime, default=datetime.now)'),
    (None, "    user = db.relationship('User', backref='operation_logs')"),
], title='【核心代码】')

# ---------- 3.2 ----------
print('3.2 Operation log placement...')
add_section(doc, '3.3 日志查看页', [
    ('file', '📄 app.py —— 登录相关 (3 处)'),
    (None, '# === 登录成功（login 视图, 验证通过后） ==='),
    (None, "log_action('登录成功', username, f'角色: {user.role}')"),
    (None, ''),
    (None, '# === 登录失败（login 视图, 验证失败后） ==='),
    (None, "log_action('登录失败', username or '', '密码错误或用户不存在')"),
    (None, ''),
    (None, '# === 退出登录（logout 视图） ==='),
    (None, "log_action('退出登录', '', '')"),
    ('sep', ''),
    ('file', '📄 blueprints/employee.py —— 员工管理 (3 处)'),
    (None, '# add_employee: commit 成功后'),
    (None, "log_action('新增员工', f'员工编号{emp_id}', f'姓名：{name}')"),
    (None, ''),
    (None, '# edit_employee: commit 成功后'),
    (None, "log_action('编辑员工', f'员工编号{emp_id}', f'更新: {changed_fields}')"),
    (None, ''),
    (None, '# delete_employee: commit 成功后'),
    (None, "log_action('删除员工', f'员工编号{emp_id}', '')"),
    ('sep', ''),
    ('file', '📄 blueprints/predict.py —— 预测 + 报告 (6 处)'),
    (None, "# api_predict:     log_action('单次预测', f'员工#{eid}', f'风险:{level}')"),
    (None, "# api_batch:       log_action('批量预测', '', f'共{len(res)}名员工')"),
    (None, "# api_generate:    log_action('生成报告', filename, f'类型:{ftype}')"),
    (None, "# api_download:    log_action('下载报告', filename, '')"),
    (None, "# api_send_mail:   log_action('发送报告邮件', email, f'附件:{name}')"),
    (None, "# api_interventions_create: log_action('添加干预记录', ...)"),
    ('sep', ''),
    ('file', '📄 blueprints/user.py —— 用户管理 (2 处)'),
    (None, "# add_user:        log_action('创建用户', username, f'姓名：{real_name}')"),
    (None, "# change_password: log_action('修改密码', user.username, '密码已更新')"),
], title='【核心代码】')

# ---------- 3.3 ----------
print('3.3 Log viewer page...')
add_section(doc, '3.4 我的操作记录', [
    ('file', '📄 前端位置: templates/log_list.html'),
    (None, '<!-- 筛选栏 -->'),
    (None, '<div class="filter-bar">'),
    (None, '  <input id="filter-username" placeholder="输入用户名">'),
    (None, '  <select id="filter-action"><option value="">全部类型</option></select>'),
    (None, '  <input type="text" id="filter-start" readonly> —'),
    (None, '  <input type="text" id="filter-end" readonly>'),
    (None, '  <button id="btn-query">查询</button>'),
    (None, '  <button id="btn-reset">重置</button>'),
    (None, '  <span id="total-info">共 0 条</span>'),
    (None, '</div>'),
    ('sep', ''),
    (None, '<!-- Layui 表格（6 列） -->'),
    (None, 'table.render({'),
    (None, "  elem:'#log-table', url:'/predict/api/logs', page:true, limit:15,"),
    (None, '  cols:[[ '),
    (None, "    {field:'created_at', title:'操作时间', width:170},"),
    (None, "    {field:'username', title:'操作人', width:100},"),
    (None, "    {field:'action', title:'操作类型', width:120, templet:'#actionTpl'},"),
    (None, "    {field:'target', title:'操作对象', width:160},"),
    (None, "    {field:'detail_short', title:'描述', minWidth:180},"),
    (None, "    {field:'ip', title:'IP地址', width:130}"),
    (None, '  ]]'),
    (None, '});'),
    ('sep', ''),
    (None, '<!-- 操作类型彩色标签 -->'),
    (None, '.action-登录成功 { background:#5FB878; }'),
    (None, '.action-登录失败 { background:#FF5722; }'),
    (None, '.action-删除员工 { background:#FF5722; }'),
    (None, '.action-新增员工 { background:#409EFF; }'),
    (None, '.action-批量预测 { background:#6366f1; }'),
    (None, '.action-生成报告 { background:#14B8A6; }'),
    ('sep', ''),
    (None, '<!-- Jinja2 与 Layui 模板冲突解决方案: {% raw %} 包裹 -->'),
    (None, '{% raw %}'),
    (None, '<script type="text/html" id="actionTpl">'),
    (None, '  <span class="action-tag action-{{d.action}}">{{d.action}}</span>'),
    (None, '</script>'),
    (None, '{% endraw %}'),
    ('sep', ''),
    ('be', '【后端代码】'),
    ('file', '📄 后端位置: blueprints/predict.py —— GET /predict/api/logs + GET /predict/api/logs/actions'),
    (None, '@predict_bp.route("/api/logs", methods=["GET"])'),
    (None, 'def api_logs_list():'),
    (None, '    """分页 + 筛选: 操作人(username模糊), 类型(action精确), 时间范围"""'),
    (None, "    username = request.args.get('username', '')"),
    (None, "    action = request.args.get('action', '')"),
    (None, "    start_date = request.args.get('start_date', '')"),
    (None, "    end_date = request.args.get('end_date', '')"),
    (None, ''),
    (None, '    query = OperationLog.query'),
    (None, '    if username:'),
    (None, "        query = query.filter(OperationLog.username.like(f'%{username}%'))"),
    (None, '    if action:'),
    (None, '        query = query.filter(OperationLog.action == action)'),
    (None, '    if start_date:'),
    (None, '        query = query.filter(OperationLog.created_at >= ...)'),
    (None, '    if end_date:'),
    (None, '        query = query.filter(OperationLog.created_at <= ...)'),
    (None, ''),
    (None, '    total = query.count()'),
    (None, '    logs = query.order_by(OperationLog.created_at.desc())'),
    (None, '        .offset((page-1)*limit).limit(limit).all()'),
    (None, "    return jsonify({'code': 0, 'data': data, 'count': total})"),
    ('sep', ''),
    ('file', '📄 后端位置: app.py —— 页面路由 /log/list'),
    (None, "@app.route('/log/list')"),
    (None, 'def log_list():'),
    (None, "    if 'user_id' not in session:"),
    (None, "        return redirect(url_for('index'))"),
    (None, "    return render_template('log_list.html')"),
    ('sep', ''),
    ('file', '📄 侧边栏: templates/home.html 新增操作日志入口'),
    (None, '<!-- 在侧边栏 ul 中添加 -->'),
    (None, '<li class="layui-nav-item">'),
    (None, '  <a href="/log/list" target="mainFrame">操作日志</a>'),
    (None, '</li>'),
], title='【核心代码】')

# ---------- 3.4 ----------
print('3.4 My operation records...')
add_section(doc, '3.5 日志统计 API', [
    ('file', '📄 前端位置: templates/user/my_logs.html'),
    (None, '<!-- 与 log_list.html 结构一致, 区别: -->'),
    (None, '<!-- 1. 数据源改为 /log/api/my -->'),
    (None, '<!-- 2. 表格去掉 username(操作人) 列 -->'),
    (None, '<!-- 3. 筛选栏去掉"操作人"输入框 -->'),
    (None, 'table.render({'),
    (None, "  elem:'#log-table', url:'/log/api/my', page:true,"),
    (None, '  cols:[[ '),
    (None, "    {field:'created_at', title:'操作时间', width:170},"),
    (None, "    {field:'action', title:'操作类型', width:120, templet:'#actionTpl'},"),
    (None, "    {field:'target', title:'操作对象', width:160},"),
    (None, "    {field:'detail_short', title:'描述', minWidth:200},"),
    (None, "    {field:'ip', title:'IP地址', width:130}"),
    (None, '    // ↑ 无 username 列（都是自己）'),
    (None, '  ]]'),
    (None, '});'),
    ('sep', ''),
    ('file', '📄 入口: templates/user/profile.html 个人中心新增链接'),
    (None, '<!-- 在"修改密码"卡片前插入 -->'),
    (None, '<div class="card" style="text-align:center;padding:18px 32px;">'),
    (None, '  <a href="/log/my" target="mainFrame"'),
    (None, '     style="color:#409eff;font-size:15px;text-decoration:none;">'),
    (None, '    <i class="layui-icon layui-icon-log"></i> 我的操作记录'),
    (None, '  </a>'),
    (None, '</div>'),
    ('sep', ''),
    ('be', '【后端代码】'),
    ('file', '📄 后端位置: app.py —— GET /log/api/my (按 user_id 过滤)'),
    (None, "@app.route('/log/api/my')"),
    (None, 'def api_my_logs():'),
    (None, '    """仅返回当前登录用户的操作日志"""'),
    (None, "    if 'user_id' not in session:"),
    (None, "        return jsonify({'code': 401, 'msg': '请先登录'})"),
    (None, '    query = OperationLog.query.filter('),
    (None, "        OperationLog.user_id == session['user_id']"),
    (None, '    )'),
    (None, "    if request.args.get('action'):"),
    (None, '        query = query.filter('),
    (None, "            OperationLog.action == request.args.get('action'))"),
    (None, '    # ... 时间范围筛选同上 ...'),
    (None, '    total = query.count()'),
    (None, '    logs = query.order_by(OperationLog.created_at.desc())'),
    (None, '        .offset((page-1)*limit).limit(limit).all()'),
    (None, "    return jsonify({'code': 0, 'data': data, 'count': total})"),
    ('sep', ''),
    ('file', '📄 后端位置: app.py —— 我的日志页面路由'),
    (None, "@app.route('/log/my')"),
    (None, 'def my_logs_page():'),
    (None, "    if 'user_id' not in session:"),
    (None, "        return redirect(url_for('index'))"),
    (None, "    return render_template('user/my_logs.html')"),
], title='【核心代码】')

# ---------- 3.5 ----------
print('3.5 Log stats API...')
add_section(doc, '3.6（选做）旧日志清理', [
    ('file', '📄 后端位置: app.py —— GET /log/api/stats/today'),
    (None, "@app.route('/log/api/stats/today')"),
    (None, 'def api_log_stats_today():'),
    (None, '    """返回今日操作总数 + 各类型分布（供工作台可视化调用）"""'),
    (None, '    from datetime import datetime as dt'),
    (None, '    from sqlalchemy import func'),
    (None, '    today_start = dt.now().replace('),
    (None, '        hour=0, minute=0, second=0, microsecond=0)'),
    (None, ''),
    (None, '    query = OperationLog.query.filter('),
    (None, '        OperationLog.created_at >= today_start)'),
    (None, '    total = query.count()'),
    (None, ''),
    (None, '    type_counts = db.session.query('),
    (None, '        OperationLog.action, func.count(OperationLog.id)'),
    (None, '    ).filter('),
    (None, '        OperationLog.created_at >= today_start'),
    (None, '    ).group_by(OperationLog.action)'),
    (None, '     .order_by(func.count(OperationLog.id).desc()).all()'),
    (None, ''),
    (None, "    return jsonify({'code': 0, 'data': {"),
    (None, "        'today_total': total,"),
    (None, "        'type_distribution': ["),
    (None, "            {'action': a, 'count': c} for a, c in type_counts"),
    (None, '        ]'),
    (None, '    }})'),
    ('sep', ''),
    (None, '# 返回示例:'),
    (None, '# {"today_total": 63, "type_distribution": ['),
    (None, '#   {"action": "批量预测", "count": 41},'),
    (None, '#   {"action": "登录成功", "count": 7},'),
    (None, '#   {"action": "登录失败", "count": 9}, ...]}'),
], title='【核心代码】')

# ---------- 3.6 ----------
print('3.6 Old log cleanup...')
add_section_end(doc, [
    ('file', '📄 前端位置: templates/log_list.html —— 红色清理按钮'),
    (None, '<!-- 在筛选栏重置按钮后添加 -->'),
    (None, '<button class="layui-btn layui-btn-sm layui-btn-danger"'),
    (None, '        id="btn-clean" style="height:36px;border-radius:6px;">'),
    (None, '  <i class="layui-icon layui-icon-delete"></i> 清理旧日志'),
    (None, '</button>'),
    ('sep', ''),
    (None, '/* JS: 确认弹窗 -> AJAX POST */'),
    (None, "$('#btn-clean').click(function(){"),
    (None, '  layer.confirm('),
    (None, "    '确认删除 <strong style=\"color:#FF5722;\">90 天前</strong> 的日志？',"),
    (None, "    {title:'清理旧日志', icon:3, btn:['确认清理','取消']},"),
    (None, '    function(idx){'),
    (None, '      layer.close(idx);'),
    (None, "      $.post('/log/api/clean', function(res){"),
    (None, "        if(res.code === 0){"),
    (None, "          layer.msg('成功清理 ' + res.deleted + ' 条旧日志');"),
    (None, '          tableIns.reload();'),
    (None, '        }'),
    (None, '      });'),
    (None, '    }'),
    (None, '  );'),
    (None, '});'),
    ('sep', ''),
    ('be', '【后端代码】'),
    ('file', '📄 后端位置: app.py —— POST /log/api/clean (仅管理员)'),
    (None, "@app.route('/log/api/clean', methods=['POST'])"),
    (None, 'def api_log_clean():'),
    (None, '    """删除 90 天前的日志记录"""'),
    (None, "    if session.get('role') != 'admin':"),
    (None, "        return jsonify({'code': 403, 'msg': '仅管理员可操作'})"),
    (None, '    from datetime import datetime as dt, timedelta'),
    (None, '    cutoff = dt.now() - timedelta(days=90)'),
    (None, '    count = OperationLog.query.filter('),
    (None, '        OperationLog.created_at < cutoff).delete()'),
    (None, '    db.session.commit()'),
    (None, "    return jsonify({'code': 0,"),
    (None, "        'msg': f'成功清理 {count} 条旧日志',"),
    (None, "        'deleted': count})"),
], title='【核心代码】')

# ========== Save ==========
print(f'\nSaving to: {DOC_PATH}')
doc.save(DOC_PATH)
print('Done!')

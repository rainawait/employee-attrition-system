from flask import Blueprint, render_template, request, jsonify, send_file
from db_model import db, EmployeeBase, JobDetail, AttritionRisk
import json
import pandas as pd
from io import BytesIO

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

# 员工列表页面
@employee_bp.route('/list')
def employee_list():
    return render_template("employee.html")

# 分页+三表联查+多条件筛选接口
@employee_bp.route('/api/employees')
def api_employees():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    department = request.args.get('department', '').strip()
    gender = request.args.get('gender', '').strip()
    keyword = request.args.get('keyword', '').strip()

    query = db.session.query(
        EmployeeBase.EmployeeNumber,
        EmployeeBase.Age,
        EmployeeBase.Gender,
        EmployeeBase.MaritalStatus,
        EmployeeBase.EducationField,
        EmployeeBase.Department,
        EmployeeBase.DistanceFromHome,
        JobDetail.JobRole,
        JobDetail.MonthlyIncome,
        JobDetail.JobLevel,
        JobDetail.TotalWorkingYears,
        AttritionRisk.Attrition,
        AttritionRisk.OverTime,
        AttritionRisk.JobSatisfaction
    ).join(
        JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
    ).join(
        AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
    )

    if department:
        query = query.filter(EmployeeBase.Department == department)
    if gender:
        query = query.filter(EmployeeBase.Gender == gender)
    if keyword:
        query = query.filter(
            EmployeeBase.EmployeeNumber.like(f'%{keyword}%') |
            JobDetail.JobRole.like(f'%{keyword}%')
        )

    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    employees = []
    for r in pagination.items:
        employees.append({
            'EmployeeNumber': r.EmployeeNumber,
            'Age': r.Age,
            'Gender': r.Gender,
            'Department': r.Department,
            'MaritalStatus': r.MaritalStatus,
            'EducationField': r.EducationField,
            'DistanceFromHome': r.DistanceFromHome,
            'JobRole': r.JobRole,
            'JobLevel': r.JobLevel,
            'MonthlyIncome': r.MonthlyIncome,
            'TotalWorkingYears': r.TotalWorkingYears,
            'Attrition': r.Attrition,
            'OverTime': r.OverTime,
            'JobSatisfaction': r.JobSatisfaction
        })
    return jsonify({"code":0, "count":pagination.total, "data":employees})

# 1. 添加员工接口
@employee_bp.route('/api/add', methods=['POST'])
def add_employee():
    try:
        data = request.form
        emp_id_str = data.get('EmployeeNumber')
        if not emp_id_str:
            return jsonify({"code":400, "msg":"工号不能为空"}),400
        emp_id = int(emp_id_str)
        if EmployeeBase.query.get(emp_id):
            return jsonify({"code":400, "msg":f"工号{emp_id}已存在，不可重复添加"}),400

        emp_base = EmployeeBase(
            EmployeeNumber=emp_id,
            Age=int(data.get('Age')),
            Gender=data.get('Gender'),
            MaritalStatus=data.get('MaritalStatus','Single'),
            EducationField=data.get('EducationField',''),
            Department=data.get('Department'),
            DistanceFromHome=int(data.get('DistanceFromHome')) if data.get('DistanceFromHome') else 0
        )
        db.session.add(emp_base)

        job_detail = JobDetail(
            EmployeeNumber=emp_id,
            JobRole=data.get('JobRole'),
            JobLevel=int(data.get('JobLevel')) if data.get('JobLevel') else 1,
            MonthlyIncome=float(data.get('MonthlyIncome')),
            TotalWorkingYears=int(data.get('TotalWorkingYears')) if data.get('TotalWorkingYears') else 0,
            NumCompaniesWorked=0, YearsInCurrentRole=0, YearsSinceLastPromotion=0, YearsWithCurrManager=0
        )
        db.session.add(job_detail)

        attrition_risk = AttritionRisk(
            EmployeeNumber=emp_id,
            Attrition=data.get('Attrition','No'),
            OverTime=data.get('OverTime','No'),
            JobSatisfaction=int(data.get('JobSatisfaction')) if data.get('JobSatisfaction') else 4,
            WorkLifeBalance=3, EnvironmentSatisfaction=3, JobInvolvement=3, RelationshipSatisfaction=3, YearsAtCompany=0
        )
        db.session.add(attrition_risk)
        db.session.commit()
        from utils.logger import log_action
        log_action('新增员工', f'员工编号 {emp_id}', f'姓名：{data.get("real_name","")}, 部门：{data.get("Department","")}')
        return jsonify({"code":0, "msg":"员工添加成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code":500, "msg":f"服务器错误：{str(e)}"}),500

# 2. 编辑更新员工接口
@employee_bp.route('/api/edit', methods=['POST'])
def edit_employee():
    try:
        data = request.form
        emp_id_str = data.get('EmployeeNumber')
        if not emp_id_str:
            return jsonify({"code":400, "msg":"未获取有效员工工号"}),400
        emp_id = int(emp_id_str)

        emp_base = EmployeeBase.query.get(emp_id)
        job_detail = JobDetail.query.get(emp_id)
        attrition_risk = AttritionRisk.query.get(emp_id)
        if not emp_base:
            return jsonify({"code":400, "msg":f"工号{emp_id}员工不存在"}),400

        # 更新基础表
        emp_base.Age = int(data.get('Age'))
        emp_base.Gender = data.get('Gender')
        emp_base.MaritalStatus = data.get('MaritalStatus','Single')
        emp_base.Department = data.get('Department')
        emp_base.EducationField = data.get('EducationField','')
        emp_base.DistanceFromHome = int(data.get('DistanceFromHome')) if data.get('DistanceFromHome') else 0

        # 更新工作详情表
        if not job_detail:
            job_detail = JobDetail(EmployeeNumber=emp_id)
            db.session.add(job_detail)
        job_detail.JobRole = data.get('JobRole')
        job_detail.JobLevel = int(data.get('JobLevel')) if data.get('JobLevel') else 1
        job_detail.MonthlyIncome = float(data.get('MonthlyIncome'))
        job_detail.TotalWorkingYears = int(data.get('TotalWorkingYears')) if data.get('TotalWorkingYears') else 0

        # 更新离职风险表
        if not attrition_risk:
            attrition_risk = AttritionRisk(EmployeeNumber=emp_id)
            db.session.add(attrition_risk)
        attrition_risk.Attrition = data.get('Attrition','No')
        attrition_risk.OverTime = data.get('OverTime','No')
        attrition_risk.JobSatisfaction = int(data.get('JobSatisfaction')) if data.get('JobSatisfaction') else 4

        db.session.commit()
        from utils.logger import log_action
        log_action('编辑员工', f'员工编号 {emp_id}', f'部门：{data.get("Department","")}, 岗位：{data.get("JobRole","")}')
        return jsonify({"code":0, "msg":"修改成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code":500, "msg":f"修改失败：{str(e)}"}),500

# 3. 单行删除员工接口
@employee_bp.route('/api/delete', methods=['POST'])
def delete_employee():
    try:
        emp_id_str = request.form.get('EmployeeNumber')
        if not emp_id_str:
            return jsonify({"code":-1, "msg":"参数缺失：员工工号不能为空"}),400
        emp_id = int(emp_id_str)

        emp_base = EmployeeBase.query.get(emp_id)
        job_detail = JobDetail.query.get(emp_id)
        attrition_risk = AttritionRisk.query.get(emp_id)
        if not emp_base:
            return jsonify({"code":-1, "msg":f"工号{emp_id}员工不存在"}),400

        # 按从表→主表顺序删除（外键约束）
        if attrition_risk:
            db.session.delete(attrition_risk)
        if job_detail:
            db.session.delete(job_detail)
        if emp_base:
            db.session.delete(emp_base)
        db.session.commit()
        from utils.logger import log_action
        log_action('删除员工', f'员工编号 {emp_id}', '')
        return jsonify({"code":0, "msg":"删除成功"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code":-1, "msg":f"删除失败：{str(e)}"}),500

# ========== 新增练习1：批量删除接口 ==========
@employee_bp.route('/api/batch_delete', methods=['POST'])
def batch_delete():
    try:
        emp_ids_str = request.form.get('emp_ids')
        if not emp_ids_str:
            return jsonify({"code":400, "msg":"未选择任何员工"}),400
        emp_id_list = json.loads(emp_ids_str)
        delete_count = 0
        for emp_id in emp_id_list:
            emp_id = int(emp_id)
            emp_base = EmployeeBase.query.get(emp_id)
            if not emp_base:
                continue
            job_detail = JobDetail.query.get(emp_id)
            attrition_risk = AttritionRisk.query.get(emp_id)
            # 从表先删
            if attrition_risk:
                db.session.delete(attrition_risk)
            if job_detail:
                db.session.delete(job_detail)
            db.session.delete(emp_base)
            delete_count += 1
        db.session.commit()
        return jsonify({"code":0, "msg":"批量删除完成", "count":delete_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code":500, "msg":f"批量删除失败：{str(e)}"}),500

# ========== 新增练习2：导出CSV接口 ==========
@employee_bp.route('/api/export_csv')
def export_csv():
    # 接收前端搜索筛选参数，和列表查询共用过滤逻辑
    department = request.args.get('department', '').strip()
    gender = request.args.get('gender', '').strip()
    keyword = request.args.get('keyword', '').strip()

    query = db.session.query(
        EmployeeBase.EmployeeNumber.label("工号"),
        EmployeeBase.Age.label("年龄"),
        EmployeeBase.Gender.label("性别"),
        EmployeeBase.MaritalStatus.label("婚姻状况"),
        EmployeeBase.EducationField.label("专业领域"),
        EmployeeBase.Department.label("部门"),
        EmployeeBase.DistanceFromHome.label("通勤距离(公里)"),
        JobDetail.JobRole.label("工作角色"),
        JobDetail.JobLevel.label("工作级别"),
        JobDetail.MonthlyIncome.label("月收入"),
        JobDetail.TotalWorkingYears.label("总工作年限"),
        AttritionRisk.Attrition.label("是否离职"),
        AttritionRisk.OverTime.label("是否加班"),
        AttritionRisk.JobSatisfaction.label("工作满意度(1-4)")
    ).join(
        JobDetail, EmployeeBase.EmployeeNumber == JobDetail.EmployeeNumber
    ).join(
        AttritionRisk, EmployeeBase.EmployeeNumber == AttritionRisk.EmployeeNumber
    )

    # 拼接筛选条件，和列表保持一致
    if department:
        query = query.filter(EmployeeBase.Department == department)
    if gender:
        query = query.filter(EmployeeBase.Gender == gender)
    if keyword:
        query = query.filter(
            EmployeeBase.EmployeeNumber.like(f'%{keyword}%') |
            JobDetail.JobRole.like(f'%{keyword}%')
        )
    all_data = query.all()
    # 转为DataFrame
    df = pd.DataFrame([row._asdict() for row in all_data])
    # 内存字节流生成CSV，不生成本地文件
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    # 返回文件下载
    return send_file(
        BytesIO(output.getvalue()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="员工数据.csv"
    )
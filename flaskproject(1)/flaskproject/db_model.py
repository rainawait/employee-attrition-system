from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 仅初始化db，不和app耦合
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    real_name = db.Column(db.String(50), comment="真实姓名")
    email = db.Column(db.String(100), comment="邮箱")
    phone = db.Column(db.String(20), comment="手机号")
    department = db.Column(db.String(50), comment="部门")
    role = db.Column(db.String(20), default='user', nullable=False, comment='角色admin/user')
    status = db.Column(db.String(10), default='active', nullable=False, comment='active正常/disabled禁用')
    avatar = db.Column(db.String(200), default="", comment="头像静态路径")
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# 员工基础信息表
class EmployeeBase(db.Model):
    """员工基础信息表"""
    __tablename__ = 'employee_base'
    EmployeeNumber = db.Column(db.Integer, primary_key=True)
    Age = db.Column(db.Integer)
    Gender = db.Column(db.String(10))
    MaritalStatus = db.Column(db.String(20))
    EducationField = db.Column(db.String(50))
    Department = db.Column(db.String(50))
    DistanceFromHome = db.Column(db.Integer)
    record_date = db.Column(db.DateTime, default=datetime.now, comment='记录日期-用于时间范围筛选')

# 工作详情表（工号作为外键+主键，一对一关联员工表）
class JobDetail(db.Model):
    """工作详情表"""
    __tablename__ = 'job_detail'
    EmployeeNumber = db.Column(db.Integer, db.ForeignKey('employee_base.EmployeeNumber'), primary_key=True, nullable=False)
    JobRole = db.Column(db.String(50))
    JobLevel = db.Column(db.Integer)
    MonthlyIncome = db.Column(db.Float)
    NumCompaniesWorked = db.Column(db.Integer)
    TotalWorkingYears = db.Column(db.Integer)
    YearsInCurrentRole = db.Column(db.Integer)
    YearsSinceLastPromotion = db.Column(db.Integer)
    YearsWithCurrManager = db.Column(db.Integer)

# 离职预警因素表
class AttritionRisk(db.Model):
    """预警因素表"""
    __tablename__ = 'attrition_risk'
    EmployeeNumber = db.Column(db.Integer, db.ForeignKey('employee_base.EmployeeNumber'), primary_key=True, nullable=False)
    Attrition = db.Column(db.String(5))
    OverTime = db.Column(db.String(5))
    WorkLifeBalance = db.Column(db.Integer)
    JobSatisfaction = db.Column(db.Integer)
    EnvironmentSatisfaction = db.Column(db.Integer)
    JobInvolvement = db.Column(db.Integer)
    RelationshipSatisfaction = db.Column(db.Integer)
    YearsAtCompany = db.Column(db.Integer)


# 报告生成记录表
class ReportRecord(db.Model):
    """每次生成报告的记录"""
    __tablename__ = 'report_records'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(200), comment='文件名')
    file_type = db.Column(db.String(10), comment='PNG / Excel / PDF')
    file_size = db.Column(db.Integer, comment='文件大小（字节）')
    filters = db.Column(db.Text, comment='筛选条件 JSON')
    generated_by = db.Column(db.String(50), comment='生成人')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='生成时间')


# 干预措施跟踪表
class Intervention(db.Model):
    """HR 对高风险员工采取的干预措施记录"""
    __tablename__ = 'interventions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_base.EmployeeNumber'), nullable=False, comment='员工工号')
    type = db.Column(db.String(20), default='其他', comment='干预类型：调薪/转岗/面谈/培训/其他')
    description = db.Column(db.Text, default='', comment='具体描述')
    result = db.Column(db.Text, default='', comment='处理结果（可后续补充）')
    operator = db.Column(db.String(50), default='', comment='操作人姓名')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联员工表，方便联查姓名、部门
    employee = db.relationship('EmployeeBase', backref='interventions')


# 操作日志表
class OperationLog(db.Model):
    """系统操作日志 —— 所有关键操作可追溯"""
    __tablename__ = 'operation_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='操作人用户ID')
    username = db.Column(db.String(50), default='', comment='操作人姓名（冗余）')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    target = db.Column(db.String(200), default='', comment='操作对象')
    detail = db.Column(db.Text, default='', comment='补充描述')
    ip = db.Column(db.String(50), default='', comment='操作IP地址')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联用户表
    user = db.relationship('User', backref='operation_logs')
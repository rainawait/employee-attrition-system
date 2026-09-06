"""
报告模块统一配置：字体、配色、画布参数
"""
import matplotlib.pyplot as plt
import matplotlib

# 配置中文字体——必须在任何绘图代码之前执行
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方框的问题

# 统一配色方案
COLORS = {
    'primary':   '#409EFF',  # 主色-蓝
    'success':   '#5FB878',  # 成功-绿
    'warning':   '#FFB800',  # 警告-黄
    'danger':    '#FF5722',  # 危险-红
    'dark':      '#303133',  # 深色文字
    'gray':      '#C0C4CC',  # 浅灰辅助
}

# 画布参数
A4_SIZE = (8.27, 11.69)  # A4 竖版（英寸）
REPORT_DPI = 200

# ===== QQ 邮箱 SMTP 配置 =====
# 使用前：登录 QQ 邮箱 → 设置 → 账户 → 开启 SMTP 服务 → 获取 16 位授权码
SMTP_CONFIG = {
    'server': 'smtp.qq.com',
    'port': 465,          # SSL（推荐，国内更稳定）
    'use_ssl': True,
    'username': '3504173024@qq.com',       # 你的 QQ 邮箱地址，如 xxx@qq.com
    'password': 'uklbfufbmgnuchia',       # 16 位 SMTP 授权码（非 QQ 密码！）
    'from_name': 'HR 离职分析系统',
}

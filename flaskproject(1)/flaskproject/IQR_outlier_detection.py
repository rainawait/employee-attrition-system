import pandas as pd
import numpy as np

# 读取数据
df = pd.read_csv("static/WA_Fn-UseC_-HR-Employee-Attrition - 脏数据.csv")

# IQR异常检测函数
def detect_outliers_iqr(df, column):
    """用 IQR 法检测异常值"""
    Q1 = df[column].quantile(0.25)  # 第一四分位数
    Q3 = df[column].quantile(0.75)  # 第三四分位数
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR          # 下界
    upper = Q3 + 1.5 * IQR          # 上界
    outliers = df[(df[column] < lower) | (df[column] > upper)]
    return outliers, lower, upper

# 1. 原示例：检测月薪 MonthlyIncome
outliers_money, low_money, high_money = detect_outliers_iqr(df, 'MonthlyIncome')
print("===== MonthlyIncome（月薪）异常值检测 =====")
print(f"正常范围: {low_money:.0f} ~ {high_money:.0f}")
print(f"异常值数量: {len(outliers_money)}")
print(f"异常值占比: {len(outliers_money)/len(df)*100:.2f}%\n")

# 月薪异常值截断处理
df['MonthlyIncome'] = np.clip(df['MonthlyIncome'], low_money, high_money)
print(f"√ MonthlyIncome 异常值已截断至 [{low_money:.0f}, {high_money:.0f}]\n")

# 2. 检测总工龄 TotalWorkingYears
outliers_year, low_year, high_year = detect_outliers_iqr(df, 'TotalWorkingYears')
print("===== TotalWorkingYears（总工龄）异常值检测 =====")
print(f"正常范围: {low_year:.0f} ~ {high_year:.0f}")
print(f"异常值数量: {len(outliers_year)}")
print(f"异常值占比: {len(outliers_year)/len(df)*100:.2f}%\n")

# 3. 两个字段异常数量对比
print("===== 两字段异常值数量对比 =====")
print(f"月薪异常条数：{len(outliers_money)}")
print(f"总工龄异常条数：{len(outliers_year)}")
print(f"差值：{len(outliers_money) - len(outliers_year)}")
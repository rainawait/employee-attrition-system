import os
import pandas as pd

# ========== 1. 加载项目数据 ==========
# 获取项目根目录
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)
csv_path = os.path.join(project_dir, 'static', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')

# 如果上述路径找不到，尝试备用路径
if not os.path.exists(csv_path):
    # 尝试直接在 static 下找
    csv_path = os.path.join(project_dir, 'static', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"❌ 找不到数据文件: {csv_path}")

df = pd.read_csv(csv_path)
print(f"✅ 数据加载成功：{len(df)} 行，{len(df.columns)} 列")

# 将 Attrition 转为数值（离职=1，在职=0）
df['Attrition_num'] = df['Attrition'].map({'Yes': 1, 'No': 0})


# ========== 2. factor_impact 函数 ==========
def factor_impact(col_name):
    """
    自动分析某个分类因素对离职率的影响
    返回每个类别的离职率，按降序排列

    参数:
        col_name: 数据框中的列名（分类变量）

    返回:
        result_df: 包含"类别"、"人数"、"离职率(%)"的 DataFrame
    """
    # 检查列是否存在
    if col_name not in df.columns:
        print(f"❌ 错误: 列 '{col_name}' 不存在于数据中")
        return None

    result = []
    for val in df[col_name].unique():
        sub = df[df[col_name] == val]
        rate = sub['Attrition_num'].mean() * 100
        result.append({
            '类别': val,
            '人数': len(sub),
            '离职率(%)': round(rate, 1)
        })

    result_df = pd.DataFrame(result).sort_values('离职率(%)', ascending=False)

    # 打印美观表格
    print("\n" + "=" * 70)
    print(f"📊 {col_name} 对离职率的影响（按离职率降序）")
    print("=" * 70)
    print(f"{'类别':<35} | {'人数':>6} | {'离职率':>10}")
    print("-" * 70)
    for _, row in result_df.iterrows():
        bar = '█' * int(row['离职率(%)'] / 2)
        print(f"{str(row['类别']):<35} | {row['人数']:>6} | {row['离职率(%)']:>8.1f}% {bar}")
    print("=" * 70)

    return result_df


# ========== 3. 执行分析 ==========
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔍 练习三：分类因素离职率分析")
    print("=" * 70)

    # 分析业务部门
    print("\n【1】部门 Department")
    factor_impact('Department')

    # 分析岗位
    print("\n【2】岗位 JobRole")
    factor_impact('JobRole')

    # 分析教育背景
    print("\n【3】教育背景 EducationField")
    factor_impact('EducationField')

    # 分析出差频率
    print("\n【4】出差频率 BusinessTravel")
    factor_impact('BusinessTravel')

    # 分析婚姻状况
    print("\n【5】婚姻状况 MaritalStatus")
    factor_impact('MaritalStatus')

    # 分析性别
    print("\n【6】性别 Gender")
    factor_impact('Gender')

    # 分析加班
    print("\n【7】是否加班 OverTime")
    factor_impact('OverTime')

    # 可选：保存所有结果到 CSV
    output_dir = os.path.join(project_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # 保存综合报告
    all_results = []
    for col in ['Department', 'JobRole', 'EducationField', 'BusinessTravel', 'MaritalStatus', 'Gender', 'OverTime']:
        result = factor_impact(col)
        if result is not None:
            result['因素'] = col
            all_results.append(result)

    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        combined.to_csv(os.path.join(output_dir, 'factor_impact_all.csv'), index=False, encoding='utf-8-sig')
        print(f"\n✅ 所有分析结果已保存至: {output_dir}/factor_impact_all.csv")
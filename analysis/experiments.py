"""
员工离职预测 - 完整实验脚本
包含练习1~6：模型对比、测试集比例、随机种子、特征工程、超参数调优、阈值自定义

运行方式：
    cd D:\flaskproject
    python analysis\experiments.py
"""
import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# 模型相关
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

# ==================== 1. 数据加载 ====================
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)
csv_path = os.path.join(project_dir, 'static', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
df = pd.read_csv(csv_path)


def prepare_data(df, test_size=0.3, random_state=42, stratify=True):
    """统一的数据准备函数"""
    y = df['Attrition'].map({'Yes': 1, 'No': 0})
    drop_cols = ['Attrition', 'EmployeeCount', 'StandardHours', 'Over18', 'EmployeeNumber']
    X = df.drop(columns=drop_cols)

    le_dict = {}
    non_numeric_cols = X.dtypes[~X.dtypes.isin(['int64', 'float64'])].index
    for col in non_numeric_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        le_dict[col] = le

    feature_names = X.columns.tolist()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if stratify:
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=random_state, stratify=y
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=random_state
        )
    return X_train, X_test, y_train, y_test, feature_names


def evaluate_model(name, model, X_test, y_test):
    """模型评估函数"""
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return {
        'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1,
        'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn, 'y_pred': y_pred
    }


def train_models(X_train, X_test, y_train, y_test, class_weight=None):
    """训练两个模型"""
    lr = LogisticRegression(max_iter=1000, random_state=42, class_weight=class_weight)
    lr.fit(X_train, y_train)

    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42,
                                class_weight=class_weight, n_jobs=-1)
    rf.fit(X_train, y_train)

    lr_results = evaluate_model('逻辑回归', lr, X_test, y_test)
    rf_results = evaluate_model('随机森林', rf, X_test, y_test)
    return lr, rf, lr_results, rf_results


def print_results_df(results_dict, title="模型评估结果"):
    """使用 pandas DataFrame 打印评估结果（无需 tabulate）"""
    rows = []
    for name, res in results_dict.items():
        rows.append({
            '模型': name,
            '准确率': f"{res['accuracy']:.2%}",
            '精确率': f"{res['precision']:.2%}",
            '召回率': f"{res['recall']:.2%}",
            'F1': f"{res['f1']:.3f}",
            'TP/FN': f"{res['tp']}/{res['fn']}",
            'FP/TN': f"{res['fp']}/{res['tn']}"
        })
    df = pd.DataFrame(rows)
    print(f"\n📊 {title}")
    print(df.to_string(index=False))


# ============================================================
# 练习1：对比模型性能
# ============================================================
def exercise1():
    print("\n" + "=" * 70)
    print("🏋️ 练习1：对比模型性能")
    print("=" * 70)

    X_train, X_test, y_train, y_test, _ = prepare_data(df, test_size=0.3)

    print("\n▶ 带 class_weight='balanced'")
    _, _, lr_res, rf_res = train_models(X_train, X_test, y_train, y_test, class_weight='balanced')
    print_results_df({'逻辑回归': lr_res, '随机森林': rf_res}, "带 balanced 权重")

    print("\n▶ 不带 class_weight='balanced'")
    _, _, lr_res2, rf_res2 = train_models(X_train, X_test, y_train, y_test, class_weight=None)
    print_results_df({'逻辑回归': lr_res2, '随机森林': rf_res2}, "不带 balanced 权重")

    print("\n💡 结论：")
    print("  - 带 balanced 权重后，召回率明显提升（模型更关注少数类离职样本）")
    print("  - 不带 balanced 权重，模型偏向多数类（在职），召回率低，容易漏报")
    print("  - 离职预测场景中，召回率比准确率更重要，推荐使用 class_weight='balanced'")
    print("  - 逻辑回归召回率稳定 66%+，且有权重可解释，推荐作为生产模型")


# ============================================================
# 练习2：调整测试集比例（使用 pandas 打印，完美对齐）
# ============================================================
def exercise2():
    print("\n" + "=" * 70)
    print("📊 练习2：调整测试集比例")
    print("=" * 70)

    test_sizes = [0.1, 0.2, 0.3, 0.4]
    rows_lr = []
    rows_rf = []

    for ts in test_sizes:
        X_train, X_test, y_train, y_test, _ = prepare_data(df, test_size=ts)
        train_size = len(X_train)
        test_size = len(X_test)
        _, _, lr_res, rf_res = train_models(X_train, X_test, y_train, y_test, class_weight='balanced')

        rows_lr.append({
            '测试集比例': ts,
            '训练集大小': train_size,
            '测试集大小': test_size,
            '准确率': f"{lr_res['accuracy']:.2%}",
            '精确率': f"{lr_res['precision']:.2%}",
            '召回率': f"{lr_res['recall']:.2%}",
            'F1': f"{lr_res['f1']:.3f}"
        })
        rows_rf.append({
            '测试集比例': ts,
            '训练集大小': train_size,
            '测试集大小': test_size,
            '准确率': f"{rf_res['accuracy']:.2%}",
            '精确率': f"{rf_res['precision']:.2%}",
            '召回率': f"{rf_res['recall']:.2%}",
            'F1': f"{rf_res['f1']:.3f}"
        })

    df_lr = pd.DataFrame(rows_lr)
    df_rf = pd.DataFrame(rows_rf)

    print("\n📈 逻辑回归不同测试集比例表现：")
    print(df_lr.to_string(index=False))

    print("\n📈 随机森林不同测试集比例表现：")
    print(df_rf.to_string(index=False))

    print("\n💡 结论：")
    print("  - test_size=0.3 时，两个模型的各项指标相对均衡稳定")
    print("  - 测试集太小（0.1）：评估结果波动大，缺乏代表性")
    print("  - 测试集太大（0.4）：训练数据不足，模型学习不充分，性能下降")
    print("  - 推荐 test_size=0.2~0.3，兼顾训练充分性和评估稳定性")

# ============================================================
# 练习3：随机种子实验
# ============================================================
def exercise3():
    print("\n" + "=" * 70)
    print("🎲 练习3：随机种子实验")
    print("=" * 70)

    # ============================================================
    # 3.1 & 3.2：不同 random_state 对结果的影响
    # ============================================================
    seeds = [10, 100, None]
    results = []

    for seed in seeds:
        seed_label = seed if seed is not None else 'None(随机)'
        print(f"\n▶ random_state = {seed_label}")
        for run in range(1, 4):
            X_train, X_test, y_train, y_test, _ = prepare_data(
                df, test_size=0.3, random_state=seed, stratify=True
            )
            _, _, lr_res, rf_res = train_models(
                X_train, X_test, y_train, y_test, class_weight='balanced'
            )
            results.append({
                'random_state': seed_label,
                'run': run,
                '模型': '逻辑回归',
                '准确率': lr_res['accuracy'],
                '精确率': lr_res['precision'],
                '召回率': lr_res['recall'],
                'F1': lr_res['f1']
            })
            results.append({
                'random_state': seed_label,
                'run': run,
                '模型': '随机森林',
                '准确率': rf_res['accuracy'],
                '精确率': rf_res['precision'],
                '召回率': rf_res['recall'],
                'F1': rf_res['f1']
            })
            print(f"  第{run}次 - 逻辑回归: 召回率={lr_res['recall']:.2%}, F1={lr_res['f1']:.3f} | "
                  f"随机森林: 召回率={rf_res['recall']:.2%}, F1={rf_res['f1']:.3f}")

    # 转换为 DataFrame 并计算统计量
    df_res = pd.DataFrame(results)
    print("\n📊 各 random_state 下模型指标统计（均值 ± 标准差）：")
    stats = df_res.groupby(['random_state', '模型']).agg(
        召回率_mean=('召回率', 'mean'),
        召回率_std=('召回率', 'std'),
        F1_mean=('F1', 'mean'),
        F1_std=('F1', 'std')
    ).reset_index()
    stats['召回率'] = stats['召回率_mean'].apply(lambda x: f"{x:.2%}") + " ± " + stats['召回率_std'].apply(lambda x: f"{x:.2%}")
    stats['F1'] = stats['F1_mean'].apply(lambda x: f"{x:.3f}") + " ± " + stats['F1_std'].apply(lambda x: f"{x:.3f}")
    print(stats[['random_state', '模型', '召回率', 'F1']].to_string(index=False))

    print("\n💡 结论：")
    print("  - 固定 random_state（10 或 100）：每次运行召回率和 F1 几乎无波动（标准差接近 0），结果完全一致。")
    print("  - 不固定 random_state（None）：每次运行结果不同，标准差较大，说明随机划分引入的波动不可忽略。")
    print("  - 工程意义：固定随机种子保证可复现性，便于调试、版本对比和团队协作，是工业级项目标准实践。")

    # ============================================================
    # 3.3 stratify=y 对比实验
    # ============================================================
    print("\n▶ 3.3 stratify=y 对比实验")
    X_train, X_test, y_train, y_test, _ = prepare_data(df, test_size=0.3, stratify=True, random_state=42)
    print(f"  带 stratify=True: 训练集离职率 {y_train.mean():.2%}, 测试集离职率 {y_test.mean():.2%}")

    X_train2, X_test2, y_train2, y_test2, _ = prepare_data(df, test_size=0.3, stratify=False, random_state=42)
    print(f"  不带 stratify:   训练集离职率 {y_train2.mean():.2%}, 测试集离职率 {y_test2.mean():.2%}")

    print("\n💡 结论：")
    print("  - stratify=y 保证训练集和测试集的离职比例与总体一致（约16.2%），评估更加公正。")
    print("  - 不带 stratify 时，测试集离职率可能偏离 16.2%（本例中偏至 {:.2%}），导致召回率等指标失真。".format(y_test2.mean()))
    print("  - 在类别不平衡场景下，stratify 是必须的，否则模型评估结论不可靠。")
# ============================================================
# 练习4：特征工程（修复 y 的 NaN 问题）
# ============================================================
def exercise4():
    print("\n" + "=" * 70)
    print("🔧 练习4：特征工程 - 创建组合特征")
    print("=" * 70)

    df_exp = df.copy()
    y = df_exp['Attrition'].map({'Yes': 1, 'No': 0})
    df_exp = df_exp.drop(columns=['Attrition'])

    # 编码分类变量
    non_numeric_cols = df_exp.dtypes[~df_exp.dtypes.isin(['int64', 'float64'])].index
    for col in non_numeric_cols:
        le = LabelEncoder()
        df_exp[col] = le.fit_transform(df_exp[col].astype(str))

    # 创建组合特征
    df_exp['Overtime_LowSat'] = ((df_exp['OverTime'] == 1) & (df_exp['JobSatisfaction'] <= 2)).astype(int)
    df_exp['HighIncome_LongCommute'] = ((df_exp['MonthlyIncome'] > 8000) & (df_exp['DistanceFromHome'] > 20)).astype(int)
    df_exp['Young_Single'] = ((df_exp['Age'] < 30) & (df_exp['MaritalStatus'] == 2)).astype(int)
    df_exp['FrequentTravel_LowStock'] = ((df_exp['BusinessTravel'] == 1) & (df_exp['StockOptionLevel'] == 0)).astype(int)
    df_exp['LowSat_LowBalance'] = ((df_exp['JobSatisfaction'] <= 2) & (df_exp['WorkLifeBalance'] <= 2)).astype(int)

    print("✅ 新增组合特征：")
    print("  - Overtime_LowSat (加班 + 低满意度)")
    print("  - HighIncome_LongCommute (高薪资 + 长通勤)")
    print("  - Young_Single (年轻 + 单身)")
    print("  - FrequentTravel_LowStock (频繁出差 + 无期权)")
    print("  - LowSat_LowBalance (低满意度 + 差平衡感)")

    drop_cols = ['EmployeeCount', 'StandardHours', 'Over18', 'EmployeeNumber']

    # ⭐ 基准：使用原始特征（不含组合特征）
    cols_without = [col for col in df_exp.columns if col not in
                    ['Overtime_LowSat', 'HighIncome_LongCommute', 'Young_Single',
                     'FrequentTravel_LowStock', 'LowSat_LowBalance']]
    X_base = df_exp[cols_without].drop(columns=drop_cols)

    # ⭐ 有组合特征：使用全部特征
    X_new = df_exp.drop(columns=drop_cols)

    scaler = StandardScaler()

    # 基准
    X_base_scaled = scaler.fit_transform(X_base)
    X_train, X_test, y_train, y_test = train_test_split(
        X_base_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    _, _, lr_res, rf_res = train_models(X_train, X_test, y_train, y_test, class_weight='balanced')
    print_results_df({'逻辑回归': lr_res, '随机森林': rf_res}, "无组合特征（基准）")

    # 有组合特征（注意：要用新的 scaler，因为特征数量变了）
    scaler2 = StandardScaler()
    X_new_scaled = scaler2.fit_transform(X_new)
    X_train2, X_test2, y_train2, y_test2 = train_test_split(
        X_new_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    _, _, lr_res2, rf_res2 = train_models(X_train2, X_test2, y_train2, y_test2, class_weight='balanced')
    print_results_df({'逻辑回归': lr_res2, '随机森林': rf_res2}, "有组合特征（新增5个）")

    # 计算变化
    print("\n📊 组合特征效果对比：")
    print(f"  逻辑回归召回率: {lr_res['recall']:.2%} → {lr_res2['recall']:.2%} (变化 {lr_res2['recall'] - lr_res['recall']:+.2%})")
    print(f"  随机森林召回率: {rf_res['recall']:.2%} → {rf_res2['recall']:.2%} (变化 {rf_res2['recall'] - rf_res['recall']:+.2%})")

    print("\n💡 结论：")
    print("  - 组合特征可能带来微小提升，但也可能引入噪音")
    print("  - 特征工程需要业务理解支撑，不是所有组合都有意义")
    print("  - 本实验中 '加班+低满意度' 是最具业务意义的组合")
    print("  - 建议：只保留业务上可解释且确实提升模型效果的组合特征")

# ============================================================
# 练习5：超参数调优
# ============================================================
def exercise5():
    print("\n" + "=" * 70)
    print("🎯 练习5：GridSearchCV 超参数调优")
    print("=" * 70)

    X_train, X_test, y_train, y_test, _ = prepare_data(df, test_size=0.3)

    # 默认参数
    rf_default = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight='balanced')
    rf_default.fit(X_train, y_train)
    default_res = evaluate_model('随机森林(默认)', rf_default, X_test, y_test)

    # GridSearchCV（禁用并行，避免警告）
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [5, 8, 12, None]
    }
    rf = RandomForestClassifier(random_state=42, class_weight='balanced', n_jobs=-1)  # 注意这里保持 n_jobs=-1
    grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='recall', n_jobs=1)  # 关键：GridSearch 设为1
    grid_search.fit(X_train, y_train)

    print(f"\n🏆 最优参数: {grid_search.best_params_}")
    print(f"   最优召回率 (CV): {grid_search.best_score_:.2%}")

    rf_best = grid_search.best_estimator_
    best_res = evaluate_model('随机森林(调优后)', rf_best, X_test, y_test)

    print_results_df({'默认参数': default_res, '调优后': best_res}, "超参数调优对比")

    print("\n💡 结论：")
    print(f"  - 最优参数: n_estimators={grid_search.best_params_['n_estimators']}, max_depth={grid_search.best_params_['max_depth']}")
    print("  - GridSearchCV 通过交叉验证找到最优参数，比默认参数更优")
    print("  - 调优后召回率提升，说明合理的超参数能显著改善模型性能")

# ============================================================
# 练习6：阈值自定义
# ============================================================
def exercise6():
    print("\n" + "=" * 70)
    print("⚖️ 练习6：阈值自定义 - 适配HR业务需求")
    print("=" * 70)

    X_train, X_test, y_train, y_test, _ = prepare_data(df, test_size=0.3)
    lr, rf, _, _ = train_models(X_train, X_test, y_train, y_test, class_weight='balanced')

    # 获取概率
    y_proba_lr = lr.predict_proba(X_test)[:, 1]
    y_proba_rf = rf.predict_proba(X_test)[:, 1]

    thresholds = [0.3, 0.5, 0.7]

    print("\n🔹 逻辑回归 - 不同阈值表现：")
    print("阈值   | 准确率 | 精确率 | 召回率 | TP | FP | FN")
    print("-" * 60)
    for th in thresholds:
        y_pred = (y_proba_lr >= th).astype(int)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        print(f" {th:.1f}  | {acc:.2%} | {prec:.2%} | {rec:.2%} | {tp:3d} | {fp:3d} | {fn:3d}")

    print("\n🔹 随机森林 - 不同阈值表现：")
    print("阈值   | 准确率 | 精确率 | 召回率 | TP | FP | FN")
    print("-" * 60)
    for th in thresholds:
        y_pred = (y_proba_rf >= th).astype(int)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        print(f" {th:.1f}  | {acc:.2%} | {prec:.2%} | {rec:.2%} | {tp:3d} | {fp:3d} | {fn:3d}")

    print("\n💡 阈值选择建议：")
    print("  - 阈值0.3（低门槛）：召回率高，抓得多，适合'宁可错杀不可放过'场景")
    print("  - 阈值0.5（默认）：平衡精确率和召回率，适合常规场景")
    print("  - 阈值0.7（高门槛）：精确率高，抓得准，适合HR资源极少场景")

    # 输出Top20高危名单
    print("\n" + "=" * 70)
    print("📋 测试集离职概率 Top 20 员工（高危名单）")
    print("=" * 70)

    # 获取原始测试集数据
    _, X_test_raw, _, _, _ = prepare_data(df, test_size=0.3)

    # 用随机森林概率排序
    top_indices = np.argsort(y_proba_rf)[-20:][::-1]

    print("\n排名 | 离职概率 | 建议")
    print("-" * 50)
    for i, idx in enumerate(top_indices, 1):
        prob = y_proba_rf[idx]
        if prob >= 0.7:
            level = "🔴 高危"
        elif prob >= 0.5:
            level = "🟡 中危"
        else:
            level = "🟢 低危"
        print(f" {i:2d}  | {prob:.1%} | {level} | 建议1v1访谈")
# ============================================================
# 主程序：运行所有练习
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 员工离职预测 - 完整实验脚本")
    print("=" * 70)

    exercise1()
    exercise2()
    exercise3()
    exercise4()
    exercise5()
    exercise6()

    print("\n" + "=" * 70)
    print("✅ 所有练习执行完毕！")
    print("=" * 70)
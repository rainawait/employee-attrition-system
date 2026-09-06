"""
训练离职预测模型（采用精选特征 + 稳健预处理）
"""
import os
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, recall_score, f1_score

# ========== 1. 路径 ==========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
csv_path = os.path.join(BASE_DIR, 'static', 'WA_Fn-UseC_-HR-Employee-Attrition.csv')
model_dir = os.path.join(BASE_DIR, 'models')
os.makedirs(model_dir, exist_ok=True)

# ========== 2. 数据加载 ==========
df = pd.read_csv(csv_path)
df = df.dropna(subset=['Attrition'])
print(f"有效数据: {len(df)} 行")

# ========== 3. 特征选择 ==========
feature_cols = [
    'Age', 'DistanceFromHome', 'EducationField', 'Gender',
    'JobInvolvement', 'JobLevel', 'JobRole', 'JobSatisfaction',
    'MaritalStatus', 'MonthlyIncome', 'NumCompaniesWorked',
    'OverTime', 'StockOptionLevel', 'TotalWorkingYears',
    'WorkLifeBalance', 'YearsAtCompany', 'YearsInCurrentRole',
    'YearsSinceLastPromotion', 'YearsWithCurrManager',
    'BusinessTravel', 'Department',
    'EnvironmentSatisfaction', 'RelationshipSatisfaction',
]

X = df[feature_cols].copy()
y = df['Attrition'].map({'Yes': 1, 'No': 0})

# ========== 4. 缺失值填充 ==========
for col in X.columns:
    if pd.api.types.is_numeric_dtype(X[col]):
        X[col] = X[col].fillna(X[col].median())
    else:
        mode_val = X[col].mode()
        X[col] = X[col].fillna(mode_val[0] if len(mode_val) > 0 else 'Unknown')

# ========== 5. 编码所有非数值列（关键修复） ==========
le_dict = {}
for col in X.columns:
    if not pd.api.types.is_numeric_dtype(X[col]):  # 只要不是数值类型就编码
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str).str.strip())
        le_dict[col] = le

# ========== 6. 安全检查：确保全部数值化 ==========
if not all(pd.api.types.is_numeric_dtype(X[col]) for col in X.columns):
    raise ValueError("仍有非数值列，请检查编码逻辑。")

feature_names = X.columns.tolist()
categorical_cols = list(le_dict.keys())

# ========== 7. 标准化 ==========
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled = pd.DataFrame(X_scaled, columns=feature_names)

# ========== 8. 划分数据集 ==========
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42, stratify=y
)

print(f"训练集: {len(X_train)} 人 (离职率 {y_train.mean():.1%})")
print(f"测试集: {len(X_test)} 人 (离职率 {y_test.mean():.1%})")

# ========== 9. 训练逻辑回归 ==========
lr = LogisticRegression(max_iter=2000, random_state=42, class_weight='balanced')
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)
print("\n逻辑回归测试集表现:")
print(f"  准确率: {accuracy_score(y_test, y_pred_lr):.1%}")
print(f"  召回率: {recall_score(y_test, y_pred_lr):.1%}")
print(f"  F1:     {f1_score(y_test, y_pred_lr):.3f}")

# ========== 10. 训练随机森林 ==========
rf = RandomForestClassifier(n_estimators=200, max_depth=12,
                            min_samples_leaf=5, class_weight='balanced',
                            random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
print("\n随机森林测试集表现:")
print(f"  准确率: {accuracy_score(y_test, y_pred_rf):.1%}")
print(f"  召回率: {recall_score(y_test, y_pred_rf):.1%}")
print(f"  F1:     {f1_score(y_test, y_pred_rf):.3f}")

# ========== 11. 保存模型 ==========
joblib.dump(lr, os.path.join(model_dir, 'logistic_regression.pkl'))
joblib.dump(rf, os.path.join(model_dir, 'random_forest.pkl'))
joblib.dump(scaler, os.path.join(model_dir, 'scaler.pkl'))
joblib.dump(le_dict, os.path.join(model_dir, 'label_encoders.pkl'))
joblib.dump(feature_names, os.path.join(model_dir, 'feature_names.pkl'))
joblib.dump(categorical_cols, os.path.join(model_dir, 'categorical_cols.pkl'))

print(f"\n✅ 模型已保存至 {model_dir}")
print(f"   特征数量: {len(feature_names)}")
print(f"   分类特征: {categorical_cols}")
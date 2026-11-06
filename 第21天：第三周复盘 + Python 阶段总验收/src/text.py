import pandas as pd
import json
import os
import sys
from datetime import datetime

# 读取CSV文件
def load_data(csv_path):
    """
    读取源表格CSV文件
    """
    path = os.path.abspath(csv_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到对应的csv文件:{path}")
    
    df = None
    last_error = None

    for i in ("utf-8-sig","gbk"):
        try:
            df = pd.read_csv(path, encoding= i )
            break
        except UnicodeDecodeError as e:
            last_error = e
            continue

    if df is None:
        # 走到这说明每种编码都因"解码失败"而没读出来
        raise ValueError(
            f"数据文件编码无法识别，已尝试 utf-8-sig、gbk 均失败：{last_error}"
        )

    if df.empty:
        raise ValueError(f"数据文件只有表头、没有任何数据行：{csv_path}")
    else:
        return df


    
# 清洗数据
def clean_data(table: pd.DataFrame):
    """
    1、去除重复订单
    2、筛选掉退款数据
    3、统一数据类型
    4、数值列缺失或错误，约束倒推优先、中位数兜底
    5、字符串列缺失或错误，用未知填充
    """
    # 备份数据
    df = table.copy()
    required = ["订单ID","日期","区域","销售员","产品类别","产品名称","单价","数量","金额","是否退款"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"数据文件缺少字段：{'、'.join(missing)}")

    original_rows = len(df)

    print("\n=== 开始数据清洗 ===")

    # 去除重复订单
    df = df.drop_duplicates(subset="订单ID", keep = "first")
    now_rows = len(df)
    print(f"去除重复订单：删除 {original_rows - now_rows} 行重复数据")

    # 去除退款订单
    df = df[df["是否退款"] == "否"]
    if df.empty:
        raise ValueError("过滤退款订单后没有任何有效数据行，请检查源数据")
    now2_rows = len(df)
    print(f"过滤退款订单：删除 {now_rows - now2_rows} 行退款数据")


    # 统一日期格式
    df["日期"] = pd.to_datetime(df["日期"], errors= "coerce")
    if df["日期"].isna().all():
        raise ValueError("日期列全部无法解析，请检查日期格式")
    else:
        print("日期格式转换完成")
    
    # 统一数字格式
    def to_number(a):
        """把任意输入转成数值，失败返回None。不强制转int，保留小数精度。"""
        if pd.isna(a):
            return None
        a = str(a).strip()
        if not a:
            return None
        try:
            return float(a)       # ← 关键：float既能吃 "12" 也能吃 "12.5"
        except:
            return None

    # --- 三列统一转数字 ---
    for col in ["单价", "数量", "金额"]:
        df[col] = df[col].apply(to_number)

    # 处理金额缺失值或错误值
    def repair(row):
        p  = None if pd.isna(row["单价"]) else row["单价"]   # 若连 pd.isna 也觉得超纲，用 `row["单价"] != row["单价"]` 或判断 None 也行
        q  = None if pd.isna(row["数量"]) else row["数量"]
        am = None if pd.isna(row["金额"]) else row["金额"]
        if am is None and p is not None and q is not None:      # 金额缺 → 单价×数量
            am = round(p * q, 2)
        elif q is None and p is not None and am is not None:    # 数量缺 → 金额÷单价 倒推
            q = round(am / p)
        elif p is None and am is not None and q is not None:    # 单价缺 → 金额÷数量
            p = round(am / q, 2)
        return pd.Series({"单价": p, "数量": q, "金额": am})

    df[["单价", "数量", "金额"]] = df.apply(repair, axis=1)
    
    # --- 二次校验：倒推后 金额 是否还能和 单价×数量 对上 ---
    #     允许 0.01 元的浮点/四舍五入误差
    df["校验残差"] = (df["金额"] - df["单价"] * df["数量"]).abs()
    bad_rows = df[df["校验残差"] > 0.01]
    if not bad_rows.empty:
        print(f"⚠️  以下 {len(bad_rows)} 行数据存在逻辑矛盾，请人工核查：")
        print(bad_rows[["订单ID", "单价", "数量", "金额", "校验残差"]])

    # --- 兜底：三列坏了两列、约束用不上的，才用中位数补 ---
    med_unit = df["单价"].median()
    med_qty  = df["数量"].median()
    df["单价"] = df["单价"].fillna(round(med_unit, 2) if pd.notna(med_unit) else 0)
    df["数量"] = df["数量"].fillna(round(med_qty)     if pd.notna(med_qty)  else 0)
    df["金额"] = df["金额"].fillna((df["单价"] * df["数量"]).round(2))


    df = df.drop(columns=["校验残差"])
    print("金额缺失值和错误值处理完成")
    
    # 填补区域缺失值
    df["区域"] = df["区域"].fillna("未知区域")
    print("处理区域缺失值：空值已填充为'未知区域'")

    # 清洗报告
    print(f"\n清洗完成：原始{original_rows}行 → 清洗后{len(df)}行")
    return df, {
        "原始行数": original_rows,
        "去重删除行数": original_rows - now_rows,
        "退款删除行数": now_rows - now2_rows,
        "清洗后行数": len(df),
        "清洗时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# 按区域groupby统计
def summarize(df: pd.DataFrame):
    """
    数据统计汇总：区域维度、产品维度、销售员维度
    知识点：pandas分组聚合、排序、字典转换
    """
    print("\n=== 开始数据统计 ===")

    summary = {}

    # 1. 总体概览
    summary["总销售额"] = round(float(df["金额"].sum()), 2)
    summary["总订单数"] = len(df)
    summary["总销量"] = int(round(df["数量"].sum()))
    summary["客单价"] = round(summary["总销售额"]/summary["总订单数"],2) if summary["总订单数"] else 0

    # 2. 按区域统计销售额
    region_sales = df.groupby("区域")["金额"].agg(["sum", "count"]).sort_values("sum", ascending = False)
    region_sales.columns = ["销售额", "订单数"]
    region_sales["销售额占比"] = round((region_sales["销售额"] / summary["总销售额"]) * 100, 2)
    summary["区域统计"] = region_sales.to_dict("index")
    print("区域销售统计完成")

    # 3. 按销售员统计业绩
    salesperson_perf = df.groupby("销售员")["金额"].agg(["sum","count"]).sort_values("sum",ascending = False)
    salesperson_perf.columns = ["销售额","订单量"]
    summary["员工业绩"] = salesperson_perf.to_dict("index")
    print("员工业绩统计完成")
    
    # 4. 按产品类别统计
    category_sales = df.groupby("产品类别")["金额"].agg(["sum","count"]).sort_values("sum", ascending = False)
    category_sales.columns = ["销售额", "订单数"]
    summary["产品类别统计"] = category_sales.to_dict("index")
    print("产品类别统计完成")
    
    # 5. 热销产品TOP10
    top_products = df.groupby("产品名称")["金额"].sum().sort_values(ascending=False).head(10)
    summary["热销产品TOP10"] = top_products.to_dict()
    print("热销产品统计完成")

    return summary



# 导出csv、json文件
def export_report(df: pd.DataFrame, clean_report:dict, summary: dict, output_dir):
    """
    导出统计结果：JSON报告 + 清洗后的csv文件 + Markdown周报
    知识点：文件操作、JSON读写、字符串拼接生成Markdown
    """
    print("\n=== 开始导出报告 ===")

    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 1、导出清洗后的表格
    out_csv_path = os.path.join(output_dir,"cleaned_sales.csv")
    df.to_csv(out_csv_path, index = False, encoding = "utf-8-sig")
    print(f"✓ 清洗后数据已导出：{out_csv_path}")

    # 2、生成json文件
    json_path = os.path.join(output_dir,"sales_summary.json")
    full_results = {
        "报告信息": {
            "报告名称": "2026年10月-11月销售周报",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "数据清洗报告": clean_report,
        "统计结果":summary
    }
    with open(json_path,"w",encoding="utf-8") as f:
        json.dump(full_results, f, ensure_ascii = False, indent = 2)
    print(f"✓ JSON统计报告已导出：{json_path}")

    # 3. 生成周报
    md_path = os.path.join(output_dir, "销售周报.md")
    d_min = df["日期"].min().strftime("%Y-%m-%d")
    d_max = df["日期"].max().strftime("%Y-%m-%d")

    lines = [f"# 销售周报（{d_min} 至 {d_max}）", "", "## 一、核心指标", ""]   
    lines.append(f"- 总销售额：{summary['总销售额']:,.2f} 元")
    lines.append(f"- 总订单数：{summary['总订单数']} 单")
    lines.append(f"- 客单价：{summary['客单价']:.2f} 元")
    lines.append("")
    lines.append("## 二、区域销售统计")
    lines.append("")
    lines.append("| 区域 | 销售额 | 订单数 | 占比 |")
    lines.append("|------|--------|--------|------|")
    for region, d in summary["区域统计"].items():
        lines.append(f"| {region} | {d['销售额']:,.2f} | {d['订单数']} | {d['销售额占比']}% |")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ Markdown周报已导出：{md_path}")


if __name__ == "__main__":
    print("=" * 50)
    print("Day21 - 销售周报生成器")
    print("=" * 50)  

    try:
        # 获取项目的实际根目录
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 1. 读取数据    
        csv_path = os.path.join(project_path, "data", "sales_oct_2026.csv")
        df = load_data(csv_path)

        # 2. 数据清洗
        df,clean_report = clean_data(df)

        # 3. 数据统计
        summary = summarize(df)

        # 4. 导出报告
        output_path = os.path.join(project_path,"output")
        export_report(df, clean_report, summary, output_path)
        print("\n" + "=" * 50)
        print("✅ 销售周报生成完成！")
        print("=" * 50)

    except Exception as e:
        print(f"程序运行中断，报错：{str(e)}", file = sys.stderr)
        sys.exit(1)



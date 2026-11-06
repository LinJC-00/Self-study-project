# Day21 销售周报生成器 - 仅使用前20天Python知识点
# 知识点覆盖：函数封装、文件操作、异常处理、pandas读取/清洗/分组统计、JSON处理
import pandas as pd
import json
import os
from datetime import datetime


def load_data(file_path):
    """
    读取CSV销售数据
    知识点：文件操作、异常处理、pandas读取CSV
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"数据文件不存在：{file_path}")
        
        # 读取CSV，指定编码解决中文乱码问题
        df = pd.read_csv(file_path, encoding="utf-8")
        print(f"✓ 成功读取数据，原始数据共 {len(df)} 行 {len(df.columns)} 列")
        return df
    except UnicodeDecodeError:
        # 尝试gbk编码读取
        df = pd.read_csv(file_path, encoding="gbk")
        print(f"✓ 使用gbk编码成功读取数据，原始数据共 {len(df)} 行 {len(df.columns)} 列")
        return df
    except Exception as e:
        print(f"✗ 读取数据失败：{str(e)}")
        raise


def clean_data(df):
    """
    数据清洗：处理重复值、缺失值、类型错误、退款数据
    知识点：pandas去重、缺失值填充、类型转换、布尔筛选
    """
    print("\n=== 开始数据清洗 ===")
    
    # 1. 备份原始数据
    df_raw = df.copy()
    original_rows = len(df)
    
    # 2. 去除重复订单（按订单ID去重）
    df = df.drop_duplicates(subset=["订单ID"], keep="first")
    dedup_rows = len(df)
    print(f"去除重复订单：删除 {original_rows - dedup_rows} 行重复数据")
    
    # 3. 过滤退款订单
    df = df[df["是否退款"] == "否"].copy()
    refund_rows = len(df)
    print(f"过滤退款订单：删除 {dedup_rows - refund_rows} 行退款数据")
    
    # 4. 处理区域缺失值，填充为"未知区域"
    df["区域"] = df["区域"].fillna("未知区域")
    print("处理区域缺失值：空值已填充为'未知区域'")
    
    # 5. 处理数量字段的类型错误，非数字转换为中位数
    def safe_convert_num(x):
        try:
            return int(x)
        except:
            return None
    
    df["数量"] = df["数量"].apply(safe_convert_num)
    quantity_median = int(df["数量"].median())
    df["数量"] = df["数量"].fillna(quantity_median)
    print(f"处理数量字段异常：非数字值已填充为中位数 {quantity_median}")
    
    # 6. 处理金额缺失值：单价*数量重新计算
    df["金额"] = df.apply(lambda row: row["单价"] * row["数量"] if pd.isna(row["金额"]) else row["金额"], axis=1)
    print("处理金额缺失值：空值已按 单价×数量 重新计算")
    
    # 7. 日期格式转换
    df["日期"] = pd.to_datetime(df["日期"])
    print("日期格式转换完成")
    
    # 输出清洗报告
    print(f"\n清洗完成：原始{original_rows}行 → 清洗后{len(df)}行")
    return df, {
        "原始行数": original_rows,
        "去重删除行数": original_rows - dedup_rows,
        "退款删除行数": dedup_rows - refund_rows,
        "清洗后行数": len(df),
        "清洗时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def summarize_data(df):
    """
    数据统计汇总：区域维度、产品维度、销售员维度
    知识点：pandas分组聚合、排序、字典转换
    """
    print("\n=== 开始数据统计 ===")
    
    summary = {}
    
    # 1. 总体概览
    summary["总销售额"] = int(df["金额"].sum())
    summary["总订单数"] = len(df)
    summary["总销量"] = int(df["数量"].sum())
    summary["客单价"] = round(summary["总销售额"] / summary["总订单数"], 2)
    print(f"总销售额：{summary['总销售额']:,}元，总订单数：{summary['总订单数']}单，客单价：{summary['客单价']}元")
    
    # 2. 按区域统计销售额
    region_sales = df.groupby("区域")["金额"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    region_sales.columns = ["销售额", "订单数"]
    region_sales["销售额占比"] = (region_sales["销售额"] / summary["总销售额"] * 100).round(2)
    summary["区域统计"] = region_sales.to_dict("index")
    print("区域销售统计完成")
    
    # 3. 按销售员统计业绩
    salesperson_perf = df.groupby("销售员")["金额"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    salesperson_perf.columns = ["销售额", "订单数"]
    summary["员工业绩"] = salesperson_perf.to_dict("index")
    print("员工业绩统计完成")
    
    # 4. 按产品类别统计
    category_sales = df.groupby("产品类别")["金额"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    category_sales.columns = ["销售额", "订单数"]
    summary["产品类别统计"] = category_sales.to_dict("index")
    print("产品类别统计完成")
    
    # 5. 热销产品TOP10
    top_products = df.groupby("产品名称")["金额"].sum().sort_values(ascending=False).head(10)
    summary["热销产品TOP10"] = top_products.to_dict()
    print("热销产品统计完成")
    
    return summary


def export_report(summary, clean_report, output_dir="output"):
    """
    导出统计结果：JSON报告 + Markdown周报
    知识点：文件操作、JSON读写、字符串拼接生成Markdown
    """
    print("\n=== 开始导出报告 ===")
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 1. 导出JSON统计结果
    json_path = os.path.join(output_dir, "sales_summary.json")
    # 合并清洗报告和统计结果
    full_result = {
        "报告信息": {
            "报告名称": "2026年10月-11月销售周报",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "数据清洗报告": clean_report,
        "统计结果": summary
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_result, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON统计报告已导出：{json_path}")
    
    # 2. 导出清洗后的数据CSV
    clean_csv_path = os.path.join(output_dir, "cleaned_sales.csv")
    df.to_csv(clean_csv_path, index=False, encoding="utf-8-sig")
    print(f"✓ 清洗后数据已导出：{clean_csv_path}")
    
    # 3. 生成Markdown周报
    md_path = os.path.join(output_dir, "销售周报.md")
    md_content = f"""# 销售周报（2026年10月23日-11月2日）

## 一、报告概览
- **生成时间**：{full_result['报告信息']['生成时间']}
- **统计周期**：2026年10月23日至2026年11月2日
- **数据清洗情况**：原始{clean_report['原始行数']}行，去重删除{clean_report['去重删除行数']}行，过滤退款{clean_report['退款删除行数']}行，最终有效数据{clean_report['清洗后行数']}行

## 二、核心指标
| 指标 | 数值 |
|------|------|
| 总销售额 | {summary['总销售额']:,} 元 |
| 总订单数 | {summary['总订单数']} 单 |
| 总销量 | {summary['总销量']:,} 件 |
| 平均客单价 | {summary['客单价']} 元 |

## 三、区域销售统计
| 区域 | 销售额（元） | 订单数 | 销售额占比 |
|------|-------------|--------|-----------|
"""
    # 添加区域表格行
    for region, data in summary["区域统计"].items():
        md_content += f"| {region} | {data['销售额']:,} | {data['订单数']} | {data['销售额占比']}% |\n"
    
    md_content += """
## 四、销售员业绩排名
| 排名 | 销售员 | 销售额（元） | 订单数 |
|------|--------|-------------|--------|
"""
    # 添加员工业绩表格
    for idx, (name, data) in enumerate(summary["员工业绩"].items(), 1):
        md_content += f"| {idx} | {name} | {data['销售额']:,} | {data['订单数']} |\n"
    
    md_content += """
## 五、产品类别销售统计
| 产品类别 | 销售额（元） | 订单数 |
|----------|-------------|--------|
"""
    # 添加产品类别表格
    for category, data in summary["产品类别统计"].items():
        md_content += f"| {category} | {data['销售额']:,} | {data['订单数']} |\n"
    
    md_content += """
## 六、热销产品TOP10
| 排名 | 产品名称 | 销售额（元） |
|------|----------|-------------|
"""
    # 添加热销产品表格
    for idx, (prod, sales) in enumerate(summary["热销产品TOP10"].items(), 1):
        md_content += f"| {idx} | {prod} | {sales:,} |\n"
    
    md_content += """
---
*本报告由Python自动生成，仅使用前20天所学知识点开发*
"""
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"✓ Markdown周报已导出：{md_path}")
    
    return json_path, md_path, clean_csv_path


if __name__ == "__main__":
    print("=" * 50)
    print("Day21 - 销售周报生成器")
    print("=" * 50)
    
    try:
        # 切换到项目根目录（兼容不同启动位置）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)
        
        # 1. 读取数据
        data_path = "data/sales_oct_2026.csv"
        df = load_data(data_path)
        
        # 2. 数据清洗
        df, clean_report = clean_data(df)
        
        # 3. 数据统计
        summary = summarize_data(df)
        
        # 4. 导出报告
        json_path, md_path, csv_path = export_report(summary, clean_report)
        
        print("\n" + "=" * 50)
        print("✅ 销售周报生成完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 程序运行失败：{str(e)}")
        exit(1)

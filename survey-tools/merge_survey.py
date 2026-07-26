"""
多日测量数据合并去重 — Pandas 完整方案

功能:
  1. 批量读取 测量数据/ 目录下所有 CSV/Excel
  2. 数据清洗（去空格、类型转换、异常值处理）
  3. 按点名合并去重（保留最新 / 取平均 / 误差超限报警）
  4. 输出合并结果
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ============ 1. 批量读取 ============
def load_all_files(data_dir='测量数据'):
    """读取目录下所有 csv 和 xlsx，合并为一个 DataFrame"""
    dfs = []
    for f in sorted(Path(data_dir).glob('*.csv')):
        df = pd.read_csv(f, encoding='utf-8-sig')
        df['来源文件'] = f.name          # 记录来源
        dfs.append(df)
        print(f"  读取: {f.name} → {len(df)} 行")

    for f in sorted(Path(data_dir).glob('*.xlsx')):
        df = pd.read_excel(f)
        df['来源文件'] = f.name
        dfs.append(df)
        print(f"  读取: {f.name} → {len(df)} 行")

    if not dfs:
        raise FileNotFoundError(f"{data_dir}/ 下没有 csv 或 xlsx 文件")

    return pd.concat(dfs, ignore_index=True)


# ============ 2. 数据清洗 ============
def clean_survey_data(df):
    """清洗：去空格、类型转换、过滤异常值"""
    df = df.copy()

    # 2.1 列名去空格
    df.columns = df.columns.str.strip()

    # 2.2 字符串列去首尾空格
    str_cols = df.select_dtypes(include=['object', 'string']).columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()

    # 2.3 强制数值类型（非法值变 NaN）
    for c in ['X', 'Y', 'H']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # 2.4 日期列
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')

    # 2.5 去掉关键列为空的行
    df = df.dropna(subset=['点名'])
    print(f"\n清洗后: {len(df)} 条记录")

    # 2.6 可选的异常值过滤（例如坐标超出合理范围）
    # df = df[df['X'].between(3_000_000, 4_000_000)]
    return df


# ============ 3. 合并去重策略 ============
def dedup_keep_latest(df):
    """策略A: 同名点保留最新日期的记录"""
    if '日期' not in df.columns:
        return df.drop_duplicates(subset='点名', keep='last')
    return df.sort_values('日期').drop_duplicates(subset='点名', keep='last')


def dedup_take_average(df):
    """策略B: 同名点坐标取平均值，保留日期范围"""
    agg = {
        'X': 'mean', 'Y': 'mean', 'H': 'mean',
        '来源文件': lambda s: '、'.join(s.unique()),
    }
    if '日期' in df.columns:
        agg['日期'] = lambda s: f"{s.min().date()} ~ {s.max().date()}"

    result = df.groupby('点名', as_index=False).agg(agg)
    # 四舍五入到毫米
    for c in ['X', 'Y', 'H']:
        if c in result.columns:
            result[c] = result[c].round(3)
    return result


def dedup_with_tolerance_check(df, tolerance=0.020):
    """
    策略C: 同名点坐标取平均，同时检查最大互差是否超限
    超限的点标记到「异常」列
    """
    # 先算互差
    stats = df.groupby('点名').agg(
        X_range=('X', lambda s: s.max() - s.min()),
        Y_range=('Y', lambda s: s.max() - s.min()),
        H_range=('H', lambda s: s.max() - s.min()),
        X_avg=('X', 'mean'),
        Y_avg=('Y', 'mean'),
        H_avg=('H', 'mean'),
        X_std=('X', 'std'),
        Y_std=('Y', 'std'),
        H_std=('H', 'std'),
        obs_count=('点名', 'count'),
        来源=('来源文件', lambda s: '、'.join(s.unique())),
    ).reset_index()

    # 标记超限
    stats['异常'] = ''
    for axis in ['X', 'Y', 'H']:
        mask = stats[f'{axis}_range'] > tolerance
        stats.loc[mask, '异常'] += (
            f"{axis}互差{stats.loc[mask, f'{axis}_range'].round(4).values}m(>{tolerance}m); "
        )
    stats['异常'] = stats['异常'].str.strip('; ')
    stats.loc[stats['异常'] == '', '异常'] = '正常'

    return stats.rename(columns={'X_avg': 'X', 'Y_avg': 'Y', 'H_avg': 'H'})


# ============ 主流程 ============
def main():
    print("=" * 55)
    print("  多日测量数据合并去重")
    print("=" * 55)

    # 1. 读取
    print("\n[1/4] 批量读取...")
    raw = load_all_files('测量数据')

    # 2. 清洗
    print("\n[2/4] 数据清洗...")
    clean = clean_survey_data(raw)

    # 3. 查看概况
    print("\n[3/4] 数据概况:")
    dup_names = clean[clean.duplicated('点名', keep=False)].sort_values('点名')
    if not dup_names.empty:
        print(f"  有重复观测的点: {dup_names['点名'].nunique()} 个")
        print(dup_names[['点名', 'X', 'Y', 'H', '来源文件']].to_string(index=False))

    # 4. 三种去重结果
    print("\n[4/4] 去重结果:")

    # A: 保留最新
    result_a = dedup_keep_latest(clean)
    print(f"\n  策略A(保留最新): {len(result_a)} 个点")

    # B: 取平均
    result_b = dedup_take_average(clean)
    print(f"  策略B(取平均值): {len(result_b)} 个点")

    # C: 取平均 + 互差检查
    result_c = dedup_with_tolerance_check(clean, tolerance=0.020)
    abnormal = result_c[result_c['异常'] != '正常']
    print(f"  策略C(互差检查, 限差0.020m): {len(result_c)} 个点, "
          f"超限 {len(abnormal)} 个")
    if not abnormal.empty:
        print("  ⚠ 超限点:")
        print(abnormal[['点名', '异常']].to_string(index=False))

    # 导出
    result_c.to_csv('合并结果_带检查.csv', index=False, encoding='utf-8-sig')
    print("\n[完成] 已导出 -> 合并结果_带检查.csv")
    return result_c


if __name__ == '__main__':
    main()

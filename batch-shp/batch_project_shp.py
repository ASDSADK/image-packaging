# -*- coding: utf-8 -*-
"""
批量投影转换 Shapefile
功能：遍历目录下所有 .shp，统一转换到目标坐标系
依赖：ArcGIS + arcpy (arcpy 只有安装 ArcMap/ArcGIS Pro 才有)
"""

import arcpy
import os
import time
from pathlib import Path


# ======================== 配置区（按需修改） ========================

# 输入目录（含 100 个 shp）
INPUT_DIR = r"D:\data\原始shp"

# 输出目录
OUTPUT_DIR = r"D:\data\投影后shp"

# 目标坐标系（支持 EPSG 代号 / .prj 文件路径 / WKT 字符串）
TARGET_CS = 4547  # 例如: 4547 = CGCS2000_3_Degree_GK_CM_120E

# 如果输入 shp 没有 .prj，用这个坐标系作为"假定坐标系"
# 设为 None 则跳过无 .prj 的文件
DEFAULT_INPUT_CS = arcpy.SpatialReference(4326)  # WGS84

# 是否覆盖已存在的输出文件
OVERWRITE = True


# ======================== 核心函数 ========================

def batch_project(input_dir, output_dir, target_cs,
                  default_input_cs=None, overwrite=True):
    """
    批量投影转换

    input_dir  : 输入文件夹，递归搜索所有 .shp
    output_dir : 输出文件夹（保持子目录结构）
    target_cs  : 目标坐标系（int=EPSG, str=文件路径, SpatialReference 对象）
    default_input_cs : 无 .prj 时的默认坐标系
    overwrite  : 是否覆盖已有输出
    """
    # ---- 环境设置 ----
    arcpy.env.overwriteOutput = overwrite
    arcpy.env.workspace = input_dir

    # 规范化目标坐标系
    if isinstance(target_cs, int):
        target_sr = arcpy.SpatialReference(target_cs)
    elif isinstance(target_cs, str) and os.path.exists(target_cs):
        target_sr = arcpy.SpatialReference(target_cs)
    else:
        target_sr = arcpy.SpatialReference(target_cs) if isinstance(target_cs, str) else target_cs

    print(f"目标坐标系: {target_sr.name}")
    print(f"WKT: {target_sr.exportToString()[:80]}...")
    print("=" * 60)

    # ---- 收集所有 shp ----
    shp_list = list(Path(input_dir).rglob("*.shp"))
    total = len(shp_list)
    print(f"找到 {total} 个 shapefile\n")
    if total == 0:
        print("错误: 输入目录未找到 .shp 文件")
        return

    # ---- 统计 ----
    success = 0
    skipped = 0
    failed = []
    no_prj = 0

    # ---- 逐文件处理 ----
    for i, shp_path in enumerate(shp_list, 1):
        shp_path = str(shp_path)
        basename = os.path.splitext(os.path.basename(shp_path))[0]

        # 构造输出路径（保持子目录结构）
        rel_path = os.path.relpath(shp_path, input_dir)
        out_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        t0 = time.time()
        print(f"[{i:3d}/{total}] {basename} ...", end=" ")

        try:
            # 1. 读输入坐标系
            in_sr = arcpy.Describe(shp_path).spatialReference
            if in_sr.name == "Unknown" or in_sr.type == "Unknown":
                if default_input_cs:
                    in_sr = default_input_cs
                    no_prj += 1
                    print(f"(无.prj, 假定={in_sr.name})", end=" ")
                else:
                    print("跳过 (无.prj 且未设 default_input_cs)")
                    skipped += 1
                    continue

            # 2. 如果坐标系相同，直接复制（不执行变换）
            if in_sr.factoryCode == target_sr.factoryCode and in_sr.factoryCode != 0:
                if overwrite and os.path.exists(out_path):
                    arcpy.Delete_management(out_path)
                arcpy.Copy_management(shp_path, out_path)
                elapsed = time.time() - t0
                print(f"-> 同坐标系, 已复制 ({elapsed:.1f}s)")
                success += 1
                continue

            # 3. 投影变换
            # 方法: arcpy.management.Project()
            # 参数: (in_dataset, out_dataset, out_coor_system,
            #        {transform_method}, {in_coor_system},
            #        {preserve_shape}, {max_deviation}, {vertical})
            arcpy.management.Project(
                in_dataset=shp_path,
                out_dataset=out_path,
                out_coor_system=target_sr,
                transform_method=None,       # 让 ArcGIS 自动选转换参数
                in_coor_system=in_sr,
                preserve_shape="NO_PRESERVE_SHAPE",
                max_deviation=None,          # 默认
                vertical=None,               # 3D 时传 VerticalCS 名称
            )

            elapsed = time.time() - t0
            print(f"-> 完成 ({elapsed:.1f}s)")
            success += 1

        except arcpy.ExecuteError as e:
            print(f"\n  [错误] {arcpy.GetMessages(2).strip().split(chr(10))[-1]}")
            failed.append((basename, str(e)))
        except Exception as e:
            print(f"\n  [异常] {e}")
            failed.append((basename, str(e)))

    # ---- 报告 ----
    print("\n" + "=" * 60)
    print(f"完成! 成功: {success}  跳过: {skipped}  失败: {len(failed)}")
    if no_prj:
        print(f"  其中 {no_prj} 个文件无 .prj 使用了假定坐标系")
    if failed:
        print("\n失败列表:")
        for name, err in failed:
            print(f"  - {name}: {err}")


# ======================== 常用坐标系速查 ========================
# EPSG 代号 → 中文含义
COMMON_CS = {
    4326:  "WGS84 (经纬度)",
    4490:  "CGCS2000 (经纬度)",
    4547:  "CGCS2000 3度带 GK CM 120E",
    4548:  "CGCS2000 3度带 GK CM 117E",
    4549:  "CGCS2000 3度带 GK CM 114E",
    4524:  "CGCS2000 3度带 GK CM 123E",
    4544:  "CGCS2000 3度带 GK CM 111E",
    4527:  "CGCS2000 3度带 GK CM 105E",
    3857:  "Web Mercator",
    2383:  "Xian 1980 3度带 GK CM 120E",
    2362:  "Xian 1980 3度带 GK CM 117E",
    2416:  "Beijing 1954 3度带 GK CM 120E",
}


# ======================== 额外工具脚本 ========================

def list_spatial_references(shp_dir):
    """列出目录下所有 shp 的坐标系（检查用）"""
    for shp in Path(shp_dir).rglob("*.shp"):
        try:
            sr = arcpy.Describe(str(shp)).spatialReference
            code = sr.factoryCode if sr.factoryCode else "未知"
            print(f"{shp.name:30s}  EPSG:{code:<8s}  {sr.name}")
        except Exception as e:
            print(f"{shp.name:30s}  读取失败: {e}")


def define_projection(shp_dir, epsg):
    """给所有无 .prj 的 shp 批量定义坐标系"""
    sr = arcpy.SpatialReference(epsg)
    for shp in Path(shp_dir).rglob("*.shp"):
        desc = arcpy.Describe(str(shp))
        if desc.spatialReference.name == "Unknown":
            print(f"定义 {shp.name} -> {sr.name}")
            arcpy.management.DefineProjection(str(shp), sr)


# ======================== 入口 ========================
if __name__ == '__main__':
    # ████████ 请根据实际情况修改上面的配置区 ████████

    # 可选: 先检查一下输入文件的坐标系
    # list_spatial_references(INPUT_DIR)

    # 执行批量投影
    batch_project(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
        target_cs=TARGET_CS,
        default_input_cs=DEFAULT_INPUT_CS,
        overwrite=OVERWRITE,
    )

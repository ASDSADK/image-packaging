"""
场景C（用户修正）：在二级文件夹下新建以二级文件夹命名的 .docx 文档，与三级文件夹同级 -> 收集所有三级文件夹的图片插入

用法：
    python merge_images_to_docx.py <一级文件夹路径>

示例：
    python merge_images_to_docx.py "C:/Users/MyProjects/汇总"
"""

import re
import sys
from pathlib import Path

# 尝试导入 python-docx
try:
    from docx import Document
    from docx.shared import Inches, Cm
    from docx.enum.section import WD_ORIENT
except ImportError:
    print("❌ 请先安装 python-docx: pip install python-docx")
    sys.exit(1)

# 支持的图片扩展名（不区分大小写）
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'}


def is_image_file(filename: str) -> bool:
    """判断文件是否为支持的图片格式"""
    ext = Path(filename).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def collect_images_from_folder(folder_path: Path) -> list[Path]:
    """收集指定文件夹下（含子文件夹）的所有图片文件"""
    images = []
    try:
        for item in sorted(folder_path.rglob('*')):
            if item.is_file() and is_image_file(item.name):
                images.append(item)
    except PermissionError as e:
        print(f"      ⚠ 跳过无权限目录: {e}")
    return images


def add_image_to_doc(doc: Document, img_path: Path, max_width_inches: float = 5.5):
    """向 docx 中插入一张图片（纯图片，无文字）
    异常不上抛由调用方处理"""
    doc.add_picture(str(img_path), width=Inches(max_width_inches))


def process_level2_folder(level2_path: Path, level2_name: str):
    """
    处理一个二级文件夹：
    1. 收集该二级下所有现有的三级文件夹
    2. 在二级文件夹下（与三级文件夹同级）创建以 level2_name 命名的 .docx
    3. 遍历所有三级文件夹，收集图片并插入 .docx
    """
    print(f"\n{'='*60}")
    print(f"📂 处理二级文件夹: {level2_name}")
    print(f"   路径: {level2_path}")

    # ---- 1. 找出所有现有的三级文件夹 ----
    existing_third_dirs: list[Path] = []
    try:
        for item in sorted(level2_path.iterdir()):
            if item.is_dir():
                existing_third_dirs.append(item)
    except PermissionError as e:
        print(f"   ⚠ 跳过无权限目录: {e}")

    if not existing_third_dirs:
        print(f"   ⚠ 二级文件夹下没有三级文件夹，跳过")
        return

    print(f"   发现 {len(existing_third_dirs)} 个已有三级文件夹:")
    for d in existing_third_dirs:
        print(f"     - {d.name}")

    # ---- 2. 创建 .docx 文档（与三级文件夹同级） ----
    docx_path = level2_path / f"{level2_name}.docx"
    if docx_path.exists():
        print(f"   ⚠ {docx_path.name} 已存在，将被覆盖")
    doc = Document()

    # ----- 页面设置（横向，适应图片） -----
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    new_width, new_height = section.page_height, section.page_width
    section.page_width = new_width
    section.page_height = new_height
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    # ---- 3. 遍历所有三级文件夹，收集图片 ----
    total_images = 0
    for third_dir in existing_third_dirs:

        print(f"   🔍 扫描三级文件夹: {third_dir.name}")

        images = collect_images_from_folder(third_dir)
        if not images:
            print(f"      → 无图片")
            continue

        for img_path in images:
            try:
                add_image_to_doc(doc, img_path)
                total_images += 1
                print(f"      ✅ {img_path.name}")
            except Exception as e:
                print(f"      ❌ {img_path.name}: {e}")

    # ---- 4. 保存 ----
    try:
        doc.save(str(docx_path))
        print(f"\n   ✅ 文档已保存: {docx_path}")
        print(f"   📊 共插入 {total_images} 张图片")
    except Exception as e:
        print(f"   ❌ 保存文档失败: {e}")


def main():
    if len(sys.argv) < 2:
        print("用法: python merge_images_to_docx.py <一级文件夹路径>")
        print('示例: python merge_images_to_docx.py "C:/Users/MyData/汇总文件夹"')
        sys.exit(1)

    root_path = Path(sys.argv[1]).resolve()
    if not root_path.is_dir():
        print(f"❌ 路径不存在或不是文件夹: {root_path}")
        sys.exit(1)

    print(f"📌 一级文件夹: {root_path}")
    print(f"📌 开始处理...")

    # 遍历一级文件夹下的所有二级文件夹（自然排序）
    try:
        level2_dirs = sorted([
            item for item in root_path.iterdir()
            if item.is_dir()
        ], key=lambda p: _natural_sort_key(p.name))
    except PermissionError as e:
        print(f"⚠ 跳过无权限目录: {e}")
        level2_dirs = []

    if not level2_dirs:
        print("⚠ 一级文件夹下没有二级文件夹")
        sys.exit(0)

    print(f"📌 发现 {len(level2_dirs)} 个二级文件夹")

    for level2_path in level2_dirs:
        process_level2_folder(level2_path, level2_path.name)

    print(f"\n{'='*60}")
    print("🎉 全部处理完成！")


def _natural_sort_key(name: str):
    """自然排序：二级_2 排在 二级_10 前面"""
    parts = re.split(r'(\d+)', name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


if __name__ == "__main__":
    main()

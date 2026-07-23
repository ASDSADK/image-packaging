---
name: merge-images-to-docx
description: 遍历一级文件夹下的二级文件夹，在二级文件夹下生成与二级文件夹同名的 .docx，收集所有三级文件夹中的图片纯插入（无文字）
---

# merge-images-to-docx

遍历一级文件夹 → 二级文件夹 → 三级文件夹，在每个二级文件夹下生成一个与二级文件夹同名的 `.docx`，将**所有三级文件夹中的图片**纯插入到该文档中（无文字、无标注、无分页）。

## 用法

```bash
python merge_images_to_docx.py "C:/一级文件夹路径"
```

## 目录结构示例

```
一级文件夹/
├── 二级_客户A/
│   ├── 三级_方案1/     ← 图片来源
│   ├── 三级_方案2/     ← 图片来源
│   └── 客户A.docx      ← 生成（含方案1+方案2的图片）
├── 二级_客户B/
│   └── 客户B.docx
```

## 脚本代码

将以下内容保存为 `merge_images_to_docx.py` 后运行：

```python
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Inches, Cm
    from docx.enum.section import WD_ORIENT
except ImportError:
    print("请先安装 python-docx: pip install python-docx")
    sys.exit(1)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}


def is_image_file(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in IMAGE_EXTENSIONS


def collect_images_from_folder(folder_path: Path) -> list[Path]:
    images = []
    for item in sorted(folder_path.rglob('*')):
        if item.is_file() and is_image_file(item.name):
            images.append(item)
    return images


def add_image_to_doc(doc: Document, img_path: Path, max_width_inches: float = 5.5):
    try:
        doc.add_picture(str(img_path), width=Inches(max_width_inches))
    except Exception:
        pass


def process_level2_folder(level2_path: Path, level2_name: str):
    print(f"\\n{'='*60}")
    print(f"处理二级文件夹: {level2_name}")

    existing_third_dirs = sorted([
        item for item in level2_path.iterdir() if item.is_dir()
    ])
    if not existing_third_dirs:
        print("   无三级文件夹，跳过")
        return

    docx_path = level2_path / f"{level2_name}.docx"
    doc = Document()

    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    new_width, new_height = section.page_height, section.page_width
    section.page_width = new_width
    section.page_height = new_height
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    total_images = 0
    for third_dir in existing_third_dirs:
        print(f"   扫描: {third_dir.name}")
        images = collect_images_from_folder(third_dir)
        if not images:
            print("      -> 无图片")
            continue
        for img_path in images:
            add_image_to_doc(doc, img_path)
            total_images += 1
            print(f"      + {img_path.name}")

    doc.save(str(docx_path))
    print(f"   已保存: {docx_path}  ({total_images} 张图片)")


def main():
    if len(sys.argv) < 2:
        print("用法: python merge_images_to_docx.py <一级文件夹路径>")
        sys.exit(1)
    root_path = Path(sys.argv[1]).resolve()
    if not root_path.is_dir():
        print(f"路径不存在: {root_path}")
        sys.exit(1)

    level2_dirs = sorted([item for item in root_path.iterdir() if item.is_dir()])
    print(f"发现 {len(level2_dirs)} 个二级文件夹")
    for level2_path in level2_dirs:
        process_level2_folder(level2_path, level2_path.name)
    print("\\n全部完成！")


if __name__ == "__main__":
    main()
```

## 依赖

```bash
pip install python-docx
```

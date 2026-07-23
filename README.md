# image-packaging

将多级文件夹中的图片自动汇总到 Word 文档中。

## 功能

遍历一级文件夹 → 二级文件夹 → 三级文件夹，在每个二级文件夹下生成一个与二级文件夹同名的 `.docx`，将**所有三级文件夹中的图片**纯插入到该文档中（无文字、无标注、无分页）。

## 快速开始

```bash
pip install python-docx
python merge_images_to_docx.py "C:/你的/一级文件夹路径"
```

## 目录结构

```
一级文件夹/
├── 二级_客户A/
│   ├── 三级_方案1/     ← 图片来源
│   ├── 三级_方案2/     ← 图片来源
│   └── 客户A.docx      ← 生成（含方案1+方案2的图片）
├── 二级_客户B/
│   └── 客户B.docx
```

## Skill 用法

该工具也以 Reasonix Skill 形式提供，可通过 `/merge-images-to-docx` 调用。

## 依赖

- Python 3.8+
- python-docx

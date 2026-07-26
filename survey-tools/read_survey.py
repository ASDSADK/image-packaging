"""
读取测量手簿 txt/dat/csv，提取 点名 + 坐标(X/Y/H)
支持多种常见格式，自动识别分隔符和列顺序
"""
import re
import csv
from pathlib import Path


def read_survey_file(filepath):
    """主函数：读取测量手簿，返回点列表 [{name, x, y, h}, ...]"""
    filepath = Path(filepath)
    text = filepath.read_text(encoding='utf-8-sig')  # utf-8-sig 自动去 BOM

    # 尝试不同解析策略，返回第一个成功的结果
    for parser in [parse_cass_dat, parse_table, parse_generic]:
        result = parser(text)
        if result:
            print(f"[解析成功] 使用策略: {parser.__name__}, 共 {len(result)} 个点")
            return result

    print("[错误] 无法识别文件格式，请检查文件内容")
    return []


# ========== 策略1: CASS .dat 逗号分隔 ==========
def parse_cass_dat(text):
    """格式: 点名,编码,Y,X,H 或 点名,Y,X,H"""
    points = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('--'):
            continue
        parts = [p.strip() for p in line.split(',')]
        try:
            if len(parts) == 5:
                points.append({'name': parts[0], 'y': float(parts[2]),
                               'x': float(parts[3]), 'h': float(parts[4])})
            elif len(parts) == 4:
                points.append({'name': parts[0], 'y': float(parts[1]),
                               'x': float(parts[2]), 'h': float(parts[3])})
        except ValueError:
            return []  # 不是纯数字坐标，换下一种策略
    return points


# ========== 策略2: 通用表格（空格/Tab分隔，有表头） ==========
COLUMN_ALIASES = {
    'name':  ['点名', '点号', '名称', 'ID', 'Name', 'Point'],
    'x':     ['X坐标', 'X', '北坐标', 'N', 'Northing', 'x'],
    'y':     ['Y坐标', 'Y', '东坐标', 'E', 'Easting', 'y'],
    'h':     ['高程', 'H', 'Z', '标高', 'Height', 'Elevation', 'h'],
}


def parse_table(text):
    """识别表头行，按空格/Tab切分，自动匹配列名"""
    lines = text.strip().splitlines()

    # 找表头行
    header_idx = None
    for i, line in enumerate(lines):
        if any(kw in line for kw in ['点名', '点号', 'X坐标', 'Y坐标', '北坐标', '东坐标']):
            header_idx = i
            break
    if header_idx is None:
        return []

    # 解析表头 → 列序号映射
    headers = lines[header_idx].split()
    col_map = {}  # {列序号: ('name'|'x'|'y'|'h')}
    for j, h in enumerate(headers):
        for key, aliases in COLUMN_ALIASES.items():
            if any(a in h for a in aliases):
                col_map[j] = key
                break

    if 'name' not in col_map.values():
        return []

    # 解析数据行
    points = []
    for line in lines[header_idx + 1:]:
        parts = line.split()
        if not parts:
            continue
        row = {}
        for j, key in col_map.items():
            if j < len(parts):
                try:
                    row[key] = float(parts[j])
                except ValueError:
                    row[key] = parts[j]  # 点名保留字符串
        if 'name' in row and 'x' in row and 'y' in row:
            row.setdefault('h', None)
            points.append(row)

    return points


# ========== 策略3: 兜底正则（点名 + 至少2组数字） ==========
def parse_generic(text):
    """从任意文本中提取 点名+数字组，适用于不规则格式"""
    points = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('--'):
            continue

        nums = re.findall(r'[-]?\d+\.?\d*', line)
        if len(nums) < 2:
            continue

        # 取第一个空格段作为点名（如果它不是纯数字）
        first_token = line.split()[0] if line.split() else ''
        if first_token.replace('.', '').replace('-', '').replace('+', '').isdigit():
            name = f"P{len(points)+1}"  # 自动编号
        else:
            name = first_token

        pt = {'name': name, 'x': float(nums[0]), 'y': float(nums[1]),
              'h': float(nums[2]) if len(nums) >= 3 else None}
        points.append(pt)

    return points


# ========== 输出 ==========
if __name__ == '__main__':
    import sys

    # 用法: python read_survey.py 你的手簿文件.txt
    if len(sys.argv) < 2:
        filepath = 'sample_手簿.dat'
        print(f"未指定文件，使用示例文件: {filepath}")
    else:
        filepath = sys.argv[1]

    pts = read_survey_file(filepath)

    if pts:
        print(f"\n{'点名':<10} {'X(北坐标)':>15} {'Y(东坐标)':>15} {'H(高程)':>12}")
        print('-' * 55)
        for p in pts:
            h_str = f"{p['h']:.3f}" if p.get('h') is not None else '-'
            print(f"{p['name']:<10} {p['x']:>15.3f} {p['y']:>15.3f} {h_str:>12}")

        # 同时写出 csv 方便 Excel 打开
        out = Path(filepath).stem + '_提取结果.csv'
        with open(out, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['点名', 'X', 'Y', 'H'])
            for p in pts:
                w.writerow([p['name'], p['x'], p['y'], p.get('h', '')])
        print(f"\n已导出 → {out}")

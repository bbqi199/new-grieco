"""
一键发布脚本
功能：自动找最新CSV → 同步商品数据到index.html → 推送到GitHub
用法：双击运行，或在命令行执行 python 发布更新.py
"""
import csv, json, re, os, glob, subprocess, sys, io
from datetime import datetime

# 修复Windows控制台中文输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ===== 第一步：找最新的CSV文件 =====
csv_files = glob.glob('商品数据*.csv') + glob.glob('*.csv')
csv_files = [f for f in csv_files if '模板' not in f]  # 排除模板文件

if not csv_files:
    print('❌ 找不到CSV文件！请先在商品管理页导出CSV。')
    input('按回车键退出...')
    sys.exit(1)

# 按修改时间取最新的
latest_csv = max(csv_files, key=os.path.getmtime)
print(f'✅ 找到CSV文件：{latest_csv}')

# ===== 第二步：读取CSV，转换商品数据 =====
goods = []
try:
    with open(latest_csv, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            spec_str = row.get('规格选项', '').strip()
            specs = [s.strip() for s in spec_str.split('|') if s.strip()] if '|' in spec_str else ([spec_str] if spec_str else [])
            img = row.get('商品图片URL', '').strip().replace('/images/', 'images/')
            attrs = {}
            kv = row.get('属性键值对', '').strip()
            if kv:
                for pair in kv.split('|'):
                    if ':' in pair:
                        k, v = pair.split(':', 1)
                        attrs[k.strip()] = v.strip()
            try:
                cat_id = int(row['所属分类ID'].strip())
            except:
                cat_id = 0

            g = {
                'id':       row['商品编号'].strip(),
                'catId':    cat_id,
                'emoji':    row.get('商品图标', '📦').strip() or '📦',
                'name':     row['商品名称'].strip(),
                'spec':     row['规格描述'].strip(),
                'price':    float(row['单价']) if row['单价'].strip() else 0,
                'unit':     row['计量单位'].strip(),
                'stock':    int(row['库存数量']) if row['库存数量'].strip() else 999,
                'tag':      [t.strip() for t in row.get('商品标签', '').split(',') if t.strip()],
                'attrs':    attrs,
                'specs':    specs,
                'imageUrl': img
            }
            goods.append(g)
except Exception as e:
    print(f'❌ 读取CSV出错：{e}')
    input('按回车键退出...')
    sys.exit(1)

print(f'✅ 读取商品数据：共 {len(goods)} 件商品')

# ===== 第三步：写入index.html（强制写入，即使内容没变） =====
lines = ['const GOODS_DATA = [']
for i, g in enumerate(goods):
    comma = ',' if i < len(goods) - 1 else ''
    lines.append('  ' + json.dumps(g, ensure_ascii=False, separators=(',', ':')) + comma)
lines.append('];')
new_block = '\n'.join(lines)

with open('index.html', encoding='utf-8') as f:
    content = f.read()

# 先确认 GOODS_DATA 标记存在
if not re.search(r'const GOODS_DATA = \[', content):
    print('❌ 写入失败：index.html 中未找到 GOODS_DATA！')
    input('按回车键退出...')
    sys.exit(1)

# 强制更新 GOODS_DATA
new_content = re.sub(r'const GOODS_DATA = \[.*?\];', new_block, content, flags=re.DOTALL)

# 强制添加时间戳注释，确保每次都有变化
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
new_content = new_content + f'\n<!-- 更新时间: {timestamp} -->'

# 始终写入文件
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

if new_content == content:
    print(f'✅ 数据内容相同，但已更新文件（确保每次都推送，共 {len(goods)} 件）')
else:
    print('✅ 商品数据已写入 index.html')

# ===== 第四步：git add、commit、push =====
now = datetime.now().strftime('%Y-%m-%d %H:%M')
commit_msg = f'更新商品数据 {now}（共{len(goods)}件）'

try:
    # 只添加 index.html，不添加其他文件
    subprocess.run(['git', 'add', '-f', 'index.html'], check=True)

    # 提交
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

    # 推送（正常推送，不强制）
    print('📤 推送到GitHub...')
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)

    print(f'\n🎉 发布成功！约1-2分钟后线上同步。')
    print(f'   线上地址：https://bbqi199.github.io/magazzino/')
except subprocess.CalledProcessError as e:
    print(f'❌ git操作失败：{e}')

input('\n按回车键退出...')

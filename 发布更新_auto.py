"""非交互式发布脚本"""
import csv, json, re, os, glob, subprocess, sys, io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 找最新的CSV文件
csv_files = glob.glob('商品数据*.csv') + glob.glob('*.csv')
csv_files = [f for f in csv_files if '模板' not in f]

if not csv_files:
    print('❌ 找不到CSV文件！')
    sys.exit(1)

latest_csv = max(csv_files, key=os.path.getmtime)
print(f'✅ 找到CSV文件：{latest_csv}')

# 读取CSV
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
    sys.exit(1)

print(f'✅ 读取商品数据：共 {len(goods)} 件商品')

# 写入index.html
lines = ['const GOODS_DATA = [']
for i, g in enumerate(goods):
    comma = ',' if i < len(goods) - 1 else ''
    lines.append('  ' + json.dumps(g, ensure_ascii=False, separators=(',', ':')) + comma)
lines.append('];')
new_block = '\n'.join(lines)

with open('index.html', encoding='utf-8') as f:
    content = f.read()

if not re.search(r'const GOODS_DATA = \[', content):
    print('❌ 写入失败：index.html 中未找到 GOODS_DATA！')
    sys.exit(1)

new_content = re.sub(r'const GOODS_DATA = \[.*?\];', new_block, content, flags=re.DOTALL)

# 添加时间戳确保每次都有变化
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
new_content = new_content + f'\n<!-- 更新时间: {timestamp} -->'

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('✅ 商品数据已写入 index.html')

# Git操作
now = datetime.now().strftime('%Y-%m-%d %H:%M')
commit_msg = f'更新商品数据 {now}（共{len(goods)}件）'

try:
    subprocess.run(['git', 'add', '-f', 'index.html'], check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
    print('📤 推送到GitHub...')
    subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
    print(f'\n🎉 发布成功！约1-2分钟后线上同步。')
    print(f'   线上地址：https://bbqi199.github.io/magazzino/')
except subprocess.CalledProcessError as e:
    print(f'❌ git操作失败：{e}')
    sys.exit(1)

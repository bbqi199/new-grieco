# 长期记忆

## 项目：百货类手机订货程序

- **文件位置**：`c:\Users\ASUS\WorkBuddy\20260326223456\index.html`
- **启动方式**：`python server.py`（必须用这个，不能用 python -m http.server）
- **访问地址**：http://localhost:8888
- **服务脚本**：`server.py` — 同时提供网页服务和图片路由

### 图片库
- **图片目录**：`C:\Users\ASUS\Pictures\foto detersivi`
- **图片数量**：约33,000+张
- **命名规则**：文件名 = 商品EAN条形码编号（例：`0000050204274.jpg`）
- **图片访问**：`/images/{商品编号}.jpg`（服务器自动路由）
- **本地images目录**：`C:\Users\ASUS\WorkBuddy\20260326223456\images`，已同步 11,061 张，约 467MB；每次更新商品数据后可重新运行图片同步脚本补充新商品图片
- **注意**：images 目录体积约467MB，已成功推送到 GitHub Pages；推送大量图片需设置 `git config http.postBuffer 524288000` 避免超时
- **如需线上全图片**：图片超过500MB建议迁移到 OSS/COS
- **重要**：商品id是字符串（EAN码），所有 `find(x=>x.id===goodId)` 必须用 `String(x.id)===String(goodId)`，HTML onclick传id必须加引号如 `openDetail('${g.id}')` 和 `quickAddCart('${g.id}')`，否则"090"变成数字90匹配失败
- **重要**：每次开电脑必须先运行 `python server.py`，服务器不运行图片全部不显示
- **兼容旧数据**：init()加载localStorage时自动补全缺失的imageUrl字段

### 功能模块
- 首页 / 全部商品 / 商品详情 / 购物车 / 结算 / 我的订单 / 个人中心 / 收货地址
- 商品管理页：Excel导入（SheetJS）/ 导出CSV / 商品统计面板
- 所有商品图片：img+emoji双层结构（加载失败自动回退emoji）；**图片尺寸**：全部用 `object-fit:contain`（显示完整图片，不裁剪），共5处（CSS样式3处+JS动态渲染2处）
- **提交订单时**：只同步到 Google Sheets，已移除自动导出Excel功能
- **订单邮件通知**：已集成 EmailJS SDK，submitOrder() 调用 sendOrderEmail()；配置已填入真实值（service_26rqfkn / template_21by9wg / eUVoSNmMG1s6PLsX1）；模板变量：order_no/order_time/buyer_name/buyer_phone/address/items_text/item_count/total/remark；items_text 为 HTML 表格格式，EmailJS 模板需设为 HTML 类型
- **Google Sheets订单同步**：submitOrder()同时调用sendOrderToSheet()，通过Apps Script接口写入表格；表格ID：19iIGhzZbgJMoeOmZm6Fl5wMH69TSomf2Hy9st3oiAiU；**最新Apps Script URL**：`https://script.google.com/macros/s/AKfycbyH7l6GYXGWbEEmtWcU3MaZ9kGNiIWEF5xOPc9ovn55qiYqakhnmPz21S0Z0jOnXAwxTg/exec`；**每个商品单独写一行**，列格式：订单号/下单时间/买家姓名/联系电话/收货地址/商品编号/商品名称/规格/数量/单价/金额/备注/订单合计；payload含items数组（每项：item_no/item_name/item_spec/item_qty/item_price/item_amount）；订单基本信息只在第一行商品显示；Apps Script需重新部署（新建版本）才生效；**重要：必须用GET请求+?data=参数传JSON，POST+no-cors模式会导致body被浏览器丢弃，Apps Script收不到items数组**；Apps Script同时实现doGet和doPost，核心逻辑在writeOrder函数
- **登录系统**（2026-03-28，已回退 index.html）：登录功能曾加入但因CSS display冲突（page-login用position:fixed覆盖app导致所有菜单不可点击）反复出问题，已用 `git checkout f7a8347 -- index.html` 回退到登录前稳定版本。如需重新加入登录，需从干净状态重新实现，注意：#page-login的CSS不能写display:flex（应默认none，用.active类切换）。用户表结构：Google Sheets ID=1-hDBMudcNl3cJWoidrza4phN9Q_nFC_YUZBwNVbxhTg，工作表1，A=用户名/B=密码/C=姓名/D=状态（禁用）
- **登录系统**（2026-03-29，listino.html）：在 listino.html 中成功添加登录功能。方案：#login-overlay用position:fixed独立于#app，JSONP方式验证Google Sheets账号，sessionStorage保存登录状态。Apps Script URL：`https://script.google.com/macros/s/AKfycbyH7l6GYXGWbEEmtWcU3MaZ9kGNiIWEF5xOPc9ovn55qiYqakhnmPz21S0Z0jOnXAwxTg/exec`，action=checkLogin，支持callback参数（JSONP）。账号表工作表名：工作表1。
- 搜索结果每个商品有"🛒 加入购物车"按钮（不触发详情页），`quickAddCart` 从 specs[0] 提取最后数字作为加入数量；搜索支持商品名称和商品编号；**全部商品页**右上角🔍按钮点击展开搜索栏（toggleCatSearch），实时过滤商品显示在goods-panel2中
- **扫码录入页**：底部tabbar新增"扫码"菜单（📷），page-scan页面；scanAdd()函数处理输入，商品库有则匹配，没有也照样按编号加入购物车，数量默认1；已有则累加数量；页面有扫码记录列表（_scanLog数组），✅=找到商品，⚠️=未知商品；切换到扫码页自动聚焦输入框；cart-badge5对应扫码页的购物车徽标
- **商品卡片布局**（2026-03-28最新）：商品名称2行→编号一行→价格/单位·规格同一行+[+]按钮；`.goods-spec`已隐藏，编号用`.goods-id`显示，规格拼在`<span>`里跟在单位后面；搜索结果布局：左侧名称3行+编号·规格同一行，右侧价格/单位+加购按钮

### 数据
- 商品数据：6大分类（日用百货/洗护/食品/玩具文具/服装/五金），初始27个示例商品
- 数据持久化：localStorage（`yg_goods` key）
- 导入的商品数据会持久保存，刷新不丢失

### GitHub Pages 部署
- **线上地址**：https://bbqi199.github.io/magazzino/
- **GitHub仓库**：https://github.com/bbqi199/magazzino
- **图片路径**：已改为相对路径 `images/xxx.jpg`（去掉开头 `/`，适配 GitHub Pages）
- **更新方式**：`git add . && git commit -m "更新" && git push`，1-2分钟后线上同步
- **图片数量**：111张，16.2MB，存放在项目 `images/` 目录
- **注意**：server.py 和 .workbuddy 目录已在 .gitignore 中排除，不会上传
- **商品数据**：88条真实商品已内嵌到 `index.html` 的 `GOODS_DATA` 常量中，新用户打开线上网站直接可见；localStorage 作为额外覆盖层（本地导入用）
- **同步商品数据**：本地导出CSV → python脚本转JSON → 替换index.html里的GOODS_DATA → git push

### 移动端适配
- **viewport**：必须加 `viewport-fit=cover`，否则 `env(safe-area-inset-bottom)` 在iPhone上不生效
- **#app高度**：用 `height:100vh; height:100dvh`（双写，dvh为动态视口高度，兼容iPhone底部Home条）
- **底部按钮**：`.detail-footer` 的 `padding-bottom` 用 `calc(12px + env(safe-area-inset-bottom))`
- **底部tabbar**：已用 `padding-bottom: calc(6px + env(safe-area-inset-bottom))`

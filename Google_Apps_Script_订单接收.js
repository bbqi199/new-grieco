/**
 * =====================================================
 *  ECO-SHOP 订单接收 — Google Apps Script
 * =====================================================
 *
 *  【部署步骤】
 *  1. 打开 Google Sheets，新建一个表格
 *  2. 点击「扩展程序」→「Apps Script」
 *  3. 删除编辑器中的默认代码，将本文件全部内容粘贴进去
 *  4. 点击「部署」→「新建部署」
 *     - 类型：选择「Web 应用」
 *     - 执行身份：我（你的 Google 账号）
 *     - 谁可以访问：所有人（或仅限你需要的用户）
 *  5. 部署后复制「Web 应用 URL」
 *  6. 将 URL 粘贴到 index.html 中的 GSHEET_URL 变量里
 *
 *  【表格自动创建的 Sheet 说明】
 *  - "Orders"：订单汇总（一笔订单一行）
 *  - "Items"：商品明细（每个商品一行）
 *  - "Log"：操作日志（调试用）
 *
 *  =====================================================
 */

/* ====================================================
   配置区 —— 你可以按需修改
   ==================================================== */
var CONFIG = {
  // Sheet 名称
  SHEET_ORDERS: 'Orders',
  SHEET_ITEMS:  'Items',
  SHEET_LOG:    'Log',

  // 表头定义
  ORDER_HEADERS: [
    '订单号',       // A
    '下单时间',     // B
    '买家姓名',     // C
    '买家电话',     // D
    '收货地址',     // E
    '备注',         // F
    '订单总额(€)',  // G
    '商品数量',     // H
    '同步时间'      // I
  ],

  ITEM_HEADERS: [
    '订单号',       // A
    '商品编码',     // B
    '商品名称',     // C
    '规格',         // D
    '标签',         // E
    '箱数',         // F
    '单箱价格(€)',  // G
    '总金额(€)'     // H
  ]
};

/* ====================================================
   Web App 入口：doGet
   ==================================================== */
function doGet(e) {
  try {
    var action = (e.parameter.action || '').toLowerCase();

    switch (action) {
      case 'readorders':
        return jsonRes(readOrders(e));

      case 'readitems':
        return jsonRes(readItems(e));

      case 'deleteorder':
        return jsonRes(deleteOrder(e));

      case 'clearall':
        return jsonRes(clearAllData());

      default:
        // 无 action 或 action 为空 → 处理写入订单
        if (e.parameter.data) {
          var result = handleOrderSubmit(e);
          return jsonRes(result);
        }
        return jsonRes({ status: 'ok', message: 'ECO-SHOP API Running. Use ?action=readOrders to get orders.' });
    }
  } catch (err) {
    log('ERROR', err.toString());
    return jsonRes({ status: 'error', message: err.toString() });
  }
}

/* 也支持 POST（备用） */
function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var result = handleOrderSubmit(payload);
    return jsonRes(result);
  } catch (err) {
    log('ERROR', 'POST: ' + err.toString());
    return jsonRes({ status: 'error', message: err.toString() });
  }
}

/* ====================================================
   核心：写入订单
   ==================================================== */
function handleOrderSubmit(e) {
  var data = e.parameter.data ? JSON.parse(e.parameter.data) : (e.data || e);

  if (!data || !data.items || data.items.length === 0) {
    return { status: 'error', message: '没有订单数据' };
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // ---------- 1) 确保所有 Sheet 存在 ----------
  ensureSheet(ss, CONFIG.SHEET_ORDERS, CONFIG.ORDER_HEADERS);
  ensureSheet(ss, CONFIG.SHEET_ITEMS,  CONFIG.ITEM_HEADERS);

  // ---------- 2) 写入订单汇总行 ----------
  var orderSheet = ss.getSheetByName(CONFIG.SHEET_ORDERS);
  var orderRow = [
    data.order_no    || '',
    data.order_time  || '',
    data.buyer_name  || '',
    data.buyer_phone || '',
    data.address     || '',
    data.remark      || '',
    data.total       || 0,
    data.items.length,
    new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' })
  ];
  orderSheet.appendRow(orderRow);
  autoResize(orderSheet);

  // ---------- 3) 写入商品明细行（每个商品一行） ----------
  var itemSheet = ss.getSheetByName(CONFIG.SHEET_ITEMS);
  var items = data.items || [];

  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var itemRow = [
      data.order_no          || '',
      item.item_no           || '',
      item.item_name         || '',
      item.item_spec         || '',
      item.item_label        || '',
      item.item_qty          || 0,
      item.item_price        || 0,
      item.item_amount       || 0
    ];
    itemSheet.appendRow(itemRow);
  }
  autoResize(itemSheet);

  // ---------- 4) 日志 ----------
  log('ORDER', '订单号: ' + (data.order_no || '') + ', 商品数: ' + items.length + ', 总额: €' + (data.total || 0));

  return {
    status: 'success',
    message: '订单 ' + (data.order_no || '') + ' 已写入表格',
    order_no: data.order_no
  };
}

/* ====================================================
   读取订单
   ==================================================== */
function readOrders(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SHEET_ORDERS);
  if (!sheet) return { orders: [] };

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return { orders: [] }; // 只有表头

  var headers = data[0];
  var orders = [];

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    if (!row[0]) continue; // 跳过空行
    var order = {};
    for (var j = 0; j < headers.length; j++) {
      order[headers[j]] = row[j];
    }
    orders.push(order);
  }

  return { orders: orders, total: orders.length };
}

/* ====================================================
   读取商品明细
   ==================================================== */
function readItems(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SHEET_ITEMS);
  if (!sheet) return { items: [] };

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return { items: [] };

  var headers = data[0];
  var items = [];

  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    if (!row[0]) continue;
    var item = {};
    for (var j = 0; j < headers.length; j++) {
      item[headers[j]] = row[j];
    }
    items.push(item);
  }

  return { items: items, total: items.length };
}

/* ====================================================
   删除指定订单
   ==================================================== */
function deleteOrder(e) {
  var orderNo = e.parameter.order_no || '';
  if (!orderNo) return { status: 'error', message: '缺少 order_no 参数' };

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // 从 Orders 中删除
  var orderSheet = ss.getSheetByName(CONFIG.SHEET_ORDERS);
  if (orderSheet) {
    var orderData = orderSheet.getDataRange().getValues();
    for (var i = orderData.length - 1; i >= 1; i--) {
      if (orderData[i][0] == orderNo) {
        orderSheet.deleteRow(i + 1);
      }
    }
  }

  // 从 Items 中删除关联的商品行
  var itemSheet = ss.getSheetByName(CONFIG.SHEET_ITEMS);
  if (itemSheet) {
    var itemData = itemSheet.getDataRange().getValues();
    for (var i = itemData.length - 1; i >= 1; i--) {
      if (itemData[i][0] == orderNo) {
        itemSheet.deleteRow(i + 1);
      }
    }
  }

  log('DELETE', '已删除订单: ' + orderNo);
  return { status: 'success', message: '订单 ' + orderNo + ' 已删除' };
}

/* ====================================================
   清空所有数据（危险操作！仅保留表头）
   ==================================================== */
function clearAllData() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  [CONFIG.SHEET_ORDERS, CONFIG.SHEET_ITEMS, CONFIG.SHEET_LOG].forEach(function(name) {
    var sheet = ss.getSheetByName(name);
    if (sheet) {
      sheet.deleteRows(2, Math.max(1, sheet.getLastRow() - 1));
    }
  });

  log('CLEAR', '所有数据已清空');
  return { status: 'success', message: '所有数据已清空' };
}

/* ====================================================
   工具函数
   ==================================================== */

/** 确保 Sheet 存在且表头正确 */
function ensureSheet(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight('bold')
      .setBackground('#4a86e8')
      .setFontColor('#ffffff');
    sheet.setFrozenRows(1);
  } else if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setFontWeight('bold')
      .setBackground('#4a86e8')
      .setFontColor('#ffffff');
    sheet.setFrozenRows(1);
  }
}

/** 自动调整列宽 */
function autoResize(sheet) {
  var lastCol = sheet.getLastColumn();
  if (lastCol > 0) {
    for (var c = 1; c <= lastCol; c++) {
      sheet.autoResizeColumn(c);
    }
  }
}

/** 写入日志 */
function log(type, message) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SHEET_LOG);
  if (!sheet) {
    sheet = ss.insertSheet(CONFIG.SHEET_LOG);
    sheet.appendRow(['时间', '类型', '内容']);
    sheet.getRange(1, 1, 1, 3)
      .setFontWeight('bold')
      .setBackground('#f6b26b')
      .setFontColor('#ffffff');
    sheet.setFrozenRows(1);
  }
  sheet.appendRow([
    new Date().toLocaleString('it-IT', { timeZone: 'Europe/Rome' }),
    type,
    message
  ]);
}

/** 返回 JSON 响应 */
function jsonRes(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ====================================================
   定时触发器：可选（每日清理超过 90 天的旧日志）
   在 Apps Script 编辑器 → 触发器 → 添加触发器
   函数选 cleanOldLogs，时间驱动：每天执行
   ==================================================== */
function cleanOldLogs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SHEET_LOG);
  if (!sheet || sheet.getLastRow() <= 1) return;

  var cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 90);

  var data = sheet.getDataRange().getValues();
  var rowsToDelete = [];

  for (var i = data.length - 1; i >= 1; i--) {
    var timeStr = data[i][0];
    if (timeStr) {
      // 尝试解析时间
      var parts = timeStr.split(/[\/: ]/);
      if (parts.length >= 6) {
        var rowDate = new Date(parts[2], parts[1] - 1, parts[0], parts[3], parts[4], parts[5]);
        if (rowDate < cutoff) {
          rowsToDelete.push(i + 1);
        }
      }
    }
  }

  // 从后往前删除，避免索引偏移
  for (var i = 0; i < rowsToDelete.length; i++) {
    sheet.deleteRow(rowsToDelete[i]);
  }

  if (rowsToDelete.length > 0) {
    log('CLEANUP', '已清理 ' + rowsToDelete.length + ' 条过期日志');
  }
}

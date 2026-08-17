// ─────────────────────────────────────────────────────────────────────────────
// monthly-expense-report / skill.js
// 架构说明：本文件是纯 JS 数据处理层（eval5 沙箱执行），不含任何 async/await 或 ExcelJS 调用。
// 从而避免在 eval5 沙箱中引入 regenerator-runtime 导致 CPU 时间超限崩溃。
// Excel 填表 I/O 全部由 Worker 主线程原生执行（见 worker.js fillPHKAndWriteBuffer）。
// ─────────────────────────────────────────────────────────────────────────────

// ── 静态模板结构元数据（解耦设计：由技能定义并返回给 Worker） ───────────────
var TEMPLATE_META = {
  subtotalColIndex: 31,
  totalsRow: 21,
  dataStartRow: 9,
  applicantRow: 3,
  applicantCol: 3,
  dateRow: 5,
  dateCol: 31,
  feeColumns: [
    { col: 12, name: "电话费" },
    { col: 13, name: "车费" },
    { col: 14, name: "餐费" },
    { col: 15, name: "交际费" },
    { col: 16, name: "电脑配件更换" },
    { col: 17, name: "油费" },
    { col: 18, name: "停车费" },
    { col: 19, name: "代驾费" },
    { col: 20, name: "快递" },
    { col: 21, name: "杂费" },
    { col: 22, name: "办公费" },
    { col: 23, name: "维修费" },
    { col: 24, name: "签证费用" },
    { col: 25, name: "办证费用" },
    { col: 26, name: "保险费" },
    { col: 27, name: "机票" },
    { col: 28, name: "Others" },
    { col: 29, name: "酒费" },
    { col: 30, name: "礼品卡" }
  ],
  originalDataRowCount: 12
};

// ── 辅助：费用类型标准化 ────────────────────────────────────────────────────
function normalizeTypeName(type) {
  if (!type) return '';
  var t = type.trim().toLowerCase();
  if (t.indexOf('电话') !== -1 || t.indexOf('手機') !== -1 || t.indexOf('手机') !== -1 || t.indexOf('通讯') !== -1 || t.indexOf('通信') !== -1 || t.indexOf('话费') !== -1 || t.indexOf('phone') !== -1 || t.indexOf('mobile') !== -1 || t.indexOf('telecom') !== -1) return '电话费';
  
  if (t.indexOf('机票') !== -1 || t.indexOf('機票') !== -1 || t.indexOf('飞机') !== -1 || t.indexOf('飛機') !== -1 || t.indexOf('flight') !== -1 || t.indexOf('air') !== -1) return '机票';
  if (t.indexOf('保险') !== -1 || t.indexOf('保險') !== -1 || t.indexOf('insurance') !== -1) return '保险费';
  
  if (t.indexOf('加油') !== -1 || t.indexOf('汽油') !== -1 || t.indexOf('柴油') !== -1 || t.indexOf('油卡') !== -1 || t.indexOf('油费') !== -1 || t.indexOf('油費') !== -1) return '油费';
  if (t.indexOf('停车') !== -1 || t.indexOf('車位') !== -1 || t.indexOf('车位') !== -1 || t.indexOf('泊车') !== -1 || t.indexOf('停車') !== -1) return '停车费';
  if (t.indexOf('代驾') !== -1 || t.indexOf('代駕') !== -1) return '代驾费';

  // 快递
  if (t.indexOf('快递') !== -1 || t.indexOf('快遞') !== -1 || t.indexOf('邮寄') !== -1 || t.indexOf('郵寄') !== -1 || t.indexOf('顺丰') !== -1 || t.indexOf('順豐') !== -1 || t.indexOf('邮政') !== -1 || t.indexOf('郵政') !== -1 || t.indexOf('邮递') !== -1 || t.indexOf('郵遞') !== -1 || t.indexOf('ems') !== -1 || t.indexOf('shunfeng') !== -1 || t.indexOf('courier') !== -1 || t.indexOf('express') !== -1) return '快递';

  if (t.indexOf('交通') !== -1 || t.indexOf('车') !== -1 || t.indexOf('打车') !== -1 || t.indexOf('滴滴') !== -1 || t.indexOf('出行') !== -1 || t.indexOf('过路') !== -1 || t.indexOf('路桥') !== -1 || t.indexOf('高速') !== -1 || t.indexOf('taxi') !== -1 || t.indexOf('commute') !== -1 || t.indexOf('火车') !== -1 || t.indexOf('火車') !== -1 || t.indexOf('高铁') !== -1 || t.indexOf('高鐵') !== -1 || t.indexOf('动车') !== -1 || t.indexOf('動車') !== -1 || t.indexOf('train') !== -1 || t.indexOf('住宿') !== -1 || t.indexOf('酒店') !== -1 || t.indexOf('hotel') !== -1 || t.indexOf('stay') !== -1) return '车费';
  
  if (t.indexOf('餐') !== -1 || t.indexOf('饭') !== -1 || t.indexOf('飯') !== -1 || t.indexOf('餐饮') !== -1 || t.indexOf('餐飲') !== -1 || t.indexOf('meal') !== -1 || t.indexOf('food') !== -1 || t.indexOf('dining') !== -1 || t.indexOf('restaurant') !== -1) return '餐费';
  if (t.indexOf('交际') !== -1 || t.indexOf('交際') !== -1 || t.indexOf('招待') !== -1 || t.indexOf('宴请') !== -1 || t.indexOf('宴請') !== -1 || t.indexOf('entertainment') !== -1 || t.indexOf('client') !== -1) return '交际费';
  
  if (t.indexOf('电脑') !== -1 || t.indexOf('電腦') !== -1 || t.indexOf('配件') !== -1 || t.indexOf('更换') !== -1 || t.indexOf('更換') !== -1 || t.indexOf('computer') !== -1 || t.indexOf('hardware') !== -1) return '电脑配件更换';
  
  if (t.indexOf('办公') !== -1 || t.indexOf('辦公') !== -1 || t.indexOf('文具') !== -1 || t.indexOf('鼠标') !== -1 || t.indexOf('滑鼠') !== -1 || t.indexOf('键盘') !== -1 || t.indexOf('鍵盤') !== -1 || t.indexOf('stationery') !== -1 || t.indexOf('office') !== -1 || t.indexOf('supply') !== -1) return '办公费';
  
  if (t.indexOf('维修') !== -1 || t.indexOf('維修') !== -1 || t.indexOf('修缮') !== -1 || t.indexOf('修繕') !== -1 || t.indexOf('repair') !== -1) return '维修费';
  
  if (t.indexOf('签证') !== -1 || t.indexOf('簽證') !== -1 || t.indexOf('visa') !== -1) return '签证费用';
  if (t.indexOf('办证') !== -1 || t.indexOf('辦證') !== -1 || t.indexOf('通行证') !== -1 || t.indexOf('通行證') !== -1 || t.indexOf('passport') !== -1) return '办证费用';
  
  if (t.indexOf('礼品') !== -1 || t.indexOf('禮品') !== -1 || t.indexOf('礼物') !== -1 || t.indexOf('禮物') !== -1 || t.indexOf('gift') !== -1 || t.indexOf('card') !== -1) return '礼品卡';
  if (t.indexOf('酒') !== -1 || t.indexOf('wine') !== -1 || t.indexOf('alcohol') !== -1 || t.indexOf('beer') !== -1) return '酒费';
  
  if (t.indexOf('杂费') !== -1 || t.indexOf('雜費') !== -1 || t.indexOf('清洁') !== -1 || t.indexOf('清潔') !== -1 || t.indexOf('水电') !== -1 || t.indexOf('水電') !== -1 || t.indexOf('电费') !== -1 || t.indexOf('電費') !== -1 || t.indexOf('gas') !== -1 || t.indexOf('water') !== -1 || t.indexOf('power') !== -1 || t.indexOf('utility') !== -1) return '杂费';
  
  return 'Others';
}

// ── 辅助：费用类型到模板列名模糊匹配 ──────────────────────────────────────
function findBestMatchedColumn(t, colNames) {
  if (!t || colNames.length === 0) return colNames[colNames.length - 1] || '';
  if (colNames.indexOf(t) !== -1) return t;

  var clean = function(s) {
    return (s || '').trim()
      .replace(/費/g, '费').replace(/車/g, '车').replace(/電/g, '电')
      .replace(/辦/g, '办').replace(/雜/g, '杂').replace(/維/g, '维')
      .replace(/裝/g, '装').replace(/機/g, '机').replace(/飛/g, '飞')
      .replace(/鐵/g, '铁').replace(/賓/g, '宾');
  };
  var cleanT = clean(t);
  var exact = colNames.find(function(c) { return clean(c) === cleanT; });
  if (exact) return exact;

  var code = normalizeTypeName(t);
  var byCode = colNames.find(function(c) { return normalizeTypeName(c) === code; });
  if (byCode) return byCode;

  var lowerT = t.toLowerCase();
  var kwMap = [
    { keys: ['电话', '手机', '话费', '通讯', '通信', 'phone', 'mobile', '手機電話'], codes: ['phone', '电话', '手機', '手机'] },
    { keys: ['交通', '打车', '滴滴', '出行', '过路', '路桥', '高速', 'taxi', 'commute', '火车', '火車', '高铁', '高鐵', '动车', '動車', 'train', '住宿', '酒店', 'hotel', 'stay'], codes: ['commute', '车费', '交通费'] },
    { keys: ['机票', '飞机', 'flight'], codes: ['机票'] },
    { keys: ['保险', 'insurance'], codes: ['保险费'] },
    { keys: ['加油', '汽油', '柴油', '油卡', '油费'], codes: ['油费'] },
    { keys: ['停车', '车位', '泊车'], codes: ['停车费'] },
    { keys: ['代驾'], codes: ['代驾费'] },
    { keys: ['快递', '顺丰', '邮寄', '邮政', 'shunfeng', 'courier', 'express'], codes: ['快递'] },
    { keys: ['餐', '饭', '用餐', '餐饮', '就餐', 'meal', 'food', 'dining'], codes: ['meal', '餐费', '餐'] },
    { keys: ['交际', '招待', '宴请', 'entertainment', 'client'], codes: ['entertainment', '交际费', '交際'] },
    { keys: ['电脑', '配件', 'computer', 'hardware'], codes: ['电脑配件更换'] },
    { keys: ['办公', '文具', '鼠标', '键盘', 'stationery', 'office', 'supply'], codes: ['办公费'] },
    { keys: ['维修', '修缮', 'repair'], codes: ['维修费'] },
    { keys: ['签证', 'visa'], codes: ['签证费用'] },
    { keys: ['办证', '通行证', 'passport'], codes: ['办证费用'] },
    { keys: ['礼品', '礼物', 'gift', 'card'], codes: ['礼品卡'] },
    { keys: ['酒', 'wine', 'beer'], codes: ['酒费'] },
    { keys: ['杂费', '杂', '清洁', '水电', '电费', 'utility'], codes: ['杂费'] },
  ];
  for (var i = 0; i < kwMap.length; i++) {
    var entry = kwMap[i];
    if (entry.keys.some(function(k) { return lowerT.indexOf(k) !== -1; })) {
      for (var j = 0; j < entry.codes.length; j++) {
        var m = colNames.find(function(c) { return normalizeTypeName(c) === entry.codes[j] || c.indexOf(entry.codes[j]) !== -1; });
        if (m) return m;
      }
    }
  }

  // Fallback to "Others" column
  var othersCol = colNames.find(function(c) {
    var name = c.toLowerCase();
    return name.indexOf('others') !== -1 || name.indexOf('其它') !== -1 || name.indexOf('其他') !== -1 || name.indexOf('other') !== -1;
  });
  if (othersCol) return othersCol;

  return colNames[colNames.length - 1];
}

function mergeInvoicesByDate(invoices) {
  var businessTripDates = {};
  invoices.forEach(function(inv) {
    var type = (inv.type || '').trim();
    var summary = (inv.summary || '').toLowerCase();
    var client = (inv.client || '').toLowerCase();
    
    var isTripType = (type === '飞机票' || type === '机票' || type === '火车票' || type === '高铁' || type === '火车票/大巴票' || type === '住宿');
    var hasRoute = inv.from || inv.to;
    var mentionsTrip = summary.includes('出差') || summary.includes('往返') || summary.includes('飞机') || summary.includes('火车') || summary.includes('高铁') ||
                       client.includes('航空') || client.includes('铁路') || client.includes('客运') ||
                       /武汉-深圳|深圳-武汉|武汉至深圳|深圳至武汉/.test(summary) || /武汉-深圳|深圳-武汉/.test(client);
                         
    if ((isTripType || hasRoute || mentionsTrip) && inv.date) {
      businessTripDates[inv.date] = true;
    }
  });

  var tripGroups = {};
  var localCourierInvoices = [];
  var localTransitInvoices = [];
  var processedRows = [];

  var courierTypes = ['快递费', '邮寄', '郵寄', '顺丰', '順豐', '快递', '邮政', '郵政', '寄', 'packaging'];

  invoices.forEach(function(inv) {
    var type = (inv.type || '').trim();
    var summary = (inv.summary || '').toLowerCase();
    var client = (inv.client || '').toLowerCase();
    var date = inv.date;

    var isTripInvoice = ['飞机票', '机票', '火车票', '高铁', '火车票/大巴票', '交通费', '交通費', '的士', '打车', '滴滴', '保险', '旅行险', '住宿', '酒店', '餐费', '餐費', 'commute', 'meal', 'entertainment'].indexOf(inv.type) !== -1 ||
                        inv.from || inv.to || summary.includes('出差') || summary.includes('往返');

    if (date && businessTripDates[date] && isTripInvoice) {
      if (!tripGroups[date]) {
        tripGroups[date] = [];
      }
      tripGroups[date].push(inv);
    }
    else if (courierTypes.indexOf(type) !== -1 || summary.includes('快递') || summary.includes('邮寄') || summary.includes('顺丰') || summary.includes('邮政')) {
      localCourierInvoices.push(inv);
    }
    else if (summary.includes('加油') || summary.includes('汽油') || summary.includes('柴油') || summary.includes('油卡') || type.includes('油')) {
      var amounts = {};
      amounts[inv.type] = inv.amount;
      processedRows.push({
        date: inv.date,
        client: '油费',
        from: '',
        to: '',
        productLine: inv.productLine || 'OTHER',
        amounts: amounts,
        amount: inv.amount,
        summary: '',
        originalInvoices: [inv]
      });
    }
    else if (summary.includes('停车') || summary.includes('车位') || summary.includes('泊车') || type.includes('停车')) {
      var amounts = {};
      amounts[inv.type] = inv.amount;
      processedRows.push({
        date: inv.date,
        client: '停车费',
        from: '',
        to: '',
        productLine: inv.productLine || 'OTHER',
        amounts: amounts,
        amount: inv.amount,
        summary: '',
        originalInvoices: [inv]
      });
    }
    else if (summary.includes('代驾') || type.includes('代驾')) {
      var amounts = {};
      amounts[inv.type] = inv.amount;
      processedRows.push({
        date: inv.date,
        client: '代驾费',
        from: '',
        to: '',
        productLine: inv.productLine || 'OTHER',
        amounts: amounts,
        amount: inv.amount,
        summary: '',
        originalInvoices: [inv]
      });
    }
    else if (type === '交通费' || type === '交通費' || type === 'commute' || summary.includes('打车') || summary.includes('的士') || summary.includes('滴滴') || summary.includes('出行')) {
      localTransitInvoices.push(inv);
    }
    else if (type === 'meal' || type === 'entertainment' || type === '餐费' || type === '交际费' || type === '交際' || type === '餐費' || type === '招待') {
      var amounts = {};
      amounts[inv.type] = inv.amount;
      var merchant = inv.client || '餐馆';
      var people = inv.people || 3;
      processedRows.push({
        date: inv.date,
        client: '',
        from: '',
        to: '',
        productLine: inv.productLine || 'OTHER',
        amounts: amounts,
        amount: inv.amount,
        summary: merchant + '，' + people + '人',
        originalInvoices: [inv]
      });
    }
    else if (type === 'phone' || type === '电话费' || type === '電話' || type === '手機' || type === '手机' || summary.includes('电话') || summary.includes('手机')) {
      var amounts = {};
      amounts[inv.type] = inv.amount;
      processedRows.push({
        date: inv.date,
        client: '电话费',
        from: '',
        to: '',
        productLine: inv.productLine || 'OTHER',
        amounts: amounts,
        amount: inv.amount,
        summary: '',
        originalInvoices: [inv]
      });
    }
    else {
      var amounts = {};
      amounts[inv.type] = inv.amount;
      processedRows.push({
        date: inv.date,
        client: inv.client || '',
        from: '',
        to: '',
        productLine: inv.productLine || 'OTHER',
        amounts: amounts,
        amount: inv.amount,
        summary: inv.summary || inv.type || '其它',
        originalInvoices: [inv]
      });
    }
  });

  // 3.3 组装出差行
  var tripDates = Object.keys(tripGroups);
  tripDates.forEach(function(date) {
    var invs = tripGroups[date];
    var amounts = {};
    var totalAmount = 0;
    var summaries = [];
    var clients = [];
    var tripFrom = '';
    var tripTo = '';

    invs.forEach(function(inv) {
      var t = inv.type || '其它';
      amounts[t] = (amounts[t] || 0) + inv.amount;
      totalAmount += inv.amount;
      
      var desc = inv.summary || inv.type || '';
      if (inv.client && !desc.includes(inv.client)) {
        desc = desc + '(' + inv.client + ')';
      }
      if (desc) summaries.push(desc);
      if (inv.client && clients.indexOf(inv.client) === -1) clients.push(inv.client);
      if (inv.from && !tripFrom) tripFrom = inv.from;
      if (inv.to && !tripTo) tripTo = inv.to;
    });

    processedRows.push({
      date: date,
      client: clients.join('/') || '出差费用',
      from: tripFrom,
      to: tripTo,
      productLine: 'WHPA',
      amounts: amounts,
      amount: totalAmount,
      summary: '出差大交通及相关: ' + summaries.join('，'),
      originalInvoices: invs
    });
  });

  // 3.4 组装本地快递/邮政行
  if (localCourierInvoices.length > 0) {
    var courierAmounts = {};
    var totalCourierAmount = 0;
    
    localCourierInvoices.forEach(function(inv) {
      var t = inv.type || '其它';
      courierAmounts[t] = (courierAmounts[t] || 0) + inv.amount;
      totalCourierAmount += inv.amount;
    });

    localCourierInvoices.sort(function(a, b) { return new Date(a.date) - new Date(b.date); });
    var courierDate = localCourierInvoices[0].date;

    processedRows.push({
      date: courierDate,
      client: '快递费',
      from: '',
      to: '',
      productLine: 'OTHER',
      amounts: courierAmounts,
      amount: totalCourierAmount,
      summary: '',
      originalInvoices: localCourierInvoices
    });
  }

  // 3.5 组装本地交通行
  var localTransitRow = null;
  if (localTransitInvoices.length > 0) {
    var transitAmounts = {};
    var totalTransitAmount = 0;
    
    localTransitInvoices.forEach(function(inv) {
      var t = inv.type || '其它';
      transitAmounts[t] = (transitAmounts[t] || 0) + inv.amount;
      totalTransitAmount += inv.amount;
    });

    localTransitInvoices.sort(function(a, b) { return new Date(a.date) - new Date(b.date); });
    var transitDate = localTransitInvoices[0].date;

    localTransitRow = {
      date: transitDate,
      client: '交通费',
      from: '',
      to: '',
      productLine: 'OTHER',
      amounts: transitAmounts,
      amount: totalTransitAmount,
      summary: '',
      originalInvoices: localTransitInvoices
    };
  }

  // 3.6 组装电话费行与其它独立行并整体按日期排序
  var phoneRows = [];
  var otherIndependentRows = [];

  processedRows.forEach(function(row) {
    if (row.client === '电话费') {
      phoneRows.push(row);
    } else {
      otherIndependentRows.push(row);
    }
  });

  // 各类别内部进行排序
  otherIndependentRows.sort(function(a, b) { return new Date(a.date) - new Date(b.date); });
  phoneRows.sort(function(a, b) { return new Date(a.date) - new Date(b.date); });

  var finalMergedRows = [];
  
  // 电话费行排在第一行
  phoneRows.forEach(function(r) { finalMergedRows.push(r); });

  // 本地出行交通车费排在第二行
  if (localTransitRow) {
    finalMergedRows.push(localTransitRow);
  }

  // 其它所有行按日期排序放在后面
  var remainingRows = [].concat(otherIndependentRows);
  remainingRows.sort(function(a, b) { return new Date(a.date) - new Date(b.date); });
  remainingRows.forEach(function(r) { finalMergedRows.push(r); });

  return finalMergedRows;
}

// ── 默认导出：纯 JS 数据计算（无 ExcelJS，完全同步） ────────────────
export default function monthlyExpenseReport(processed, env) {
  var applicant = (env.applicant || '').trim();
  var productLine = (env.productLine || 'WHPA').trim();
  var today = new Date();
  var todayStr = today.getFullYear() + '/' + String(today.getMonth() + 1).padStart(2, '0') + '/' + String(today.getDate()).padStart(2, '0');
  var month = today.getMonth() + 1;

  // 获取发票数据
  var invoices = env.confirmedInvoices || (env.confirmedData && env.confirmedData.invoices) || [];
  // 如果 confirmedData 本身是数组（直接传入发票列表），则直接使用
  if (!invoices.length && Array.isArray(env.confirmedData)) {
    invoices = env.confirmedData;
  }

  // 使用技能自带的静态模板结构信息
  var templateMeta = TEMPLATE_META;
  var feeColumns = templateMeta.feeColumns || [];
  var colNames = feeColumns.map(function(fc) { return fc.name; });

  // 标准化发票类型
  var normalizedInvoices = invoices.map(function(inv) {
    return {
      date: inv.date || '',
      client: inv.client || '',
      from: inv.from || '',
      to: inv.to || '',
      summary: inv.summary || '',
      amount: Number(inv.amount || 0),
      type: normalizeTypeName(inv.type || inv.suggestedType || ''),
      people: inv.people || 0,
      fileName: inv.fileName || inv.filename || ''
    };
  });

  // 按日期合并
  var mergedRows = mergeInvoicesByDate(normalizedInvoices);

  // 为每行计算列分配（纯 JS 业务逻辑，核心热插拔点）
  var rows = mergedRows.map(function(row) {
    var colAmounts = {};
    var typeNames = Object.keys(row.amounts);
    for (var ti = 0; ti < typeNames.length; ti++) {
      var typeName = typeNames[ti];
      var amount = row.amounts[typeName];
      var matchedColName = findBestMatchedColumn(typeName, colNames);
      var matchedFeeCol = null;
      for (var fi = 0; fi < feeColumns.length; fi++) {
        if (feeColumns[fi].name === matchedColName) { matchedFeeCol = feeColumns[fi]; break; }
      }
      if (!matchedFeeCol && feeColumns.length > 0) {
        matchedFeeCol = feeColumns[feeColumns.length - 1]; // 兜底：最后一列
      }
      if (matchedFeeCol) {
        var col = matchedFeeCol.col;
        colAmounts[col] = (colAmounts[col] || 0) + amount;
      }
    }
    return {
      date: row.date,
      client: row.client || '',
      from: row.from || '',
      to: row.to || '',
      summary: row.summary || '',
      amount: row.amount,
      colAmounts: colAmounts  // { colIndex: amount }  → Worker 直接填格子
    };
  });

  var totalSum = rows.reduce(function(s, r) { return s + r.amount; }, 0);

  var clientData = {
    totalUploaded: invoices.length,
    totalProcessed: rows.length,
    matchStatus: rows.length === invoices.length ? '正常' : ('已合并(原' + invoices.length + '张→' + rows.length + '行)')
  };

  var tableData = {
    applicant: applicant,
    productLine: productLine,
    date: todayStr,
    rows: rows.map(function(r) {
      return { date: r.date, client: r.client, from: r.from, to: r.to, summary: r.summary, amount: Number(r.amount.toFixed(2)) };
    }),
    totals: { totalSum: Number(totalSum.toFixed(2)) }
  };

  // 返回纯数据，Worker 原生负责 Excel 填写
  return {
    type: 'excel_data',
    applicant: applicant,
    productLine: productLine,
    month: month,
    todayStr: todayStr,
    rows: rows,
    filename: (applicant || 'Monthly') + '_' + month + '\u6708\u62a5\u9500\u8868.xlsx',
    addedCount: rows.length,
    clientData: clientData,
    tableData: tableData,
    templateMeta: templateMeta // 携带元数据返回
  };
}

/* 茶息看板 —— Echarts 渲染逻辑
 * 所有数据走 fetch 异步请求后端接口，前端不写死任何业务数据。
 */
const THEME = ['#6f9e77', '#c8a15a', '#c87941', '#5e8fa6', '#b55c52', '#8b7aa8'];

async function getJSON(url) {
  const resp = await fetch(url);
  const result = await resp.json();
  if (result.code !== 0) throw new Error(result.message || '接口返回异常');
  return result.data;
}

const fmtMoney = (n) => '¥' + Number(n || 0).toLocaleString('zh-CN', { maximumFractionDigits: 0 });
const fmtInt = (n) => Number(n || 0).toLocaleString('zh-CN');

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

/* ---------- 总览卡片 ---------- */
async function initSummary() {
  const data = await getJSON('/api/dashboard/summary');
  setText('amountCard', fmtMoney(data.total_amount));
  setText('orderCard', fmtInt(data.order_count));
  setText('storeCard', fmtInt(data.store_count));
  setText('avgCard', '¥' + Number(data.avg_order_amount || 0).toFixed(2));
  setText('cupsCard', fmtInt(data.total_cups) + ' 杯');
}

/* ---------- 健康检查 ---------- */
async function initHealth() {
  const el = document.getElementById('dbStatus');
  try {
    const data = await getJSON('/api/health');
    el.textContent = '● 数据库已连接';
    el.className = 'status ok';
  } catch (err) {
    el.textContent = '● 数据库未连接：' + err.message;
    el.className = 'status bad';
  }
}

/* ---------- 销售趋势折线图 ---------- */
let trendChart;
async function renderTrend(days) {
  const list = await getJSON(`/api/dashboard/trend?days=${days}`);
  const dates = list.map((it) => it.order_date);
  const values = list.map((it) => Number(it.total_amount));
  trendChart.setOption({
    color: THEME,
    tooltip: { trigger: 'axis', valueFormatter: (v) => fmtMoney(v) },
    grid: { left: 60, right: 20, top: 30, bottom: 60 },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: { type: 'value', axisLabel: { formatter: (v) => '¥' + v } },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8 }],
    series: [{
      name: '销售额', type: 'line', smooth: true, showSymbol: false,
      data: values,
      lineStyle: { width: 2.5, color: THEME[0] },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(111,158,119,0.45)' },
            { offset: 1, color: 'rgba(111,158,119,0.02)' },
          ],
        },
      },
    }],
  }, true);
}

/* ---------- 城市销售分布 ---------- */
function initRegion() {
  const chart = echarts.init(document.getElementById('regionChart'));
  getJSON('/api/dashboard/region').then((list) => {
    chart.setOption({
      color: THEME,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => fmtMoney(v) },
      grid: { left: 55, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: list.map((it) => it.city) },
      yAxis: { type: 'value', axisLabel: { formatter: (v) => '¥' + v } },
      series: [{
        name: '销售额', type: 'bar', barWidth: '45%',
        data: list.map((it) => Number(it.total_amount)),
        itemStyle: { borderRadius: [6, 6, 0, 0], color: THEME[3] },
        label: { show: true, position: 'top', formatter: (p) => fmtMoney(p.value), color: '#c9d1d8', fontSize: 10 },
      }],
    });
  });
  return chart;
}

/* ---------- 横向柱状图通用渲染 ---------- */
function renderHorizontalBar(chart, list, nameKey, valueKey, formatter, color) {
  const names = list.map((it) => it[nameKey]).reverse();
  const values = list.map((it) => Number(it[valueKey])).reverse();
  chart.setOption({
    color: THEME,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: formatter },
    grid: { left: 90, right: 60, top: 16, bottom: 24 },
    xAxis: { type: 'value', axisLabel: { formatter: (v) => (v >= 10000 ? v / 10000 + '万' : v) } },
    yAxis: { type: 'category', data: names },
    series: [{
      name: nameKey, type: 'bar', barWidth: '55%', data: values,
      itemStyle: { borderRadius: [0, 5, 5, 0], color },
      label: { show: true, position: 'right', formatter: (p) => formatter(p.value), color: '#c9d1d8', fontSize: 10 },
    }],
  }, true);
}

/* ---------- 品类占比饼图 ---------- */
function initCategory() {
  const chart = echarts.init(document.getElementById('categoryChart'));
  getJSON('/api/dashboard/category').then((list) => {
    chart.setOption({
      color: THEME,
      tooltip: { trigger: 'item', formatter: (p) => `${p.name}<br>${fmtMoney(p.value)} (${p.percent}%)` },
      legend: { bottom: 0, textStyle: { color: '#98a2ab', fontSize: 11 } },
      series: [{
        name: '品类销售额', type: 'pie', radius: ['40%', '65%'], center: ['50%', '43%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#1d242b', borderWidth: 2 },
        label: { formatter: '{b}\n{d}%', color: '#c9d1d8', fontSize: 11 },
        data: list.map((it) => ({ name: it.category, value: Number(it.total_amount) })),
      }],
    });
  });
  return chart;
}

/* ---------- 24 小时订单分布 ---------- */
function initHourly() {
  const chart = echarts.init(document.getElementById('hourlyChart'));
  getJSON('/api/dashboard/hourly').then((list) => {
    const hours = list.map((it) => it.order_hour + ':00');
    const values = list.map((it) => Number(it.order_count));
    chart.setOption({
      color: THEME,
      tooltip: { trigger: 'axis', valueFormatter: (v) => fmtInt(v) + ' 单' },
      grid: { left: 55, right: 16, top: 20, bottom: 40 },
      xAxis: { type: 'category', data: hours, axisLabel: { interval: 3 } },
      yAxis: { type: 'value' },
      series: [{
        name: '订单数', type: 'bar', barWidth: '65%', data: values,
        itemStyle: { borderRadius: [4, 4, 0, 0], color: THEME[2] },
      }],
    });
  });
  return chart;
}

/* ---------- 工作日 vs 周末 ---------- */
function initDaytype() {
  const chart = echarts.init(document.getElementById('daytypeChart'));
  getJSON('/api/dashboard/daytype').then((list) => {
    chart.setOption({
      color: THEME,
      tooltip: { trigger: 'axis', valueFormatter: (v) => fmtMoney(v) },
      legend: { bottom: 0, textStyle: { color: '#98a2ab', fontSize: 11 } },
      grid: { left: 60, right: 16, top: 20, bottom: 50 },
      xAxis: { type: 'category', data: list.map((it) => it.day_type) },
      yAxis: [
        { type: 'value', name: '销售额', axisLabel: { formatter: (v) => '¥' + v } },
        { type: 'value', name: '客单价', axisLabel: { formatter: (v) => '¥' + v } },
      ],
      series: [
        {
          name: '销售额', type: 'bar', barWidth: '40%',
          data: list.map((it) => Number(it.total_amount)),
          itemStyle: { borderRadius: [5, 5, 0, 0], color: THEME[0] },
        },
        {
          name: '客单价', type: 'line', yAxisIndex: 1, smooth: true,
          data: list.map((it) => Number(it.avg_order_amount)),
          lineStyle: { color: THEME[1], width: 2.5 },
          itemStyle: { color: THEME[1] },
        },
      ],
    });
  });
  return chart;
}

/* ---------- 启动 ---------- */
window.addEventListener('DOMContentLoaded', () => {
  const charts = [];

  initSummary().catch(console.error);
  initHealth();

  trendChart = echarts.init(document.getElementById('trendChart'));
  charts.push(trendChart);
  charts.push(initRegion());

  const productChart = echarts.init(document.getElementById('productChart'));
  const storeChart = echarts.init(document.getElementById('storeChart'));
  charts.push(productChart, storeChart);
  getJSON('/api/dashboard/product_top?limit=10')
    .then((list) => renderHorizontalBar(productChart, list, 'product_name', 'total_quantity', (v) => fmtInt(v) + ' 杯', THEME[0]))
    .catch(console.error);
  getJSON('/api/dashboard/store_top?limit=10')
    .then((list) => renderHorizontalBar(storeChart, list, 'store_name', 'total_amount', (v) => fmtMoney(v), THEME[1]))
    .catch(console.error);

  charts.push(initCategory(), initHourly(), initDaytype());

  const daysSelect = document.getElementById('daysSelect');
  const trendSubtitle = document.getElementById('trendSubtitle');
  daysSelect.addEventListener('change', () => {
    const days = daysSelect.value;
    trendSubtitle.textContent = `近 ${days} 天`;
    renderTrend(days).catch(console.error);
  });
  renderTrend(daysSelect.value).catch(console.error);

  window.addEventListener('resize', () => charts.forEach((c) => c.resize()));
});

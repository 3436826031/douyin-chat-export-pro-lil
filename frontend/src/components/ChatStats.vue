<template>
  <div class="stats-overlay" @click.self="$emit('close')">
    <div class="stats-panel">
      <div class="stats-header">
        <h3>📊 聊天统计</h3>
        <span class="stats-conv-name">{{ conversation?.name }}</span>
        <button class="stats-close" @click="$emit('close')">×</button>
      </div>

      <div class="stats-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="stats-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="stats-content">
        <!-- 消息趋势折线图 -->
        <div v-if="activeTab === 'trend'" class="trend-view">
          <div class="trend-controls">
            <button
              v-for="p in periods"
              :key="p.key"
              class="period-btn"
              :class="{ active: period === p.key }"
              @click="period = p.key"
            >
              {{ p.label }}
            </button>
          </div>
          <div class="chart-container">
            <div class="chart-title">消息数量趋势</div>
            <div class="line-chart" ref="lineChartRef">
              <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none">
                <!-- 网格线 -->
                <line
                  v-for="i in 5"
                  :key="'grid-' + i"
                  :x1="padding"
                  :y1="padding + (chartHeight - 2 * padding) * (i - 1) / 4"
                  :x2="chartWidth - padding"
                  :y2="padding + (chartHeight - 2 * padding) * (i - 1) / 4"
                  class="grid-line"
                />
                <!-- Y轴标签 -->
                <text
                  v-for="i in 5"
                  :key="'label-' + i"
                  :x="padding - 8"
                  :y="padding + (chartHeight - 2 * padding) * (i - 1) / 4 + 4"
                  class="axis-label"
                  text-anchor="end"
                >
                  {{ Math.round(maxValue * (5 - i) / 4) }}
                </text>
                <!-- 数据线 -->
                <polyline
                  v-if="trendData.length > 1"
                  :points="trendLinePoints"
                  class="trend-line"
                />
                <!-- 数据点 -->
                <circle
                  v-for="(point, index) in trendPoints"
                  :key="'point-' + index"
                  :cx="point.x"
                  :cy="point.y"
                  r="4"
                  class="trend-point"
                  @mouseenter="showTooltip($event, point)"
                  @mouseleave="hideTooltip"
                />
              </svg>
              <!-- X轴标签 -->
              <div class="x-labels">
                <span
                  v-for="(label, index) in xLabels"
                  :key="'x-' + index"
                  :style="{ left: label.x + '%' }"
                >
                  {{ label.text }}
                </span>
              </div>
            </div>
            <div class="chart-summary">
              <div class="summary-item">
                <span class="summary-label">总计</span>
                <span class="summary-value">{{ totalMessages }} 条</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">日均</span>
                <span class="summary-value">{{ avgMessages }} 条</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">峰值</span>
                <span class="summary-value">{{ maxValue }} 条</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 发送者统计饼图 -->
        <div v-if="activeTab === 'sender'" class="sender-view">
          <div class="pie-container">
            <div class="chart-title">消息发送比例</div>
            <div class="pie-chart">
              <svg viewBox="0 0 200 200">
                <circle
                  v-for="(slice, index) in pieSlices"
                  :key="'slice-' + index"
                  cx="100"
                  cy="100"
                  r="80"
                  fill="none"
                  :stroke="slice.color"
                  stroke-width="40"
                  :stroke-dasharray="slice.dasharray"
                  :stroke-dashoffset="slice.dashoffset"
                  class="pie-slice"
                />
                <!-- 中心白圆 -->
                <circle cx="100" cy="100" r="55" fill="var(--bg-secondary)" />
                <!-- 中心文字 -->
                <text x="100" y="95" text-anchor="middle" class="pie-center-text">
                  {{ totalMessages }}
                </text>
                <text x="100" y="115" text-anchor="middle" class="pie-center-label">
                  总消息
                </text>
              </svg>
            </div>
            <div class="pie-legend">
              <div
                v-for="(sender, index) in senderStats"
                :key="sender.sender_uid"
                class="legend-item"
              >
                <span class="legend-color" :style="{ background: pieColors[index] }"></span>
                <span class="legend-name">{{ sender.nickname }}</span>
                <span class="legend-count">{{ sender.count }} 条</span>
                <span class="legend-percent">{{ ((sender.count / totalMessages) * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 消息类型统计 -->
        <div v-if="activeTab === 'type'" class="type-view">
          <div class="type-grid">
            <div v-for="item in mediaStats" :key="item.type" class="type-card">
              <div class="type-icon">{{ getTypeIcon(item.type) }}</div>
              <div class="type-name">{{ getTypeName(item.type) }}</div>
              <div class="type-count">{{ item.count }}</div>
              <div class="type-bar">
                <div
                  class="type-bar-fill"
                  :style="{ width: (item.count / maxTypeCount * 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 活跃时段统计 -->
        <div v-if="activeTab === 'hourly'" class="hourly-view">
          <div class="chart-title">24小时消息分布</div>
          <div class="hourly-chart">
            <div v-for="h in 24" :key="h - 1" class="hourly-bar-container">
              <div class="hourly-bar-wrapper">
                <div
                  class="hourly-bar"
                  :style="{ height: getHourlyHeight(h - 1) + '%' }"
                >
                  <span v-if="getHourlyCount(h - 1) > 0" class="hourly-count">
                    {{ getHourlyCount(h - 1) }}
                  </span>
                </div>
              </div>
              <span class="hourly-label">{{ h - 1 }}</span>
            </div>
          </div>
          <div class="hourly-summary">
            <div class="summary-item">
              <span class="summary-label">最活跃</span>
              <span class="summary-value">{{ peakHour }}:00</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">最安静</span>
              <span class="summary-value">{{ quietHour }}:00</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="stats-loading">加载中...</div>
    </div>

    <!-- Tooltip -->
    <div v-if="tooltip.show" class="tooltip" :style="{ left: tooltip.x, top: tooltip.y }">
      <div class="tooltip-date">{{ tooltip.date }}</div>
      <div class="tooltip-count">{{ tooltip.count }} 条消息</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  conversation: Object,
})

const emit = defineEmits(['close'])

const activeTab = ref('trend')
const loading = ref(false)
const period = ref('day')
const trendData = ref([])
const senderStats = ref([])
const mediaStats = ref([])
const hourlyStats = ref([])

const chartWidth = 800
const chartHeight = 300
const padding = 50

const tabs = [
  { key: 'trend', label: '📈 消息趋势' },
  { key: 'sender', label: '👥 发送统计' },
  { key: 'type', label: '📊 消息类型' },
  { key: 'hourly', label: '🕐 活跃时段' },
]

const periods = [
  { key: 'day', label: '按天' },
  { key: 'month', label: '按月' },
  { key: 'year', label: '按年' },
]

const pieColors = [
  '#6366f1',
  '#ec4899',
  '#14b8a6',
  '#f59e0b',
  '#8b5cf6',
  '#06b6d4',
]

// Tooltip
const tooltip = ref({ show: false, x: '0px', y: '0px', date: '', count: 0 })

function showTooltip(event, point) {
  tooltip.value = {
    show: true,
    x: (event.clientX + 10) + 'px',
    y: (event.clientY - 40) + 'px',
    date: point.label,
    count: point.value,
  }
}

function hideTooltip() {
  tooltip.value.show = false
}

// 计算统计数据
const totalMessages = computed(() => {
  if (activeTab.value === 'sender') {
    return senderStats.value.reduce((sum, s) => sum + s.count, 0)
  }
  return trendData.value.reduce((sum, d) => sum + d.count, 0)
})

const avgMessages = computed(() => {
  if (trendData.value.length === 0) return 0
  return Math.round(totalMessages.value / trendData.value.length)
})

const maxValue = computed(() => {
  if (trendData.value.length === 0) return 0
  return Math.max(...trendData.value.map(d => d.count))
})

const maxTypeCount = computed(() => {
  if (mediaStats.value.length === 0) return 0
  return Math.max(...mediaStats.value.map(d => d.count))
})

// 折线图计算
const trendPoints = computed(() => {
  if (trendData.value.length === 0) return []
  const data = trendData.value
  const xStep = (chartWidth - 2 * padding) / Math.max(data.length - 1, 1)
  const yRange = chartHeight - 2 * padding

  return data.map((d, i) => ({
    x: padding + i * xStep,
    y: padding + yRange - (d.count / Math.max(maxValue.value, 1)) * yRange,
    label: d.period,
    value: d.count,
  }))
})

const trendLinePoints = computed(() => {
  return trendPoints.value.map(p => `${p.x},${p.y}`).join(' ')
})

const xLabels = computed(() => {
  const data = trendData.value
  if (data.length === 0) return []
  const maxLabels = 10
  const step = Math.max(1, Math.floor(data.length / maxLabels))
  const labels = []

  for (let i = 0; i < data.length; i += step) {
    const x = (i / Math.max(data.length - 1, 1)) * 100
    let text = data[i].period
    if (period.value === 'day') {
      text = text.substring(5) // MM-DD
    } else if (period.value === 'month') {
      text = text.substring(2) // YY-MM
    }
    labels.push({ x, text })
  }
  return labels
})

// 饼图计算
const pieSlices = computed(() => {
  const total = totalMessages.value
  if (total === 0) return []

  const circumference = 2 * Math.PI * 80
  let accumulatedOffset = 0

  return senderStats.value.map((sender, index) => {
    const percentage = sender.count / total
    const dasharray = `${percentage * circumference} ${circumference}`
    const dashoffset = -accumulatedOffset
    accumulatedOffset += percentage * circumference

    return {
      color: pieColors[index % pieColors.length],
      dasharray,
      dashoffset,
    }
  })
})

// 小时统计
const peakHour = computed(() => {
  if (hourlyStats.value.length === 0) return 0
  return hourlyStats.value.reduce((max, h) => h.count > max.count ? h : max, hourlyStats.value[0]).hour
})

const quietHour = computed(() => {
  const allHours = Array.from({ length: 24 }, (_, i) => i)
  const statsMap = {}
  hourlyStats.value.forEach(h => { statsMap[h.hour] = h.count })
  const minHour = allHours.reduce((min, h) => (statsMap[h] || 0) < (statsMap[min] || 0) ? h : min, 0)
  return minHour
})

function getHourlyCount(hour) {
  const stat = hourlyStats.value.find(h => h.hour === hour)
  return stat ? stat.count : 0
}

function getHourlyHeight(hour) {
  const count = getHourlyCount(hour)
  const max = Math.max(...hourlyStats.value.map(h => h.count), 1)
  return (count / max) * 100
}

function getTypeIcon(type) {
  const icons = { text: '📝', emoji: '😊', image: '🖼️', video: '🎬', share: '🔗', system: '⚙️', other: '📎' }
  return icons[type] || '📎'
}

function getTypeName(type) {
  const names = { text: '文字', emoji: '表情', image: '图片', video: '视频', share: '分享', system: '系统', other: '其他' }
  return names[type] || '其他'
}

// 加载数据
async function loadTrend() {
  if (!props.conversation) return
  loading.value = true
  try {
    const res = await fetch(`/api/conversations/${props.conversation.conv_id}/stats/messages?period=${period.value}`)
    trendData.value = await res.json()
  } catch {}
  loading.value = false
}

async function loadSender() {
  if (!props.conversation) return
  loading.value = true
  try {
    const res = await fetch(`/api/conversations/${props.conversation.conv_id}/stats/senders`)
    senderStats.value = await res.json()
  } catch {}
  loading.value = false
}

async function loadMedia() {
  if (!props.conversation) return
  loading.value = true
  try {
    const res = await fetch(`/api/conversations/${props.conversation.conv_id}/stats/media`)
    mediaStats.value = await res.json()
  } catch {}
  loading.value = false
}

async function loadHourly() {
  if (!props.conversation) return
  loading.value = true
  try {
    const res = await fetch(`/api/conversations/${props.conversation.conv_id}/stats/hourly`)
    hourlyStats.value = await res.json()
  } catch {}
  loading.value = false
}

// 切换标签
watch(activeTab, (tab) => {
  if (tab === 'trend') loadTrend()
  else if (tab === 'sender') loadSender()
  else if (tab === 'type') loadMedia()
  else if (tab === 'hourly') loadHourly()
})

// 切换周期
watch(period, () => loadTrend())

// 切换会话
watch(() => props.conversation, () => {
  if (props.conversation) {
    trendData.value = []
    senderStats.value = []
    mediaStats.value = []
    hourlyStats.value = []
    if (activeTab.value === 'trend') loadTrend()
    else if (activeTab.value === 'sender') loadSender()
    else if (activeTab.value === 'type') loadMedia()
    else if (activeTab.value === 'hourly') loadHourly()
  }
}, { immediate: true })
</script>

<style scoped>
.stats-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.stats-panel {
  width: 90vw;
  max-width: 900px;
  height: 80vh;
  background: var(--bg-secondary);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.stats-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.stats-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.stats-conv-name {
  font-size: 13px;
  color: var(--text-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-close:hover {
  background: var(--border-color);
}

.stats-tabs {
  display: flex;
  padding: 12px 20px;
  gap: 8px;
  border-bottom: 1px solid var(--border-color);
}

.stats-tab {
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.stats-tab:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.stats-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.stats-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.chart-container {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

/* 折线图 */
.trend-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.period-btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.period-btn:hover {
  border-color: var(--accent);
}

.period-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.line-chart {
  position: relative;
  height: 250px;
  margin-bottom: 30px;
}

.line-chart svg {
  width: 100%;
  height: 100%;
}

.grid-line {
  stroke: var(--border-color);
  stroke-width: 1;
  stroke-dasharray: 4 4;
}

.axis-label {
  fill: var(--text-muted);
  font-size: 10px;
}

.trend-line {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2;
  stroke-linejoin: round;
}

.trend-point {
  fill: var(--accent);
  cursor: pointer;
  transition: r 0.15s;
}

.trend-point:hover {
  r: 6;
}

.x-labels {
  position: absolute;
  bottom: -25px;
  left: 0;
  right: 0;
  height: 20px;
}

.x-labels span {
  position: absolute;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--text-muted);
}

.chart-summary {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.summary-item {
  text-align: center;
}

.summary-label {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
}

/* 饼图 */
.sender-view {
  display: flex;
  justify-content: center;
}

.pie-container {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid var(--border-color);
  width: 100%;
  max-width: 500px;
}

.pie-chart {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.pie-chart svg {
  width: 200px;
  height: 200px;
}

.pie-slice {
  transition: stroke-width 0.2s;
}

.pie-slice:hover {
  stroke-width: 44;
}

.pie-center-text {
  fill: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
}

.pie-center-label {
  fill: var(--text-muted);
  font-size: 12px;
}

.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  background: var(--bg-secondary);
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  font-size: 13px;
}

.legend-count {
  font-size: 13px;
  color: var(--text-muted);
}

.legend-percent {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  min-width: 50px;
  text-align: right;
}

/* 消息类型 */
.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.type-card {
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
  text-align: center;
}

.type-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.type-name {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.type-count {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.type-bar {
  height: 4px;
  background: var(--bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.type-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 小时分布 */
.hourly-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 200px;
  padding: 0 8px;
  margin-bottom: 16px;
}

.hourly-bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.hourly-bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.hourly-bar {
  width: 80%;
  max-width: 20px;
  background: var(--accent);
  border-radius: 4px 4px 0 0;
  position: relative;
  min-height: 2px;
  transition: height 0.3s ease;
}

.hourly-count {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
}

.hourly-label {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
}

.hourly-summary {
  display: flex;
  justify-content: center;
  gap: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.stats-loading {
  text-align: center;
  color: var(--text-muted);
  padding: 12px;
  font-size: 13px;
  border-top: 1px solid var(--border-color);
}

/* Tooltip */
.tooltip {
  position: fixed;
  z-index: 9999;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}

.tooltip-date {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.tooltip-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent);
}

@media (max-width: 768px) {
  .stats-overlay {
    background: #fff;
  }

  .stats-panel {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
    max-width: none;
    max-height: none;
  }

  .stats-header {
    padding: 12px 16px;
  }

  .stats-tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding: 8px 12px;
  }

  .stats-tab {
    flex-shrink: 0;
    padding: 6px 12px;
    font-size: 12px;
  }

  .stats-content {
    padding: 12px;
  }

  .chart-container {
    padding: 12px;
  }

  .line-chart {
    height: 180px;
  }

  .chart-summary {
    gap: 16px;
    margin-top: 12px;
  }

  .summary-value {
    font-size: 16px;
  }

  .pie-container {
    padding: 16px;
  }

  .pie-chart svg {
    width: 150px;
    height: 150px;
  }

  .pie-center-text {
    font-size: 20px;
  }

  .legend-item {
    padding: 6px;
    gap: 6px;
  }

  .legend-name {
    font-size: 12px;
  }

  .legend-count,
  .legend-percent {
    font-size: 12px;
  }

  .type-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .type-card {
    padding: 12px;
  }

  .type-icon {
    font-size: 24px;
  }

  .type-count {
    font-size: 20px;
  }

  .hourly-chart {
    height: 150px;
  }

  .hourly-summary {
    gap: 16px;
  }
}
</style>

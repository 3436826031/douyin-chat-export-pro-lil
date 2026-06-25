<template>
  <div class="explorer-overlay" @click.self="$emit('close')">
    <div class="explorer-panel">
      <div class="explorer-header">
        <h3>聊天记录</h3>
        <span class="explorer-conv-name">{{ conversation?.name }}</span>
        <button class="explorer-close" @click="$emit('close')">×</button>
      </div>

      <div class="explorer-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="explorer-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <div class="explorer-content">
        <!-- 按日期查看 -->
        <div v-if="activeTab === 'date'" class="date-view">
          <div class="date-sidebar">
            <!-- 日历组件 -->
            <div class="calendar">
              <div class="calendar-header">
                <button class="cal-nav" @click="prevMonth">‹</button>
                <span class="cal-title">{{ calendarTitle }}</span>
                <button class="cal-nav" @click="nextMonth">›</button>
              </div>
              <div class="calendar-weekdays">
                <span v-for="w in weekdays" :key="w">{{ w }}</span>
              </div>
              <div class="calendar-days">
                <button
                  v-for="day in calendarDays"
                  :key="day.date"
                  class="cal-day"
                  :class="{
                    'other-month': !day.currentMonth,
                    'has-messages': day.hasMessages,
                    'selected': selectedDate === day.date,
                    'is-today': day.isToday
                  }"
                  @click="day.currentMonth && day.hasMessages && selectDate(day.date)"
                  :disabled="!day.currentMonth || !day.hasMessages"
                >
                  {{ day.day }}
                </button>
              </div>
            </div>
            <!-- 日期列表 -->
            <div class="date-list">
              <div class="date-list-title">有消息的日期</div>
              <div
                v-for="d in dates"
                :key="d.date"
                class="date-item"
                :class="{ active: selectedDate === d.date }"
                @click="selectDate(d.date)"
              >
                <span class="date-text">{{ formatDate(d.date) }}</span>
                <span class="date-count">{{ d.count }} 条</span>
              </div>
              <div v-if="dates.length === 0 && !loading" class="empty-hint">暂无数据</div>
            </div>
          </div>
          <div class="date-messages">
            <div v-if="selectedDate" class="date-messages-header">
              {{ formatDate(selectedDate) }} 的消息
            </div>
            <div class="messages-scroll">
              <div v-for="msg in dateMessages" :key="msg.msg_id" class="explorer-msg">
                <div class="msg-info">
                  <span class="msg-sender">{{ getSenderName(msg) }}</span>
                  <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
                </div>
                <div class="msg-content">
                  <template v-if="msg.msg_type === 3 && isImage(msg)">
                    <img :src="getImageSrc(msg)" class="msg-thumb" @click="openLightbox(getImageSrc(msg))" />
                  </template>
                  <template v-else-if="msg.msg_type === 3 && isVideo(msg)">
                    <div class="video-thumb" @click="playVideo(msg)">
                      <span class="play-icon">▶</span>
                      <span>视频</span>
                    </div>
                  </template>
                  <template v-else-if="isVoice(msg)">
                    <audio controls :src="getVoiceUrl(msg)" preload="none"></audio>
                  </template>
                  <template v-else-if="msg.msg_type === 4 || isJsonShare(msg)">
                    <div class="share-link" @click="openShare(msg)">
                      <span class="share-icon">🔗</span>
                      <span>{{ getShareTitle(msg) || '分享链接' }}</span>
                    </div>
                  </template>
                  <template v-else>
                    <span>{{ msg.content }}</span>
                  </template>
                </div>
              </div>
              <div v-if="dateMessages.length === 0 && !loading" class="empty-hint">
                {{ selectedDate ? '该日期暂无消息' : '请选择日期' }}
              </div>
            </div>
          </div>
        </div>

        <!-- 图片查看 -->
        <div v-if="activeTab === 'image'" class="media-grid">
          <div v-for="msg in mediaMessages" :key="msg.msg_id" class="media-item" @click="openLightbox(getImageSrc(msg))">
            <img :src="getImageSrc(msg)" loading="lazy" @error="onImgError" />
            <div class="media-overlay">
              <span>{{ formatTime(msg.timestamp) }}</span>
            </div>
          </div>
          <div v-if="mediaMessages.length === 0 && !loading" class="empty-hint">暂无图片</div>
        </div>

        <!-- 视频查看 -->
        <div v-if="activeTab === 'video'" class="media-grid">
          <div v-for="msg in mediaMessages" :key="msg.msg_id" class="media-item video-item" @click="playVideo(msg)">
            <video :src="'/media/' + msg.media_local_path" preload="metadata"></video>
            <div class="media-overlay">
              <span class="play-icon">▶</span>
              <span>{{ formatTime(msg.timestamp) }}</span>
            </div>
          </div>
          <div v-if="mediaMessages.length === 0 && !loading" class="empty-hint">暂无视频</div>
        </div>

        <!-- 语音查看 -->
        <div v-if="activeTab === 'voice'" class="voice-list">
          <div v-for="msg in mediaMessages" :key="msg.msg_id" class="voice-item">
            <div class="voice-info">
              <span class="voice-sender">{{ getSenderName(msg) }}</span>
              <span class="voice-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <audio controls :src="getVoiceUrl(msg)" preload="none"></audio>
          </div>
          <div v-if="mediaMessages.length === 0 && !loading" class="empty-hint">暂无语音</div>
        </div>

        <!-- 分享查看 -->
        <div v-if="activeTab === 'share'" class="share-list">
          <div v-for="msg in mediaMessages" :key="msg.msg_id" class="share-item" @click="openShare(msg)">
            <div class="share-info">
              <span class="share-sender">{{ getSenderName(msg) }}</span>
              <span class="share-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="share-content">
              <img v-if="getShareCover(msg)" :src="getShareCover(msg)" class="share-cover" @error="onImgError" />
              <div class="share-text">
                <div class="share-title">{{ getShareTitle(msg) || '[分享]' }}</div>
                <div v-if="getShareAuthor(msg)" class="share-author">@ {{ getShareAuthor(msg) }}</div>
              </div>
            </div>
          </div>
          <div v-if="mediaMessages.length === 0 && !loading" class="empty-hint">暂无分享</div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-hint">加载中...</div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <button :disabled="currentPage <= 1" @click="changePage(currentPage - 1)">上一页</button>
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <button :disabled="currentPage >= totalPages" @click="changePage(currentPage + 1)">下一页</button>
        </div>
      </div>
    </div>

    <!-- Lightbox -->
    <div v-if="lightboxSrc" class="lightbox-overlay" @click.self="closeLightbox">
      <img class="lightbox-img" :src="lightboxSrc" />
      <button class="lightbox-close" @click="closeLightbox">×</button>
    </div>

    <!-- Video Player -->
    <div v-if="videoSrc" class="video-overlay" @click.self="closeVideo">
      <video class="video-player" :src="videoSrc" controls autoplay></video>
      <button class="video-close" @click="closeVideo">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  conversation: Object,
})

const emit = defineEmits(['close', 'navigate'])

const activeTab = ref('date')
const loading = ref(false)
const dates = ref([])
const selectedDate = ref('')
const dateMessages = ref([])
const mediaMessages = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const lightboxSrc = ref(null)
const videoSrc = ref(null)
const userCache = ref({})

const tabs = [
  { key: 'date', label: '日期', icon: '📅' },
  { key: 'image', label: '图片', icon: '🖼️' },
  { key: 'video', label: '视频', icon: '🎬' },
  { key: 'voice', label: '语音', icon: '🎤' },
  { key: 'share', label: '分享', icon: '🔗' },
]

// 日历相关
const currentMonth = ref(new Date().getMonth())
const currentYear = ref(new Date().getFullYear())
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const calendarTitle = computed(() => {
  return `${currentYear.value}年${currentMonth.value + 1}月`
})

// 有消息的日期集合（用于快速查找）
const dateSet = computed(() => {
  return new Set(dates.value.map(d => d.date))
})

const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]

  const days = []

  // 上个月的日期（填充到第一行）
  const startWeekday = firstDay.getDay()
  const prevMonthLastDay = new Date(year, month, 0).getDate()
  for (let i = startWeekday - 1; i >= 0; i--) {
    const d = prevMonthLastDay - i
    const date = new Date(year, month - 1, d)
    const dateStr = date.toISOString().split('T')[0]
    days.push({
      day: d,
      date: dateStr,
      currentMonth: false,
      hasMessages: dateSet.value.has(dateStr),
      isToday: dateStr === todayStr,
    })
  }

  // 本月的日期
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const date = new Date(year, month, d)
    const dateStr = date.toISOString().split('T')[0]
    days.push({
      day: d,
      date: dateStr,
      currentMonth: true,
      hasMessages: dateSet.value.has(dateStr),
      isToday: dateStr === todayStr,
    })
  }

  // 下个月的日期（填充到最后一行）
  const remaining = 42 - days.length
  for (let d = 1; d <= remaining; d++) {
    const date = new Date(year, month + 1, d)
    const dateStr = date.toISOString().split('T')[0]
    days.push({
      day: d,
      date: dateStr,
      currentMonth: false,
      hasMessages: dateSet.value.has(dateStr),
      isToday: dateStr === todayStr,
    })
  }

  return days
})

function prevMonth() {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

// 加载用户信息
async function loadUserInfo(uid) {
  if (!uid || userCache.value[uid]) return
  try {
    const res = await fetch(`/api/users/${uid}`)
    if (res.ok) {
      const data = await res.json()
      userCache.value[uid] = data
    }
  } catch {}
}

function getSenderName(msg) {
  if (userCache.value[msg.sender_uid]?.nickname) {
    return userCache.value[msg.sender_uid].nickname
  }
  if (msg.sender_name && msg.sender_name !== '__self__') return msg.sender_name
  return '未知用户'
}

// 加载日期列表
async function loadDates() {
  if (!props.conversation) return
  loading.value = true
  try {
    const res = await fetch(`/api/conversations/${props.conversation.conv_id}/dates`)
    dates.value = await res.json()
  } catch {}
  loading.value = false
}

// 选择日期
async function selectDate(date) {
  selectedDate.value = date
  currentPage.value = 1
  await loadDateMessages()
}

// 加载指定日期的消息
async function loadDateMessages() {
  if (!props.conversation || !selectedDate.value) return
  loading.value = true
  try {
    const res = await fetch(
      `/api/conversations/${props.conversation.conv_id}/messages/by-date?date=${selectedDate.value}&page=${currentPage.value}&page_size=100`
    )
    const data = await res.json()
    dateMessages.value = data.items
    totalPages.value = Math.ceil(data.total / 100)
    // 加载用户信息
    for (const msg of data.items) {
      if (msg.sender_uid) loadUserInfo(msg.sender_uid)
    }
  } catch {}
  loading.value = false
}

// 加载媒体消息
async function loadMediaMessages() {
  if (!props.conversation) return
  loading.value = true
  const type = activeTab.value === 'share' ? 'share' : activeTab.value
  try {
    const res = await fetch(
      `/api/conversations/${props.conversation.conv_id}/media?type=${type}&page=${currentPage.value}&page_size=50`
    )
    const data = await res.json()
    mediaMessages.value = data.items
    totalPages.value = Math.ceil(data.total / 50)
    // 加载用户信息
    for (const msg of data.items) {
      if (msg.sender_uid) loadUserInfo(msg.sender_uid)
    }
  } catch {}
  loading.value = false
}

// 切换标签
watch(activeTab, (tab) => {
  currentPage.value = 1
  if (tab === 'date') {
    loadDates()
  } else {
    loadMediaMessages()
  }
})

// 切换会话
watch(() => props.conversation, () => {
  if (props.conversation) {
    dates.value = []
    selectedDate.value = ''
    dateMessages.value = []
    mediaMessages.value = []
    currentPage.value = 1
    if (activeTab.value === 'date') {
      loadDates()
    } else {
      loadMediaMessages()
    }
  }
}, { immediate: true })

// 切换页码
function changePage(page) {
  currentPage.value = page
  if (activeTab.value === 'date') {
    loadDateMessages()
  } else {
    loadMediaMessages()
  }
}

// 工具函数
function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = d.toDateString() === yesterday.toDateString()

  if (isToday) return '今天'
  if (isYesterday) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function isImage(msg) {
  if (!msg.media_local_path) return msg.msg_type === 2
  return /\.(jpg|jpeg|png|webp|gif)$/i.test(msg.media_local_path)
}

function isVideo(msg) {
  return msg.media_local_path && /\.mp4$/i.test(msg.media_local_path)
}

function isVoice(msg) {
  if (msg.content?.includes('resource_url')) return true
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    return !!raw?.content_json?.resource_url?.url_list?.length
  } catch {}
  return false
}

function isJsonShare(msg) {
  if (!msg.content || !msg.content.startsWith('{')) return false
  return msg.content.includes('content_title') || msg.content.includes('cover_url')
}

function getImageSrc(msg) {
  if (msg.media_local_path && !isVideo(msg)) return '/media/' + msg.media_local_path
  // 尝试从 raw_data 获取 inline_pic
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    if (raw?.content_json?.inline_pic) {
      return 'data:image/webp;base64,' + raw.content_json.inline_pic.replace(/\r?\n/g, '')
    }
  } catch {}
  return ''
}

function getVoiceUrl(msg) {
  if (msg.media_local_path) return '/media/' + msg.media_local_path
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    const cj = raw?.content_json
    if (cj?.resource_url?.url_list?.length) return cj.resource_url.url_list[0]
  } catch {}
  return ''
}

function getShareTitle(msg) {
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    const cj = raw?.content_json || tryParseJson(msg.content)
    return cj?.content_title || cj?.aweme_title || ''
  } catch {}
  return ''
}

function getShareAuthor(msg) {
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    const cj = raw?.content_json || tryParseJson(msg.content)
    return cj?.content_name || ''
  } catch {}
  return ''
}

function getShareCover(msg) {
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    const cj = raw?.content_json || tryParseJson(msg.content)
    return cj?.cover_url?.url_list?.[0] || ''
  } catch {}
  return ''
}

function tryParseJson(str) {
  if (!str || !str.startsWith('{')) return null
  try { return JSON.parse(str) } catch { return null }
}

function openShare(msg) {
  const title = getShareTitle(msg)
  let itemId = ''
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    const cj = raw?.content_json || tryParseJson(msg.content)
    itemId = cj?.itemId || cj?.related_share_video?.itemId || ''
  } catch {}
  if (itemId) {
    window.open(`https://www.douyin.com/video/${itemId}`, '_blank')
  }
}

function openLightbox(src) {
  if (src) lightboxSrc.value = src
}

function closeLightbox() {
  lightboxSrc.value = null
}

function playVideo(msg) {
  if (msg.media_local_path) {
    videoSrc.value = '/media/' + msg.media_local_path
  }
}

function closeVideo() {
  videoSrc.value = null
}

function onImgError(e) {
  e.target.style.display = 'none'
}
</script>

<style scoped>
.explorer-overlay {
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

.explorer-panel {
  width: 90vw;
  max-width: 1000px;
  height: 80vh;
  background: var(--bg-secondary);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.explorer-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.explorer-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.explorer-conv-name {
  font-size: 13px;
  color: var(--text-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.explorer-close {
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

.explorer-close:hover {
  background: var(--border-color);
}

.explorer-tabs {
  display: flex;
  padding: 12px 20px;
  gap: 8px;
  border-bottom: 1px solid var(--border-color);
}

.explorer-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.explorer-tab:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.explorer-tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.tab-icon {
  font-size: 14px;
}

.explorer-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 日期视图 */
.date-view {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.date-sidebar {
  width: 280px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 日历组件 */
.calendar {
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.cal-nav {
  width: 28px;
  height: 28px;
  border: none;
  background: var(--bg-tertiary);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cal-nav:hover {
  background: var(--border-color);
}

.cal-title {
  font-size: 14px;
  font-weight: 600;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 4px;
}

.calendar-weekdays span {
  text-align: center;
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 0;
}

.calendar-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.cal-day {
  width: 100%;
  aspect-ratio: 1;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 12px;
  cursor: default;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cal-day.other-month {
  color: var(--text-muted);
  opacity: 0.4;
}

.cal-day.has-messages {
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.cal-day.has-messages:hover {
  opacity: 0.85;
}

.cal-day.selected {
  box-shadow: 0 0 0 2px var(--accent-hover, #4a9eff);
}

.cal-day.is-today:not(.has-messages) {
  border: 1px solid var(--accent);
}

.date-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.date-list-title {
  font-size: 12px;
  color: var(--text-muted);
  padding: 8px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 4px;
}

.date-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.date-item:hover {
  background: var(--bg-tertiary);
}

.date-item.active {
  background: var(--accent);
  color: #fff;
}

.date-text {
  font-size: 13px;
}

.date-count {
  font-size: 11px;
  opacity: 0.7;
}

.date-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.date-messages-header {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}

.messages-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.explorer-msg {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
}

.explorer-msg:last-child {
  border-bottom: none;
}

.msg-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.msg-sender {
  font-size: 12px;
  color: var(--accent);
  font-weight: 600;
}

.msg-time {
  font-size: 11px;
  color: var(--text-muted);
}

.msg-content {
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.msg-thumb {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
}

.video-thumb {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
}

.video-thumb:hover {
  background: var(--border-color);
}

.play-icon {
  font-size: 16px;
}

.share-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  cursor: pointer;
  color: var(--accent);
}

.share-link:hover {
  background: var(--border-color);
}

/* 媒体网格 */
.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.media-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.media-item img,
.media-item video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.media-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  color: #fff;
  font-size: 11px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.video-item .play-icon {
  font-size: 24px;
}

/* 语音列表 */
.voice-list {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.voice-item {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 8px;
}

.voice-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.voice-sender {
  font-size: 13px;
  color: var(--accent);
  font-weight: 600;
}

.voice-time {
  font-size: 11px;
  color: var(--text-muted);
}

.voice-item audio {
  width: 100%;
  height: 36px;
}

/* 分享列表 */
.share-list {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.share-item {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.share-item:hover {
  border-color: var(--accent);
}

.share-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.share-sender {
  font-size: 13px;
  color: var(--accent);
  font-weight: 600;
}

.share-time {
  font-size: 11px;
  color: var(--text-muted);
}

.share-content {
  display: flex;
  gap: 12px;
}

.share-cover {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
}

.share-text {
  flex: 1;
  min-width: 0;
}

.share-title {
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.share-author {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 空状态 */
.empty-hint {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 20px;
  font-size: 14px;
}

.loading-hint {
  text-align: center;
  color: var(--text-muted);
  padding: 20px;
  font-size: 13px;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.pagination button {
  padding: 6px 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  font-size: 13px;
  color: var(--text-muted);
}

/* Lightbox */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
}

/* Video Player */
.video-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-player {
  max-width: 90vw;
  max-height: 90vh;
}

.video-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 24px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .explorer-panel {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .date-view {
    flex-direction: column;
  }

  .date-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    max-height: 350px;
  }

  .date-list {
    width: 100%;
    max-height: 120px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    overflow-x: auto;
    padding: 8px;
    gap: 8px;
  }

  .date-item {
    flex-shrink: 0;
    padding: 8px 16px;
  }

  .media-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}
</style>

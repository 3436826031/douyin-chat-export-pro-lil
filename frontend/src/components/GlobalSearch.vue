<template>
  <div class="global-search-overlay" @click.self="$emit('close')">
    <div class="global-search-panel">
      <div class="gs-header">
        <h3>全局搜索</h3>
        <div class="gs-input-wrap">
          <svg class="gs-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input
            ref="inputRef"
            v-model="query"
            placeholder="搜索所有聊天记录..."
            @input="onInput"
            @keydown.escape="$emit('close')"
            autofocus
          />
          <span v-if="query" class="gs-clear" @click="clear">×</span>
        </div>
        <button class="gs-close" @click="$emit('close')">×</button>
      </div>

      <div class="gs-body">
        <!-- 左侧：会话列表 -->
        <div class="gs-sidebar">
          <div class="gs-sidebar-header">
            <span>相关会话 ({{ groupedResults.length }})</span>
          </div>
          <div class="gs-conv-list">
            <div
              v-for="group in groupedResults"
              :key="group.conv_id"
              class="gs-conv-item"
              :class="{ active: selectedConvId === group.conv_id }"
              @click="selectConv(group)"
            >
              <div class="gs-conv-avatar">
                <span>{{ (group.conv_name || '?')[0] }}</span>
              </div>
              <div class="gs-conv-info">
                <div class="gs-conv-name">{{ group.conv_name || '未知会话' }}</div>
                <div class="gs-conv-preview">{{ group.lastMatch }}</div>
              </div>
              <div class="gs-conv-count">{{ group.count }}</div>
            </div>
            <div v-if="groupedResults.length === 0 && !loading && query" class="gs-empty">
              无匹配结果
            </div>
            <div v-if="!query" class="gs-empty">
              输入关键词搜索所有聊天记录
            </div>
          </div>
        </div>

        <!-- 右侧：消息列表 -->
        <div class="gs-content">
          <div v-if="selectedConvId" class="gs-content-header">
            <span class="gs-content-conv">{{ selectedConvName }}</span>
            <span class="gs-content-count">找到 {{ selectedGroup?.count || 0 }} 条</span>
          </div>
          <div class="gs-messages" ref="messagesRef">
            <div
              v-for="msg in selectedMessages"
              :key="msg.msg_id"
              class="gs-msg"
              :class="{ 'gs-msg-self': isSelf(msg) }"
              @click="jumpTo(msg)"
            >
              <div class="gs-msg-sender">{{ getSenderName(msg) }}</div>
              <div class="gs-msg-content" v-html="highlight(msg.content)"></div>
              <div class="gs-msg-time">{{ formatTime(msg.timestamp) }}</div>
            </div>
            <div v-if="selectedMessages.length === 0 && selectedConvId && !loading" class="gs-empty">
              该会话无匹配消息
            </div>
            <div v-if="!selectedConvId && query" class="gs-empty">
              选择左侧会话查看匹配消息
            </div>
          </div>
          <!-- 加载更多 -->
          <div v-if="selectedHasMore" class="gs-load-more">
            <button @click="loadMoreSelected" :disabled="loading">
              {{ loading ? '加载中...' : '加载更多' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="gs-loading">搜索中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'

const emit = defineEmits(['close', 'navigate'])

const query = ref('')
const results = ref([])
const loading = ref(false)
const selectedConvId = ref('')
const selectedConvName = ref('')
const selectedMessages = ref([])
const selectedHasMore = ref(false)
const selectedPage = ref(1)
const selfUid = ref(localStorage.getItem('selfUid') || '')
const inputRef = ref(null)
const messagesRef = ref(null)

let debounceTimer = null

// 按会话分组
const groupedResults = computed(() => {
  const groups = {}
  for (const msg of results.value) {
    if (!groups[msg.conv_id]) {
      groups[msg.conv_id] = {
        conv_id: msg.conv_id,
        conv_name: msg.conv_name,
        count: 0,
        lastMatch: '',
        messages: [],
      }
    }
    groups[msg.conv_id].count++
    groups[msg.conv_id].lastMatch = msg.content?.substring(0, 50) || ''
    groups[msg.conv_id].messages.push(msg)
  }
  return Object.values(groups).sort((a, b) => b.count - a.count)
})

const selectedGroup = computed(() => {
  return groupedResults.value.find(g => g.conv_id === selectedConvId.value)
})

function onInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => search(query.value), 400)
}

async function search(q) {
  if (!q || q.length < 1) {
    results.value = []
    selectedConvId.value = ''
    selectedMessages.value = []
    return
  }
  loading.value = true
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&page_size=200`)
    const data = await res.json()
    results.value = data.items
    // 自动选中第一个会话
    if (groupedResults.value.length > 0 && !selectedConvId.value) {
      selectConv(groupedResults.value[0])
    }
  } catch {}
  loading.value = false
}

async function selectConv(group) {
  selectedConvId.value = group.conv_id
  selectedConvName.value = group.conv_name || '未知会话'
  selectedPage.value = 1
  // 从已有结果中筛选该会话的消息
  selectedMessages.value = group.messages
  selectedHasMore.value = group.count > group.messages.length
  await nextTick()
  if (messagesRef.value) messagesRef.value.scrollTop = 0
}

async function loadMoreSelected() {
  if (!query.value || !selectedConvId.value) return
  selectedPage.value++
  loading.value = true
  try {
    const res = await fetch(
      `/api/search?q=${encodeURIComponent(query.value)}&page=${selectedPage.value}&page_size=50`
    )
    const data = await res.json()
    // 筛选出当前会话的消息
    const newMsgs = data.items.filter(m => m.conv_id === selectedConvId.value)
    selectedMessages.value.push(...newMsgs)
    selectedHasMore.value = newMsgs.length > 0 && data.items.length === 50
  } catch {}
  loading.value = false
}

function clear() {
  query.value = ''
  results.value = []
  selectedConvId.value = ''
  selectedMessages.value = []
}

function isSelf(msg) {
  return selfUid.value && msg.sender_uid === selfUid.value
}

function getSenderName(msg) {
  return msg.sender_display_name || msg.sender_name || '未知'
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts * 1000).toLocaleDateString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function highlight(text) {
  if (!text || !query.value) return escapeHtml(text || '')
  const safe = escapeHtml(text)
  const escaped = query.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return safe.replace(
    new RegExp(`(${escaped})`, 'gi'),
    '<mark>$1</mark>'
  )
}

function jumpTo(msg) {
  emit('navigate', msg)
  emit('close')
}

onMounted(() => {
  inputRef.value?.focus()
})
</script>

<style scoped>
.global-search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.global-search-panel {
  width: 92vw;
  max-width: 1100px;
  height: 80vh;
  background: var(--bg-secondary);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.gs-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
}

.gs-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
}

.gs-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 12px;
}

.gs-input-wrap:focus-within {
  border-color: var(--accent);
}

.gs-icon {
  width: 18px;
  height: 18px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.gs-input-wrap input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
}

.gs-clear {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 18px;
  padding: 0 4px;
}

.gs-clear:hover {
  color: var(--text-primary);
}

.gs-close {
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

.gs-close:hover {
  background: var(--border-color);
}

.gs-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.gs-sidebar {
  width: 300px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.gs-sidebar-header {
  padding: 12px 16px;
  font-size: 13px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.gs-conv-list {
  flex: 1;
  overflow-y: auto;
}

.gs-conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.15s;
}

.gs-conv-item:hover {
  background: var(--bg-tertiary);
}

.gs-conv-item.active {
  background: var(--bg-tertiary);
  border-left: 3px solid var(--accent);
}

.gs-conv-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  flex-shrink: 0;
}

.gs-conv-info {
  flex: 1;
  min-width: 0;
}

.gs-conv-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gs-conv-preview {
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gs-conv-count {
  background: var(--accent);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.gs-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.gs-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.gs-content-conv {
  font-size: 14px;
  font-weight: 600;
}

.gs-content-count {
  font-size: 12px;
  color: var(--text-muted);
}

.gs-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.gs-msg {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.15s;
}

.gs-msg:hover {
  background: var(--bg-tertiary);
}

.gs-msg:last-child {
  border-bottom: none;
}

.gs-msg-sender {
  font-size: 12px;
  color: var(--accent);
  font-weight: 600;
  margin-bottom: 4px;
}

.gs-msg-self .gs-msg-sender {
  color: var(--text-muted);
}

.gs-msg-content {
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.gs-msg-content :deep(mark) {
  background: var(--highlight, #ffd700);
  color: #000;
  padding: 0 2px;
  border-radius: 2px;
}

.gs-msg-time {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.gs-msg-self {
  text-align: right;
}

.gs-load-more {
  padding: 12px;
  text-align: center;
  border-top: 1px solid var(--border-color);
}

.gs-load-more button {
  padding: 6px 20px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
}

.gs-load-more button:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.gs-load-more button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.gs-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 20px;
  font-size: 14px;
}

.gs-loading {
  text-align: center;
  color: var(--text-muted);
  padding: 12px;
  font-size: 13px;
  border-top: 1px solid var(--border-color);
}

@media (max-width: 768px) {
  .global-search-panel {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .gs-body {
    flex-direction: column;
  }

  .gs-sidebar {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }

  .gs-conv-list {
    display: flex;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 8px;
    gap: 8px;
  }

  .gs-conv-item {
    flex-shrink: 0;
    width: 160px;
    flex-direction: column;
    align-items: flex-start;
    border-bottom: none;
    border: 1px solid var(--border-color);
    border-radius: 8px;
  }

  .gs-conv-item.active {
    border-left: 1px solid var(--accent);
  }
}
</style>

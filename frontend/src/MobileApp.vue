<template>
  <div class="mobile-app">
    <!-- 顶部导航 -->
    <div class="mobile-header">
      <h1>消息</h1>
      <div class="header-actions">
        <button class="header-btn" @click="showSearch = !showSearch">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 搜索框 -->
    <div v-if="showSearch" class="mobile-search">
      <div class="search-input-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <input
          v-model="searchQuery"
          placeholder="搜索联系人"
          @input="onSearch"
          ref="searchInput"
        />
        <span v-if="searchQuery" class="search-clear" @click="clearSearch">×</span>
      </div>
    </div>

    <!-- 会话列表 -->
    <div class="mobile-conv-list" ref="listRef">
      <div
        v-for="conv in filteredConversations"
        :key="conv.conv_id"
        class="mobile-conv-item"
        @click="openChat(conv)"
      >
        <div class="conv-avatar">
          <img v-if="getAvatar(conv)" :src="getAvatar(conv)" @error="e => e.target.style.display='none'" />
          <span v-else>{{ (conv.name || '?')[0] }}</span>
        </div>
        <div class="conv-content">
          <div class="conv-top">
            <span class="conv-name">{{ conv.name || '未命名' }}</span>
            <span class="conv-time">{{ formatTime(conv.last_message_time) }}</span>
          </div>
          <div class="conv-bottom">
            <span class="conv-preview">{{ getPreview(conv) }}</span>
          </div>
        </div>
      </div>
      <div v-if="filteredConversations.length === 0" class="mobile-empty">
        {{ searchQuery ? '无匹配结果' : '暂无会话' }}
      </div>
    </div>

    <!-- 聊天页面 -->
    <div v-if="activeChat" class="mobile-chat">
      <div class="chat-header">
        <button class="chat-back" @click="activeChat = null">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
        </button>
        <h2>{{ activeChat.name || '未命名' }}</h2>
        <div class="chat-header-actions">
          <button class="chat-action-btn" @click="showChatExplorer = true">📋</button>
          <button class="chat-action-btn" @click="showChatStats = true">📊</button>
        </div>
      </div>

      <div class="chat-messages" ref="chatMessagesRef" @scroll="onChatScroll">
        <div v-if="chatLoading" class="chat-loading">加载中...</div>
        <div v-if="hasMore && !chatLoading" class="chat-load-more" @click="loadMoreMessages">
          加载更早消息
        </div>
        <div
          v-for="msg in messages"
          :key="msg.msg_id"
          class="chat-msg"
          :class="{ 'chat-msg-self': isSelf(msg) }"
        >
          <div class="msg-bubble">
            <!-- 图片 -->
            <img
              v-if="msg.msg_type === 3 && isImage(msg)"
              :src="getImageSrc(msg)"
              class="msg-image"
              @click="openLightbox(getImageSrc(msg))"
            />
            <!-- 视频 -->
            <video
              v-else-if="msg.msg_type === 3 && isVideo(msg)"
              :src="'/media/' + msg.media_local_path"
              controls
              class="msg-video"
            />
            <!-- 表情 -->
            <img
              v-else-if="msg.msg_type === 2 && getEmojiSrc(msg)"
              :src="getEmojiSrc(msg)"
              class="msg-emoji"
            />
            <!-- 语音 -->
            <div v-else-if="isVoice(msg)" class="msg-voice">
              <audio controls :src="getVoiceUrl(msg)" preload="none"></audio>
            </div>
            <!-- 分享 -->
            <div v-else-if="msg.msg_type === 4 || isJsonShare(msg)" class="msg-share" @click="openShare(msg)">
              <div class="share-title">{{ getShareTitle(msg) || '[分享]' }}</div>
              <div v-if="getShareAuthor(msg)" class="share-author">@ {{ getShareAuthor(msg) }}</div>
            </div>
            <!-- 文字 -->
            <span v-else>{{ msg.content }}</span>
          </div>
          <div class="msg-time">{{ formatMsgTime(msg.timestamp) }}</div>
        </div>
      </div>
    </div>

    <!-- Lightbox -->
    <div v-if="lightboxSrc" class="mobile-lightbox" @click="lightboxSrc = null">
      <img :src="lightboxSrc" />
    </div>

    <!-- 聊天记录查看器 -->
    <ChatExplorer
      v-if="showChatExplorer && activeChat"
      :conversation="activeChat"
      @close="showChatExplorer = false"
    />

    <!-- 统计 -->
    <ChatStats
      v-if="showChatStats && activeChat"
      :conversation="activeChat"
      @close="showChatStats = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import ChatExplorer from './components/ChatExplorer.vue'
import ChatStats from './components/ChatStats.vue'

const conversations = ref([])
const activeChat = ref(null)
const messages = ref([])
const total = ref(0)
const chatLoading = ref(false)
const hasMore = ref(false)
const showSearch = ref(false)
const searchQuery = ref('')
const searchInput = ref(null)
const listRef = ref(null)
const chatMessagesRef = ref(null)
const lightboxSrc = ref(null)
const showChatExplorer = ref(false)
const showChatStats = ref(false)
const selfUid = ref(localStorage.getItem('selfUid') || '')
const userCache = ref({})

// 加载会话列表
async function loadConversations() {
  try {
    const res = await fetch('/api/conversations?page_size=200')
    const data = await res.json()
    conversations.value = data.items
  } catch {}
}

// 过滤会话
const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value
  const q = searchQuery.value.toLowerCase()
  return conversations.value.filter(c => (c.name || '').toLowerCase().includes(q))
})

function onSearch() {}
function clearSearch() {
  searchQuery.value = ''
}

// 打开聊天
async function openChat(conv) {
  activeChat.value = conv
  messages.value = []
  await loadMessages(conv.conv_id)
}

// 加载消息
async function loadMessages(convId, beforeSeq = null) {
  chatLoading.value = true
  let url = `/api/conversations/${convId}/messages?page_size=50`
  if (beforeSeq !== null) url += `&before_seq=${beforeSeq}`

  try {
    const res = await fetch(url)
    const data = await res.json()

    if (beforeSeq === null) {
      messages.value = data.items
      await nextTick()
      scrollToBottom()
    } else {
      const list = chatMessagesRef.value
      const prevHeight = list ? list.scrollHeight : 0
      messages.value = [...data.items, ...messages.value]
      await nextTick()
      if (list) list.scrollTop = list.scrollHeight - prevHeight
    }

    total.value = data.total
    hasMore.value = messages.value.length < data.total

    // 加载用户信息
    for (const msg of data.items) {
      if (msg.sender_uid) loadUserInfo(msg.sender_uid)
    }
  } catch {}
  chatLoading.value = false
}

async function loadMoreMessages() {
  if (!activeChat.value || messages.value.length === 0) return
  const minSeq = Math.min(...messages.value.map(m => m.seq))
  await loadMessages(activeChat.value.conv_id, minSeq)
}

function scrollToBottom() {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

function onChatScroll() {
  const list = chatMessagesRef.value
  if (!list || chatLoading.value || !hasMore.value) return
  if (list.scrollTop < 50) {
    loadMoreMessages()
  }
}

// 用户信息
async function loadUserInfo(uid) {
  if (!uid || userCache.value[uid]) return
  try {
    const res = await fetch(`/api/users/${uid}`)
    if (res.ok) {
      userCache.value[uid] = await res.json()
    }
  } catch {}
}

function isSelf(msg) {
  return selfUid.value && msg.sender_uid === selfUid.value
}

function getAvatar(conv) {
  if (conv.avatar_url) {
    if (conv.avatar_url.startsWith('avatars/')) return `/media/${conv.avatar_url}`
    if (conv.avatar_url.startsWith('http')) return conv.avatar_url
  }
  return null
}

function getPreview(conv) {
  // 简单预览
  return ''
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = d.toDateString() === yesterday.toDateString()

  if (isToday) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  if (isYesterday) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function formatMsgTime(ts) {
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
  return ''
}

function getEmojiSrc(msg) {
  if (msg.media_local_path) return '/media/' + msg.media_local_path
  return msg.media_url || null
}

function getVoiceUrl(msg) {
  if (msg.media_local_path) return '/media/' + msg.media_local_path
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    return raw?.content_json?.resource_url?.url_list?.[0] || ''
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

function tryParseJson(str) {
  if (!str || !str.startsWith('{')) return null
  try { return JSON.parse(str) } catch { return null }
}

function openShare(msg) {
  let itemId = ''
  try {
    const raw = typeof msg.raw_data === 'string' ? JSON.parse(msg.raw_data) : msg.raw_data
    const cj = raw?.content_json || tryParseJson(msg.content)
    itemId = cj?.itemId || cj?.related_share_video?.itemId || ''
  } catch {}
  if (itemId) window.open(`https://www.douyin.com/video/${itemId}`, '_blank')
}

function openLightbox(src) {
  if (src) lightboxSrc.value = src
}

// 初始化
onMounted(() => {
  loadConversations()
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.mobile-app {
  height: 100vh;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 顶部导航 */
.mobile-header {
  background: #fff;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 10;
}

.mobile-header h1 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  cursor: pointer;
}

/* 搜索框 */
.mobile-search {
  background: #fff;
  padding: 8px 16px 12px;
}

.search-input-wrap {
  display: flex;
  align-items: center;
  background: #f5f5f5;
  border-radius: 20px;
  padding: 8px 12px;
  gap: 8px;
}

.search-input-wrap svg {
  color: #999;
  flex-shrink: 0;
}

.search-input-wrap input {
  flex: 1;
  border: none;
  background: none;
  font-size: 14px;
  outline: none;
  color: #333;
}

.search-clear {
  color: #999;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
}

/* 会话列表 */
.mobile-conv-list {
  flex: 1;
  overflow-y: auto;
  background: #fff;
}

.mobile-conv-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.15s;
}

.mobile-conv-item:active {
  background: #f5f5f5;
}

.conv-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.conv-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.conv-avatar span {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.conv-content {
  flex: 1;
  min-width: 0;
}

.conv-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.conv-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: 12px;
  color: #999;
  flex-shrink: 0;
  margin-left: 8px;
}

.conv-bottom {
  display: flex;
  align-items: center;
}

.conv-preview {
  font-size: 13px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-empty {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-size: 14px;
}

/* 聊天页面 */
.mobile-chat {
  position: fixed;
  inset: 0;
  background: #f5f5f5;
  z-index: 100;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.chat-header {
  background: #fff;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #e8e8e8;
}

.chat-back {
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  cursor: pointer;
}

.chat-header h2 {
  flex: 1;
  font-size: 17px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-header-actions {
  display: flex;
  gap: 4px;
}

.chat-action-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 聊天消息 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.chat-loading,
.chat-load-more {
  text-align: center;
  color: #999;
  padding: 12px;
  font-size: 13px;
}

.chat-load-more {
  color: #667eea;
  cursor: pointer;
}

.chat-msg {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  max-width: 75%;
}

.chat-msg-self {
  align-self: flex-end;
}

.msg-bubble {
  background: #fff;
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 15px;
  line-height: 1.5;
  word-break: break-word;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.chat-msg-self .msg-bubble {
  background: #667eea;
  color: #fff;
}

.msg-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 12px;
  cursor: pointer;
}

.msg-video {
  max-width: 240px;
  max-height: 240px;
  border-radius: 12px;
}

.msg-emoji {
  max-width: 120px;
  max-height: 120px;
}

.msg-voice audio {
  height: 36px;
  max-width: 200px;
}

.msg-share {
  background: #f0f0f0;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  border-left: 3px solid #667eea;
}

.chat-msg-self .msg-share {
  background: rgba(255, 255, 255, 0.2);
  border-left-color: #fff;
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
  opacity: 0.7;
  margin-top: 4px;
}

.msg-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  padding: 0 4px;
}

.chat-msg-self .msg-time {
  text-align: right;
}

/* Lightbox */
.mobile-lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mobile-lightbox img {
  max-width: 95vw;
  max-height: 95vh;
  object-fit: contain;
}

/* 适配暗色主题 */
@media (prefers-color-scheme: dark) {
  .mobile-app {
    background: #1a1a1a;
  }

  .mobile-header,
  .chat-header {
    background: #2a2a2a;
    border-color: #3a3a3a;
  }

  .mobile-header h1,
  .chat-header h2,
  .conv-name {
    color: #fff;
  }

  .mobile-conv-list {
    background: #1a1a1a;
  }

  .mobile-conv-item {
    border-color: #2a2a2a;
  }

  .mobile-conv-item:active {
    background: #2a2a2a;
  }

  .mobile-search {
    background: #2a2a2a;
  }

  .search-input-wrap {
    background: #3a3a3a;
  }

  .search-input-wrap input {
    color: #fff;
  }

  .chat-messages {
    background: #1a1a1a;
  }

  .msg-bubble {
    background: #2a2a2a;
    color: #fff;
  }

  .chat-msg-self .msg-bubble {
    background: #667eea;
  }
}
</style>

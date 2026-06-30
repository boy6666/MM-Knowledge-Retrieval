<template>
  <Layout>
    <div class="chat-container">
      <div class="chat-header">
        <h2>AI 助手对话</h2>
        <button class="new-chat-btn" @click="startNewChat">新对话</button>
      </div>
      
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="!conversationId" class="welcome-message">
          <div class="welcome-icon">🤖</div>
          <h3>欢迎使用设备检修助手</h3>
          <p>您可以通过文字、图片、语音或视频与AI助手进行对话</p>
          <button class="start-btn" @click="startNewChat">开始对话</button>
        </div>
        
        <div v-for="(msg, index) in messages" :key="index" class="message-item" :class="msg.role">
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-text" v-html="markdownToHtml(msg.content)"></div>
            <div v-if="msg.media_type === 'image' && msg.media_url" class="message-media">
              <img :src="getImageUrl(msg.media_url)" alt="图片" />
            </div>
            <div v-if="msg.media_type === 'audio'" class="message-media">
              <span class="audio-tag">🎤 语音消息</span>
            </div>
            <div v-if="msg.media_type === 'video'" class="message-media">
              <span class="video-tag">📹 视频消息</span>
            </div>
            <div v-if="msg.role === 'assistant' && msg.media_type === 'text' && !msg.is_media" class="message-actions">
              <button class="add-guidance-btn" @click="addToGuidance(msg)">生成检修方案</button>
            </div>
          </div>
        </div>
        
        <div v-if="loading" class="loading-message">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
          <span>AI正在思考...</span>
        </div>
      </div>
      
      <div v-if="conversationId" class="chat-input-area">
        <div class="chat-toolbar">
          <button class="tool-btn" @click="triggerImageUpload" title="上传图片">
            🖼️
          </button>
          <button class="tool-btn" @click="triggerVideoUpload" title="上传视频">
            📹
          </button>
          <button 
            class="tool-btn" 
            :class="{ recording: isRecording }"
            @click="toggleRecording"
            :title="speechSupported ? '点击语音输入' : '浏览器不支持语音识别'"
            :disabled="!speechSupported"
          >
            {{ isRecording ? '🎙️' : '🎤' }}
          </button>
          <input 
            ref="imageInput" 
            type="file" 
            accept="image/*" 
            class="hidden-input"
            @change="handleImageUpload"
          />
          <input 
            ref="videoInput" 
            type="file" 
            accept="video/*" 
            class="hidden-input"
            @change="handleVideoUpload"
          />
        </div>
        
        <div class="chat-input-wrapper">
          <input 
            v-model="inputMessage" 
            type="text" 
            placeholder="输入消息..."
            class="chat-input"
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" @click="sendMessage" :disabled="!inputMessage && !pendingFiles.length">
            发送
          </button>
        </div>
        
        <div v-if="pendingFiles.length > 0" class="pending-files">
          <span>待发送文件: {{ pendingFiles.length }}</span>
          <button class="cancel-btn" @click="clearPendingFiles">取消</button>
        </div>
        
        <div v-if="isRecording" class="recording-indicator">
          <div class="recording-dot"></div>
          <span>正在录音... 松开结束</span>
        </div>
      </div>
      
      <div v-if="showImageModal" class="modal-overlay" @click="showImageModal = false">
        <div class="image-modal-content" @click.stop>
          <img :src="previewImageUrl" alt="预览" />
          <button class="modal-close" @click="showImageModal = false">×</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus"
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'
import { markdownToHtml } from '../utils/format'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const conversationId = ref('')
const messages = ref<any[]>([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

const isRecording = ref(false)
const recognition = ref<any>(null)
const speechSupported = ref(false)

const pendingFiles = ref<{ type: string; file: File }[]>([])
const imageInput = ref<HTMLInputElement | null>(null)
const videoInput = ref<HTMLInputElement | null>(null)
const showImageModal = ref(false)
const previewImageUrl = ref('')

const getImageUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const startNewChat = async () => {
  try {
    const response = await api.chat.new()
    conversationId.value = response.conversation_id
    messages.value = []
    inputMessage.value = ''
    pendingFiles.value = []
  } catch (error) {
    console.error('创建对话失败:', error)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value && pendingFiles.value.length === 0) return
  
  loading.value = true
  
  const formData = new FormData()
  if (inputMessage.value) {
    formData.append('message', inputMessage.value)
  }
  
  for (const pf of pendingFiles.value) {
    formData.append(pf.type, pf.file)
  }
  
  messages.value.push({
    role: 'user',
    content: inputMessage.value || '[文件]',
    media_type: pendingFiles.value.length > 0 ? pendingFiles.value[0].type : 'text',
    media_url: ''
  })
  
  inputMessage.value = ''
  pendingFiles.value = []
  
  await scrollToBottom()
  
  try {
    const response = await api.chat.chat(conversationId.value, formData)
    messages.value.push({
      role: 'assistant',
      content: response.response,
      media_type: 'text',
      media_url: '',
      is_media: false,
      _message_id: response.message_id,
      _conversation_id: conversationId.value
    })
    
    if (response.related_images && response.related_images.length > 0) {
      response.related_images.forEach((img: any) => {
        messages.value.push({
          role: 'assistant',
          content: img.title,
          media_type: 'image',
          media_url: img.image_url,
          is_media: true
        })
      })
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: '发送失败，请稍后重试',
      media_type: 'text',
      media_url: ''
    })
    console.error('发送消息失败:', error)
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const triggerImageUpload = () => {
  imageInput.value?.click()
}

const triggerVideoUpload = () => {
  videoInput.value?.click()
}

const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      previewImageUrl.value = e.target?.result as string
      showImageModal.value = true
    }
    reader.readAsDataURL(file)
    pendingFiles.value.push({ type: 'image', file })
  }
}

const handleVideoUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    pendingFiles.value.push({ type: 'video', file })
  }
}

const clearPendingFiles = () => {
  pendingFiles.value = []
  if (imageInput.value) imageInput.value.value = ''
  if (videoInput.value) videoInput.value.value = ''
}

const initSpeechRecognition = () => {
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (!SpeechRecognition) {
    speechSupported.value = false
    return
  }
  speechSupported.value = true
  
  const rec = new SpeechRecognition()
  rec.lang = 'zh-CN'
  rec.interimResults = false
  rec.continuous = false
  rec.maxAlternatives = 1

  rec.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript
    inputMessage.value = transcript
    isRecording.value = false
  }

  rec.onerror = (event: any) => {
    console.error('语音识别错误:', event.error)
    isRecording.value = false
    if (event.error === 'not-allowed') {
      ElMessage('请允许麦克风权限以使用语音输入')
    }
  }

  rec.onend = () => {
    isRecording.value = false
  }

  recognition.value = rec
}

const toggleRecording = () => {
  if (!recognition.value) return
  
  if (isRecording.value) {
    recognition.value.stop()
    isRecording.value = false
  } else {
    try {
      recognition.value.start()
      isRecording.value = true
    } catch (e) {
      console.error('启动语音识别失败:', e)
    }
  }
}

const addToGuidance = async (msg: any) => {
  try {
    const title = msg.content.substring(0, 30) + (msg.content.length > 30 ? '...' : '')
    
    const saveResponse = await api.guidance.generateFromChat({
      conversation_id: msg._conversation_id || conversationId.value,
      message_id: msg._message_id,
      title: title,
      user_id: userStore.userInfo?.id
    })
    
    if (saveResponse && (saveResponse.id || saveResponse.guidance_id)) {
      router.push(`/guidance/${saveResponse.id || saveResponse.guidance_id}`)
    } else {
      ElMessage('保存失败')
    }
  } catch (error: any) {
    console.error('生成失败:', error)
    ElMessage(error.response?.data?.detail || error.message || '生成失败，请检查后端服务')
  }
}

onMounted(() => {
  startNewChat()
  initSpeechRecognition()
})

onUnmounted(() => {
  if (recognition.value) {
    recognition.value.stop()
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}

.new-chat-btn {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #fafafa;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-message h3 {
  font-size: 24px;
  color: #1e293b;
  margin-bottom: 12px;
}

.welcome-message p {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 24px;
}

.start-btn {
  padding: 10px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: #2563eb;
  color: white;
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.message-text :deep(h1) {
  font-size: 18px;
  font-weight: bold;
  margin: 12px 0 8px;
  color: inherit;
}

.message-text :deep(h2) {
  font-size: 16px;
  font-weight: bold;
  margin: 10px 0 6px;
  color: inherit;
}

.message-text :deep(h3) {
  font-size: 15px;
  font-weight: bold;
  margin: 8px 0 4px;
  color: inherit;
}

.message-text :deep(p) {
  margin: 6px 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin: 3px 0;
}

.message-text :deep(strong) {
  font-weight: bold;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 13px;
}

.message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.05);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
}

.message-text :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.message-text :deep(hr) {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin: 10px 0;
}

.message-item.user .message-text {
  background: #2563eb;
  color: white;
  border-radius: 12px 12px 0 12px;
}

.message-item.user .message-text :deep(a) {
  color: #bfdbfe;
}

.message-item.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.message-item.user .message-text :deep(pre) {
  background: rgba(255, 255, 255, 0.1);
}

.message-item.assistant .message-text {
  background: white;
  color: #1e293b;
  border: 1px solid #e2e8f0;
  border-radius: 12px 12px 12px 0;
}

.message-media {
  margin-top: 8px;
}

.message-media img {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.audio-tag, .video-tag {
  display: inline-block;
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 12px;
  color: #64748b;
}

.message-actions {
  margin-top: 8px;
}

.add-guidance-btn {
  padding: 4px 12px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.add-guidance-btn:hover {
  background: #1d4ed8;
}

.loading-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  color: #64748b;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  background: white;
}

.chat-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tool-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #f1f5f9;
}

.tool-btn.recording {
  background: #ef4444;
  border-color: #ef4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.hidden-input {
  display: none;
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
}

.chat-input {
  flex: 1;
  height: 42px;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.chat-input:focus {
  outline: none;
  border-color: #2563eb;
}

.send-btn {
  height: 42px;
  padding: 0 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.send-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.pending-files {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 6px 12px;
  background: #fef3c7;
  border-radius: 4px;
  font-size: 12px;
  color: #d97706;
}

.cancel-btn {
  background: none;
  border: none;
  color: #d97706;
  cursor: pointer;
  text-decoration: underline;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef2f2;
  border-radius: 4px;
  font-size: 13px;
  color: #dc2626;
}

.recording-dot {
  width: 8px;
  height: 8px;
  background: #dc2626;
  border-radius: 50%;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.image-modal-content {
  position: relative;
  max-width: 80vw;
  max-height: 80vh;
}

.image-modal-content img {
  max-width: 100%;
  max-height: 80vh;
  border-radius: 8px;
}

.modal-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 32px;
  height: 32px;
  background: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
}
</style>

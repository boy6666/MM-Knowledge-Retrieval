<template>
  <Layout>
    <div class="search-container">
      <div class="search-header">
        <div class="search-box-wrapper">
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="输入关键词搜索维修知识..."
              class="search-input"
              @keyup.enter="handleSearch"
            />
            <button 
              class="mic-btn" 
              :class="{ recording: isRecording }"
              @click="toggleVoiceInput"
              :title="speechSupported ? '点击语音输入' : '浏览器不支持语音识别'"
              :disabled="!speechSupported"
            >
              {{ isRecording ? '🎙️' : '🎤' }}
            </button>
            <button class="search-btn" @click="handleSearch">搜索</button>
            <button class="ai-btn" @click="goToAi">AI助手</button>
          </div>
        </div>
      </div>
      
      <div v-if="searchSuggestion" class="suggestion-section">
        <div class="suggestion-header">
          <span class="suggestion-icon">💡</span>
          <span class="suggestion-text">{{ searchSuggestion.suggestion_text }}</span>
        </div>
        <div class="suggestion-chapters">
          <button 
            v-for="(chapter, idx) in searchSuggestion.sub_chapters" 
            :key="idx"
            class="chapter-btn"
            @click="selectChapter(chapter)"
          >
            {{ chapter }}
          </button>
        </div>
      </div>
      
      <div v-if="searchResults.length > 0" class="results-section">
        <div class="results-header">
          <div class="results-tabs">
            <button 
              class="tab-btn active"
            >
              检索结果 ({{ docResults.length }})
            </button>
          </div>
        </div>
        
        <div class="results-list">
          <div class="sub-tabs">
            <button 
              class="sub-tab-btn" 
              :class="{ active: docSubTab === 'text' }"
              @click="docSubTab = 'text'"
            >
              文本结果 ({{ textResults.length }})
            </button>
            <button 
              class="sub-tab-btn" 
              :class="{ active: docSubTab === 'image' }"
              @click="docSubTab = 'image'"
            >
              图片结果 ({{ imageResults.length }})
            </button>
          </div>
          
          <div class="results-list-inner" :class="{ 'image-grid': docSubTab === 'image' }">
          <div 
            v-for="(result, index) in displayResults" 
            :key="index" 
            class="result-card"
            :class="{ 'image-card': result.type === 'image' }"
          >
            <div v-if="result.type === 'image'" class="image-result">
              <div class="result-image-wrapper" @click="showImagePreview(result)">
                <img 
                  :src="getImageUrl(result.image_url)" 
                  :alt="result.title"
                  class="result-image"
                />
                <div class="image-overlay">
                  <span>点击查看大图</span>
                </div>
              </div>
              <div class="result-header">
                <div class="result-title">
                  <span class="type-badge image-badge">图片</span>
                  {{ result.title || '维修手册插图' }}
                </div>
                <div class="result-relevance">相关度：{{ result.similarity || 0 }}%</div>
              </div>
              <div class="result-content" v-html="markdownToHtml(result.description || result.content)"></div>
              <div class="result-meta">
                <span v-if="result.source_type === 'manual'">维修手册 · 第{{ result.page }}页</span>
                <span v-else-if="result.source_type === 'case'">故障案例</span>
              </div>
              <div class="result-actions">
                <button class="action-btn" @click="showImagePreview(result)">查看大图</button>
                <button class="action-btn" :disabled="addingToGuidance" @click="addToGuidance(result)">
                  {{ addingToGuidance ? '生成中...' : '生成检修方案' }}
                </button>
              </div>
            </div>
            
            <div v-else class="result-item text-result">
              <div class="result-header">
                <div class="result-title">
                  <span class="type-badge text-badge">文本</span>
                  {{ result.title || result.source_file || '知识库' }}
                </div>
                <div class="result-relevance">相关度：{{ result.similarity || 0 }}%</div>
              </div>
              
              <div v-if="result.chapter_tree && result.chapter_tree.length > 0" class="chapter-path">
                <span class="chapter-label">章节：</span>
                <span class="chapter-text">{{ result.chapter_tree.join(' / ') }}</span>
              </div>
              
              <div class="result-content" v-html="markdownToHtml(result.content)"></div>
              
              <div v-if="result.torque_list && result.torque_list.length > 0" class="param-section">
                <span class="param-label">🔧 扭矩参数：</span>
                <span class="param-value">{{ result.torque_list.join('、') }}</span>
              </div>
              <div v-if="result.gap_standard && result.gap_standard.length > 0" class="param-section">
                <span class="param-label">📏 间隙标准：</span>
                <span class="param-value">{{ result.gap_standard.join('、') }}</span>
              </div>
              
              <div v-if="result.strong_images && result.strong_images.length > 0" class="related-images">
                <div class="related-images-title strong">📌 强关联图片 ({{ result.strong_images.length }})</div>
                <div class="related-images-list">
                  <div 
                    v-for="(img, imgIdx) in result.strong_images.slice(0, 4)" 
                    :key="'strong-' + imgIdx"
                    class="related-image-item image-placeholder-mode"
                  >
                    <div class="image-placeholder">
                      <div class="placeholder-icon">🖼️</div>
                      <div class="placeholder-desc">{{ img.description || img.caption || img.img_type || '维修图片' }}</div>
                    </div>
                    <div class="related-image-caption">{{ img.caption || img.title }}</div>
                  </div>
                </div>
              </div>
              
              <div v-if="result.weak_images && result.weak_images.length > 0" class="related-images weak-images">
                <div class="related-images-title">📎 通用示意图 ({{ result.weak_images.length }})</div>
                <div class="related-images-list">
                  <div 
                    v-for="(img, imgIdx) in result.weak_images.slice(0, 3)" 
                    :key="'weak-' + imgIdx"
                    class="related-image-item image-placeholder-mode"
                  >
                    <div class="image-placeholder">
                      <div class="placeholder-icon">🖼️</div>
                      <div class="placeholder-desc">{{ img.description || img.caption || img.img_type || '示意图' }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="result-meta">
                <span v-if="result.source_type === 'manual'">维修手册 · 第{{ result.page_start || result.page }}页</span>
                <span v-else-if="result.source_type === 'case'">故障案例</span>
                <span v-else>{{ result.source_file }}</span>
              </div>
              <div class="result-actions">
                <button class="action-btn" @click="showDetail(result)">查看详情</button>
                <button class="action-btn" :disabled="addingToGuidance" @click="addToGuidance(result)">
                  {{ addingToGuidance ? '生成中...' : '生成检修方案' }}
                </button>
              </div>
            </div>
          </div>
          </div>
        </div>
      </div>
      
      <div v-if="!searchResults.length && !loading" class="empty-state">
        <div class="empty-icon">📚</div>
        <p>输入关键词搜索维修知识，或点击AI助手获取智能问答</p>
        <button class="empty-action-btn" @click="goToAi">进入AI助手</button>
      </div>
      
      <div v-if="loading" class="empty-state">
        <div class="loading-spinner"></div>
        <p>正在检索中...</p>
      </div>
      
      <div v-if="showDetailModal" class="modal-overlay" @click="showDetailModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>检索结果详情</h3>
            <button class="modal-close" @click="showDetailModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="detail-item">
              <label>标题：</label>
              <span>{{ selectedResult?.title || '知识库' }}</span>
            </div>
            <div class="detail-item">
              <label>类型：</label>
              <span>{{ selectedResult?.type === 'image' ? '图片' : '文本' }}</span>
            </div>
            <div v-if="selectedResult?.chapter_tree && selectedResult?.chapter_tree.length > 0" class="detail-item">
              <label>章节路径：</label>
              <span>{{ selectedResult.chapter_tree.join(' / ') }}</span>
            </div>
            <div class="detail-item">
              <label>来源：</label>
              <span>{{ selectedResult?.source_type === 'manual' ? '维修手册' : selectedResult?.source_type === 'case' ? '故障案例' : selectedResult?.source_file }}</span>
            </div>
            <div class="detail-item">
              <label>相关度：</label>
              <span>{{ selectedResult?.similarity || 0 }}%</span>
            </div>
            <div v-if="selectedResult?.torque_list && selectedResult?.torque_list.length > 0" class="detail-item">
              <label>扭矩参数：</label>
              <span>{{ selectedResult.torque_list.join('、') }}</span>
            </div>
            <div v-if="selectedResult?.gap_standard && selectedResult?.gap_standard.length > 0" class="detail-item">
              <label>间隙标准：</label>
              <span>{{ selectedResult.gap_standard.join('、') }}</span>
            </div>
            <div class="detail-item">
              <label>内容：</label>
              <div class="detail-content" v-html="markdownToHtml(selectedResult?.content || selectedResult?.description)"></div>
            </div>
            
            <div v-if="selectedResult?.strong_images && selectedResult?.strong_images.length > 0" class="detail-item">
              <label>强关联图片：</label>
              <div class="detail-images">
                <div 
                  v-for="(img, idx) in selectedResult.strong_images" 
                  :key="'detail-strong-' + idx"
                  class="detail-image-item image-placeholder-mode"
                >
                  <div class="image-placeholder">
                    <div class="placeholder-icon">🖼️</div>
                    <div class="placeholder-desc">{{ img.description || img.caption || img.img_type || '维修图片' }}</div>
                  </div>
                  <div class="detail-image-caption">{{ img.caption || img.title }}</div>
                </div>
              </div>
            </div>
            
            <div v-if="selectedResult?.weak_images && selectedResult?.weak_images.length > 0" class="detail-item">
              <label>通用示意图：</label>
              <div class="detail-images">
                <div 
                  v-for="(img, idx) in selectedResult.weak_images" 
                  :key="'detail-weak-' + idx"
                  class="detail-image-item image-placeholder-mode"
                >
                  <div class="image-placeholder">
                    <div class="placeholder-icon">🖼️</div>
                    <div class="placeholder-desc">{{ img.description || img.caption || img.img_type || '示意图' }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="modal-btn" :disabled="addingToGuidance" @click="addToGuidance(selectedResult)">
              {{ addingToGuidance ? '生成中...' : '生成检修方案' }}
            </button>
            <button class="modal-btn secondary" @click="showDetailModal = false">关闭</button>
          </div>
        </div>
      </div>
      
      <div v-if="showImageModal" class="modal-overlay image-modal-overlay" @click="showImageModal = false">
        <div class="image-modal-content" @click.stop>
          <div class="image-modal-header">
            <h3>{{ previewImage?.title || '图片预览' }}</h3>
            <button class="modal-close" @click="showImageModal = false">×</button>
          </div>
          <div class="image-modal-body">
            <img 
              v-if="previewImage?.image_url"
              :src="getImageUrl(previewImage.image_url)" 
              :alt="previewImage?.title"
              class="preview-large-image"
            />
            <div v-else class="image-placeholder-large">
              <div class="placeholder-icon">🖼️</div>
              <div class="placeholder-desc">{{ previewImage?.description || previewImage?.caption || '暂无图片' }}</div>
            </div>
          </div>
          <div class="image-modal-footer">
            <div v-if="previewImage?.description" class="image-desc">{{ previewImage.description }}</div>
            <div v-if="previewImage?.page" class="image-page">第{{ previewImage.page }}页</div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus"
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'
import { markdownToHtml } from '../utils/format'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const searchQuery = ref('')
const searchResults = ref<any[]>([])
const showDetailModal = ref(false)
const showImageModal = ref(false)
const selectedResult = ref<any>(null)
const previewImage = ref<any>(null)
const addingToGuidance = ref(false)
const loading = ref(false)
const docSubTab = ref('text')
const searchSuggestion = ref<any>(null)

const isRecording = ref(false)
const recognition = ref<any>(null)
const speechSupported = ref(false)

const textResults = computed(() => {
  return searchResults.value.filter(r => r.type !== 'image')
})

const imageResults = computed(() => {
  return searchResults.value.filter(r => r.type === 'image')
})

const docResults = computed(() => {
  return searchResults.value
})

const displayResults = computed(() => {
  if (docSubTab.value === 'image') {
    return imageResults.value
  }
  return textResults.value
})

const getImageUrl = (url: string | undefined) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return url
}

const goToAi = () => {
  if (searchQuery.value) {
    router.push({ path: '/chat', query: { q: searchQuery.value } })
  } else {
    router.push('/chat')
  }
}

const handleSearch = async () => {
  if (!searchQuery.value) {
    ElMessage('请输入查询内容')
    return
  }
  
  loading.value = true
  
  try {
    const searchResponse = await api.search.text(searchQuery.value)
    searchResults.value = searchResponse.results || []
    searchSuggestion.value = searchResponse.suggestion || null
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage('搜索失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const showDetail = (result: any) => {
  selectedResult.value = result
  showDetailModal.value = true
}

const showImagePreview = (image: any) => {
  previewImage.value = image
  showImageModal.value = true
}

const addToGuidance = async (result: any) => {
  if (addingToGuidance.value) return
  addingToGuidance.value = true
  
  try {
    const deviceType = result.source_file?.includes('摩托车') || result.source_type === 'manual' ? '摩托车发动机' : '通用设备'
    const faultType = result.title || searchQuery.value || '检修任务'
    
    let content = ''
    if (result.chapter_tree && result.chapter_tree.length > 0) {
      content += `# ${result.chapter_tree.join(' / ')}\n\n`
    }
    if (result.content) {
      content += `${result.content}\n\n`
    }
    if (result.torque_list && result.torque_list.length > 0) {
      content += `### 🔧 扭矩参数\n${result.torque_list.join('、')}\n\n`
    }
    if (result.gap_standard && result.gap_standard.length > 0) {
      content += `### 📏 间隙标准\n${result.gap_standard.join('、')}\n\n`
    }
    if (result.strong_images && result.strong_images.length > 0) {
      content += `### 📌 关联图片\n`
      result.strong_images.forEach((img: any) => {
        content += `- ${img.caption || img.title}\n`
      })
    }
    
    const saveResponse = await api.guidance.save({
      title: `${deviceType} - ${faultType}`,
      device_type: deviceType,
      fault_type: faultType,
      content: content || result.content || '',
      source_type: 'search_generated',
      user_id: userStore.userInfo?.id
    })
    
    if (saveResponse && (saveResponse.id || saveResponse.guidance_id)) {
      router.push(`/guidance/${saveResponse.id || saveResponse.guidance_id}`)
    } else {
      ElMessage('保存失败')
    }
  } catch (error: any) {
    console.error('生成失败:', error)
    ElMessage(error.response?.data?.detail || error.message || '生成失败，请检查后端服务是否已配置大模型')
  } finally {
    addingToGuidance.value = false
  }
}

const selectChapter = (chapter: string) => {
  searchQuery.value = chapter
  searchSuggestion.value = null
  handleSearch()
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
    searchQuery.value = transcript
    isRecording.value = false
    handleSearch()
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

const toggleVoiceInput = () => {
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

onMounted(() => {
  initSpeechRecognition()
})

onUnmounted(() => {
  if (recognition.value) {
    recognition.value.stop()
  }
})
</script>

<style scoped>
.search-container {
  max-width: 1100px;
  margin: 0 auto;
}

.search-header {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.search-box-wrapper {
  position: relative;
}

.search-box {
  display: flex;
  gap: 12px;
}

.search-input {
  flex: 1;
  height: 42px;
  padding: 0 16px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #2563eb;
}

.search-btn {
  height: 42px;
  padding: 0 24px;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.mic-btn {
  width: 42px;
  height: 42px;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.mic-btn:hover {
  background: #e2e8f0;
}

.mic-btn.recording {
  background: #ef4444;
  border-color: #ef4444;
  color: white;
  animation: pulse 1s infinite;
}

.mic-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.ai-btn {
  height: 42px;
  padding: 0 24px;
  background-color: #f59e0b;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.suggestion-section {
  background: #f0f9ff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  border: 1px solid #bae6fd;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.suggestion-icon {
  font-size: 18px;
}

.suggestion-text {
  font-size: 15px;
  font-weight: 500;
  color: #0369a1;
}

.suggestion-chapters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.chapter-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #7dd3fc;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #0369a1;
  transition: all 0.2s;
}

.chapter-btn:hover {
  background: #0369a1;
  color: white;
  border-color: #0369a1;
}

.results-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.results-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
}

.results-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #64748b;
}

.tab-btn.active {
  background: #eff6ff;
  color: #2563eb;
}

.results-list {
  padding: 24px;
}

.results-list.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.result-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.result-card.image-card {
  margin-bottom: 0;
}

.image-result {
  display: flex;
  flex-direction: column;
}

.result-image-wrapper {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  cursor: pointer;
}

.result-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 8px;
  font-size: 12px;
  text-align: center;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.type-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.text-badge {
  background: #dbeafe;
  color: #1d4ed8;
}

.image-badge {
  background: #fef3c7;
  color: #d97706;
}

.result-relevance {
  font-size: 13px;
  color: #10b981;
  font-weight: 500;
}

.result-content {
  font-size: 14px;
  line-height: 1.6;
  color: #475569;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-content :deep(h1),
.result-content :deep(h2),
.result-content :deep(h3) {
  font-size: 14px;
  font-weight: bold;
  margin: 4px 0;
  color: #1e293b;
}

.result-content :deep(p) {
  margin: 4px 0;
}

.result-content :deep(ul),
.result-content :deep(ol) {
  margin: 4px 0;
  padding-left: 16px;
}

.result-content :deep(li) {
  margin: 2px 0;
}

.result-content :deep(strong) {
  font-weight: bold;
  color: #1e293b;
}

.result-meta {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.action-btn:hover {
  background: #1d4ed8;
}

.action-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.chapter-path {
  margin-bottom: 8px;
  font-size: 13px;
}

.chapter-label {
  color: #94a3b8;
}

.chapter-text {
  color: #2563eb;
}

.param-section {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
  font-size: 13px;
}

.param-label {
  color: #64748b;
}

.param-value {
  color: #dc2626;
  font-weight: 500;
}

.related-images {
  margin-top: 16px;
}

.related-images-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1e293b;
}

.related-images-title.strong {
  color: #dc2626;
}

.related-images-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.related-image-item {
  flex-shrink: 0;
  width: 100px;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.related-image-item img {
  width: 100%;
  height: 80px;
  object-fit: cover;
}

.related-image-caption {
  font-size: 11px;
  text-align: center;
  padding: 4px;
  background: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.related-image-item.no-image {
  cursor: default;
}

.image-placeholder {
  width: 100%;
  height: 80px;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border-radius: 8px 8px 0 0;
}

.image-placeholder-mode .image-placeholder {
  border-radius: 8px;
  height: 100px;
}

.placeholder-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.placeholder-desc {
  font-size: 10px;
  color: #94a3b8;
  text-align: center;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.detail-image-item.no-image {
  cursor: default;
}

.detail-image-item .image-placeholder {
  height: 120px;
  border-radius: 8px;
}

.detail-image-item.image-placeholder-mode .image-placeholder {
  height: 150px;
}

.image-placeholder-large {
  width: 100%;
  min-height: 200px;
  background: #f1f5f9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  border-radius: 8px;
}

.image-placeholder-large .placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.image-placeholder-large .placeholder-desc {
  font-size: 14px;
  color: #64748b;
  text-align: center;
  line-height: 1.5;
}

.weak-images {
  opacity: 0.7;
}

.empty-state {
  text-align: center;
  padding: 60px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 15px;
  color: #64748b;
  margin-bottom: 20px;
}

.empty-action-btn {
  padding: 10px 24px;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-close {
  font-size: 24px;
  background: none;
  border: none;
  cursor: pointer;
  color: #94a3b8;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: 60vh;
}

.detail-item {
  margin-bottom: 16px;
}

.detail-item label {
  font-weight: 600;
  color: #64748b;
  display: block;
  margin-bottom: 4px;
}

.detail-content {
  line-height: 1.6;
  color: #334155;
}

.detail-content :deep(h1) {
  font-size: 20px;
  font-weight: bold;
  margin: 16px 0 10px;
  color: #1e293b;
}

.detail-content :deep(h2) {
  font-size: 17px;
  font-weight: bold;
  margin: 14px 0 8px;
  color: #1e293b;
}

.detail-content :deep(h3) {
  font-size: 15px;
  font-weight: bold;
  margin: 12px 0 6px;
  color: #1e293b;
}

.detail-content :deep(p) {
  margin: 8px 0;
}

.detail-content :deep(ul),
.detail-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.detail-content :deep(li) {
  margin: 4px 0;
}

.detail-content :deep(strong) {
  font-weight: bold;
  color: #1e293b;
}

.detail-content :deep(code) {
  background: #f1f5f9;
  padding: 1px 4px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 13px;
}

.detail-content :deep(pre) {
  background: #f1f5f9;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 10px 0;
}

.detail-content :deep(pre code) {
  background: none;
  padding: 0;
}

.detail-content :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.detail-content :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 12px 0;
}

.detail-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.detail-image-item {
  width: 150px;
  cursor: pointer;
}

.detail-image-item img {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
}

.detail-image-caption {
  font-size: 12px;
  text-align: center;
  margin-top: 4px;
  color: #64748b;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f1f5f9;
  justify-content: flex-end;
}

.modal-btn {
  padding: 8px 20px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.modal-btn.secondary {
  background: #f1f5f9;
  color: #64748b;
}

.modal-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.image-modal-overlay {
  background: rgba(0, 0, 0, 0.8);
}

.image-modal-content {
  max-width: 900px;
  width: 90%;
}

.image-modal-body {
  display: flex;
  justify-content: center;
  padding: 24px;
}

.preview-large-image {
  max-width: 100%;
  max-height: 60vh;
  border-radius: 8px;
}

.image-modal-footer {
  padding: 16px 24px;
  text-align: center;
}

.image-desc {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
}

.image-page {
  font-size: 12px;
  color: #94a3b8;
}

.sub-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.sub-tab-btn {
  padding: 6px 14px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #64748b;
}

.sub-tab-btn.active {
  background: #2563eb;
  color: white;
}

.results-list-inner {
  min-height: 200px;
}
</style>

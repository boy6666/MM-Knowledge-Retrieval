<template>
  <Layout>
    <div class="detail-container">
      <div class="detail-header">
        <button class="back-btn" @click="goBack">← 返回</button>
        <h1>{{ knowledge.title }}</h1>
      </div>
      
      <div class="detail-body">
        <aside class="sidebar">
          <div class="sidebar-section">
            <h3>文档概况</h3>
            <div class="info-card">
              <div class="info-row">
                <span class="label">分类</span>
                <span class="value">{{ categoryLabel }}</span>
              </div>
              <div class="info-row">
                <span class="label">设备类型</span>
                <span class="value">{{ knowledge.device_type || '未指定' }}</span>
              </div>
              <div class="info-row">
                <span class="label">来源</span>
                <span class="value">{{ knowledge.source || '系统录入' }}</span>
              </div>
              <div class="info-row">
                <span class="label">状态</span>
                <span class="value" :class="statusClass">{{ statusLabel }}</span>
              </div>
              <div class="info-row">
                <span class="label">创建时间</span>
                <span class="value">{{ formatDate(knowledge.created_at) }}</span>
              </div>
              <div class="info-row">
                <span class="label">段落数</span>
                <span class="value">{{ chunks.length }} 段</span>
              </div>
            </div>
          </div>
          
          <div class="sidebar-section">
            <h3>段落导航</h3>
            <div class="table-of-contents">
              <div 
                v-for="chunk in chunks" 
                :key="chunk.id"
                class="toc-item"
                :class="{ active: currentChunk === chunk.id }"
                @click="selectChunk(chunk.id)"
              >
                <span class="toc-number">{{ chunk.chunk_number + 1 }}</span>
                <span class="toc-preview">{{ getPreview(chunk.content) }}</span>
              </div>
              <div v-if="chunks.length === 0" class="empty-toc">
                暂无段落数据
              </div>
            </div>
          </div>
          
          <div class="sidebar-section">
            <button class="add-guide-btn" @click="addToGuidance">
              + 添加到作业指引
            </button>
          </div>
        </aside>
        
        <main class="content-area">
          <div class="content-header">
            <h2>段落 {{ currentChunkIndex + 1 }}</h2>
            <div class="content-nav">
              <button 
                v-if="currentChunkIndex > 0" 
                class="nav-btn"
                @click="prevChunk"
              >上一段</button>
              <span class="nav-info">{{ currentChunkIndex + 1 }} / {{ chunks.length }}</span>
              <button 
                v-if="currentChunkIndex < chunks.length - 1" 
                class="nav-btn"
                @click="nextChunk"
              >下一段</button>
            </div>
          </div>
          
          <div class="content-wrapper">
            <div v-if="currentChunkData" class="chunk-section">
              <div class="chunk-header">
                <span class="chunk-number">段落 {{ currentChunkData.chunk_number + 1 }}</span>
              </div>
              <div class="chunk-content">
                <p>{{ currentChunkData.content }}</p>
              </div>
            </div>
            <div v-else class="empty-content">
              <div class="empty-icon">📄</div>
              <p>暂无文档内容</p>
            </div>
          </div>
          
          <div class="content-footer">
            <button class="view-all-btn-lg" @click="showFullContent = true">查看全文</button>
          </div>
        </main>
      </div>
    </div>
    
    <div v-if="showFullContent" class="full-content-modal-overlay" @click="showFullContent = false">
      <div class="full-content-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ knowledge.title }} - 全文</h3>
          <button class="modal-close" @click="showFullContent = false">×</button>
        </div>
        <div class="modal-body">
          <div class="full-content-wrapper">
            <div 
              v-for="chunk in chunks" 
              :key="chunk.id"
              class="full-chunk-section"
            >
              <div class="full-chunk-header">
                <span class="full-chunk-number">段落 {{ chunk.chunk_number + 1 }}</span>
              </div>
              <div class="full-chunk-content">
                <p>{{ chunk.content }}</p>
              </div>
              <div class="full-chunk-divider"></div>
            </div>
            <div v-if="chunks.length === 0" class="empty-full-content">
              暂无文档内容
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn" @click="showFullContent = false">关闭</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus"
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'

const router = useRouter()
const route = useRoute()

const knowledgeId = ref(0)
const knowledge = ref<any>({})
const chunks = ref<any[]>([])
const currentChunk = ref<number | null>(null)
const showFullContent = ref(false)

const currentChunkIndex = computed(() => {
  if (currentChunk.value === null) return 0
  return chunks.value.findIndex(c => c.id === currentChunk.value)
})

const currentChunkData = computed(() => {
  if (currentChunk.value === null) return null
  return chunks.value.find(c => c.id === currentChunk.value) || null
})

const categoryLabel = computed(() => {
  const categories: Record<string, string> = {
    manual: '维修手册',
    troubleshooting: '故障排查',
    maintenance: '保养指南',
    other: '其他'
  }
  return categories[knowledge.value.category] || knowledge.value.category || '未分类'
})

const statusLabel = computed(() => {
  const statuses: Record<string, string> = {
    approved: '已通过',
    pending: '待审核',
    rejected: '已拒绝'
  }
  return statuses[knowledge.value.status] || knowledge.value.status || '未知'
})

const statusClass = computed(() => {
  const classes: Record<string, string> = {
    approved: 'status-approved',
    pending: 'status-pending',
    rejected: 'status-rejected'
  }
  return classes[knowledge.value.status] || ''
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getPreview = (content: string) => {
  return content.slice(0, 30) + (content.length > 30 ? '...' : '')
}

const selectChunk = (chunkId: number) => {
  currentChunk.value = chunkId
}

const prevChunk = () => {
  if (currentChunkIndex.value > 0) {
    selectChunk(chunks.value[currentChunkIndex.value - 1].id)
  }
}

const nextChunk = () => {
  if (currentChunkIndex.value < chunks.value.length - 1) {
    selectChunk(chunks.value[currentChunkIndex.value + 1].id)
  }
}

const goBack = () => {
  router.push('/knowledge')
}

const addToGuidance = async () => {
  const btn = document.querySelector('.add-guide-btn') as HTMLButtonElement
  if (btn) btn.disabled = true
  
  try {
    const response = await api.guidance.save({
      title: knowledge.value.title || '维修操作',
      device_type: knowledge.value.device_type || '摩托车发动机',
      fault_type: knowledge.value.title || '维修操作',
      content: knowledge.value.content || ''
    })
    
    if (response.guidance_id) {
      router.push(`/guidance/${response.guidance_id}`)
    }
  } catch (error: any) {
    console.error('添加失败:', error)
    ElMessage(error.response?.data?.detail || '添加失败，请检查后端服务是否已配置大模型')
  } finally {
    if (btn) btn.disabled = false
  }
}

const loadData = async () => {
  knowledgeId.value = Number(route.params.id)
  
  try {
    knowledge.value = await api.knowledge.get(knowledgeId.value)
    
    const chunksResponse = await api.knowledge.getChunks(knowledgeId.value)
    chunks.value = chunksResponse.chunks || []
    
    if (chunks.value.length > 0) {
      currentChunk.value = chunks.value[0].id
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage('加载数据失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.detail-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-btn {
  padding: 8px 16px;
  background-color: #f1f5f9;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #334155;
}

.detail-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

.detail-body {
  display: flex;
  gap: 24px;
}

.sidebar {
  width: 320px;
  flex-shrink: 0;
}

.sidebar-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 16px;
}

.sidebar-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.toc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.toc-header h3 {
  margin: 0;
  padding: 0;
  border: none;
}

.view-all-btn {
  padding: 4px 12px;
  font-size: 12px;
  color: #2563eb;
  background-color: #eff6ff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f8fafc;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row .label {
  font-size: 13px;
  color: #64748b;
}

.info-row .value {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
}

.status-approved {
  color: #22c55e;
}

.status-pending {
  color: #f59e0b;
}

.status-rejected {
  color: #ef4444;
}

.table-of-contents {
  max-height: 300px;
  overflow-y: auto;
}

.toc-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: background-color 0.2s;
}

.toc-item:hover {
  background-color: #f8fafc;
}

.toc-item.active {
  background-color: #eff6ff;
  border-left: 3px solid #2563eb;
}

.toc-number {
  width: 32px;
  height: 32px;
  background-color: #e2e8f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.toc-item.active .toc-number {
  background-color: #2563eb;
  color: white;
}

.toc-preview {
  font-size: 13px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-toc {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}

.add-guide-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h2 {
  font-size: 20px;
  font-weight: 600;
}

.content-nav {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-btn {
  padding: 8px 16px;
  background-color: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.nav-info {
  font-size: 14px;
  color: #64748b;
}

.content-wrapper {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 32px;
  min-height: 400px;
  overflow-y: auto;
}

.chunk-section {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chunk-header {
  margin-bottom: 20px;
}

.chunk-number {
  font-size: 14px;
  font-weight: 600;
  color: #2563eb;
  background-color: #eff6ff;
  padding: 6px 12px;
  border-radius: 6px;
}

.chunk-content {
  font-size: 16px;
  line-height: 2;
  color: #334155;
  flex: 1;
}

.chunk-content p {
  margin: 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 80px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-content p {
  color: #94a3b8;
  font-size: 16px;
}

.content-footer {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.view-all-btn-lg {
  padding: 12px 24px;
  font-size: 14px;
  color: white;
  background-color: #2563eb;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.full-content-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.full-content-modal {
  background: white;
  border-radius: 16px;
  width: 80%;
  max-width: 900px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-close {
  width: 32px;
  height: 32px;
  font-size: 24px;
  color: #64748b;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.full-content-wrapper {
  display: flex;
  flex-direction: column;
}

.full-chunk-section {
  margin-bottom: 24px;
}

.full-chunk-header {
  margin-bottom: 12px;
}

.full-chunk-number {
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
  background-color: #eff6ff;
  padding: 4px 10px;
  border-radius: 4px;
}

.full-chunk-content {
  font-size: 15px;
  line-height: 1.8;
  color: #334155;
}

.full-chunk-content p {
  margin: 0;
}

.full-chunk-divider {
  height: 1px;
  background-color: #e2e8f0;
  margin-top: 20px;
}

.empty-full-content {
  text-align: center;
  padding: 80px;
  color: #94a3b8;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

.modal-btn {
  padding: 10px 20px;
  font-size: 14px;
  color: white;
  background-color: #2563eb;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

@media (max-width: 1024px) {
  .detail-body {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
  }
  
  .table-of-contents {
    max-height: 200px;
  }
  
  .full-content-modal {
    width: 95%;
    max-height: 90vh;
  }
}</style>
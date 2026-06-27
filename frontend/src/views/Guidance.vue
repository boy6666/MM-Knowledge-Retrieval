<template>
  <Layout>
    <div class="guidance-container">
      <div class="list-section">
        <div class="list-header">
          <h2>我的检修方案</h2>
        </div>
        
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="guidanceList.length === 0" class="empty-state">
          <p>暂无检修方案</p>
          <p class="empty-hint">去知识检索或AI助手生成你的第一个检修方案吧</p>
        </div>
        
        <div v-else class="guidance-list">
          <div 
            v-for="item in guidanceList" 
            :key="item.id" 
            class="guidance-card"
            @click="openDetailModal(item.id)"
          >
            <div class="guidance-info">
              <h3 class="guidance-title">{{ item.title }}</h3>
              <div class="guidance-meta">
                <span class="guidance-device">{{ item.device_type }}</span>
                <span class="guidance-fault">{{ item.fault_type }}</span>
                <span class="guidance-views">{{ item.views || 0 }} 次浏览</span>
              </div>
            </div>
            <div class="guidance-date">{{ formatDate(item.created_at) }}</div>
          </div>
        </div>
      </div>
      
      <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetailModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>{{ guidanceDetail?.title }}</h3>
            <button class="close-btn" @click="closeDetailModal">×</button>
          </div>
          <div class="modal-body">
            <div v-if="loadingDetail" class="loading-state">
              <div class="loading-spinner"></div>
              <p>加载中...</p>
            </div>
            <div v-else-if="guidanceDetail">
              <div class="detail-meta">
                <span class="meta-item">设备类型：{{ guidanceDetail.device_type }}</span>
                <span class="meta-item">故障类型：{{ guidanceDetail.fault_type }}</span>
                <span class="meta-item">浏览：{{ guidanceDetail.views || 0 }} 次</span>
                <span class="meta-item">创建时间：{{ formatDate(guidanceDetail.created_at) }}</span>
              </div>
              <div class="detail-body" v-html="formatContent(guidanceDetail.content)"></div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="delete-btn" @click="deleteGuidance" v-if="guidanceDetail">删除</button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'
import { markdownToHtml } from '../utils/format'
import { useUserStore } from '../stores/user'

const route = useRoute()
const userStore = useUserStore()

const guidanceList = ref<any[]>([])
const guidanceDetail = ref<any>(null)
const loading = ref(false)
const loadingDetail = ref(false)
const showDetailModal = ref(false)

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split('T')[0]
}

const formatContent = (content: string) => {
  return markdownToHtml(content)
}

const loadList = async () => {
  loading.value = true
  try {
    const response = await api.guidance.listMine()
    if (response.items) {
      guidanceList.value = response.items
    }
  } catch (error) {
    console.error('加载方案列表失败:', error)
  } finally {
    loading.value = false
  }
}

const openDetailModal = async (id: number) => {
  showDetailModal.value = true
  loadingDetail.value = true
  try {
    const response = await api.guidance.get(id)
    if (response.guidance) {
      guidanceDetail.value = response.guidance
    }
  } catch (error) {
    console.error('加载方案详情失败:', error)
  } finally {
    loadingDetail.value = false
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  guidanceDetail.value = null
}

const deleteGuidance = async () => {
  if (!guidanceDetail.value) return
  if (!confirm('确定要删除这个检修方案吗？')) return
  
  try {
    const userId = userStore.userInfo?.id
    await api.guidance.delete(guidanceDetail.value.id, { user_id: userId })
    alert('删除成功')
    closeDetailModal()
    loadList()
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败')
  }
}

onMounted(() => {
  loadList()
  // 如果路由中有id参数，直接打开该检修方案详情
  const id = route.params.taskId
  if (id) {
    openDetailModal(Number(id))
  }
})
</script>

<style scoped>
.guidance-container {
  max-width: 1000px;
  margin: 0 auto;
}

.list-header {
  margin-bottom: 20px;
}

.list-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1e293b;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state p {
  color: #64748b;
  margin: 8px 0;
}

.empty-hint {
  font-size: 13px;
  color: #94a3b8 !important;
}

.guidance-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.guidance-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.guidance-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.guidance-title {
  margin: 0 0 8px;
  font-size: 16px;
  color: #1e293b;
}

.guidance-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #64748b;
}

.guidance-date {
  font-size: 13px;
  color: #94a3b8;
  white-space: nowrap;
}

.detail-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.detail-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 4px;
}

.back-btn:hover {
  background: #eff6ff;
}

.detail-header h2 {
  margin: 0;
  flex: 1;
  font-size: 20px;
  color: #1e293b;
}

.action-btn {
  padding: 6px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.action-btn:hover {
  background: #dc2626;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 13px;
  color: #64748b;
}

.detail-body {
  padding: 24px;
  line-height: 1.8;
  color: #334155;
  font-size: 15px;
}

.detail-body :deep(h1),
.detail-body :deep(h2),
.detail-body :deep(h3) {
  color: #1e293b;
  margin-top: 24px;
  margin-bottom: 12px;
}

.detail-body :deep(h1) {
  font-size: 22px;
}

.detail-body :deep(h2) {
  font-size: 18px;
}

.detail-body :deep(h3) {
  font-size: 16px;
}

.detail-body :deep(p) {
  margin-bottom: 12px;
}

.detail-body :deep(ul),
.detail-body :deep(ol) {
  padding-left: 24px;
  margin-bottom: 12px;
}

.detail-body :deep(li) {
  margin-bottom: 6px;
}

.detail-body :deep(strong) {
  font-weight: bold;
  color: #1e293b;
}

.detail-body :deep(code) {
  background: #f1f5f9;
  padding: 1px 4px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 13px;
}

.detail-body :deep(pre) {
  background: #f1f5f9;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 10px 0;
}

.detail-body :deep(pre code) {
  background: none;
  padding: 0;
}

.detail-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.detail-body :deep(hr) {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 14px 0;
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
  width: 90%;
  max-width: 800px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #94a3b8;
  padding: 0 8px;
}

.close-btn:hover {
  color: #64748b;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.delete-btn {
  padding: 8px 20px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.delete-btn:hover {
  background: #dc2626;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 13px;
  color: #64748b;
  margin: -20px -20px 20px;
}

.detail-body {
  line-height: 1.8;
  color: #334155;
  font-size: 15px;
}
</style>

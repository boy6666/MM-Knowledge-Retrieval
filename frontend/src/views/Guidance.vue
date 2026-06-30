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
              <div v-if="relatedPosts.length > 0" class="related-section">
                <h4 class="related-heading">类似用户经验 ({{ relatedPosts.length }})</h4>
                <div 
                  v-for="post in relatedPosts.slice(0, 5)" 
                  :key="post.id"
                  class="related-post-item"
                  @click="goToPost(post.id)"
                >
                  <div class="related-post-title">{{ post.title }}</div>
                  <div class="related-post-meta">
                    <span>{{ post.author_name }}</span>
                    <span>{{ formatDate(post.created_at) }}</span>
                    <span>👍 {{ post.likes }}</span>
                  </div>
                </div>
              </div>
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
import { ElMessage } from "element-plus"
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'
import { markdownToHtml } from '../utils/format'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const guidanceList = ref<any[]>([])
const guidanceDetail = ref<any>(null)
const loading = ref(false)
const loadingDetail = ref(false)
const showDetailModal = ref(false)
const relatedPosts = ref<any[]>([])

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
  relatedPosts.value = []
  try {
    const response = await api.guidance.get(id)
    if (response.guidance) {
      guidanceDetail.value = response.guidance
      // 智能匹配类似用户经验：从方案中提取核心关键词搜索社区帖子
      // 优先按设备类型+故障类型组合搜索，其次按故障类型，最后按设备类型
      const g = response.guidance
      let searchResults: any[] = []
      
      // 方法1：按 device_type + fault_type 组合搜索
      if (g.device_type && g.fault_type) {
        const device = cleanKeyword(g.device_type)
        const fault = cleanKeyword(g.fault_type)
        if (device && fault) {
          try {
            const resp1 = await api.community.list({ 
              device_type: device,
              fault_type: fault,
              page_size: 5 
            })
            if (resp1?.items?.length) {
              searchResults = resp1.items
            }
          } catch (e) {}
        }
      }
      
      // 方法2：如果没找到，按 fault_type 搜索
      if (searchResults.length === 0 && g.fault_type) {
        const fault = cleanKeyword(g.fault_type)
        if (fault) {
          try {
            const resp2 = await api.community.list({ 
              fault_type: fault,
              page_size: 5 
            })
            if (resp2?.items?.length) {
              searchResults = resp2.items
            }
          } catch (e) {}
        }
      }
      
      // 方法3：如果还没找到，按 device_type 搜索，但只保留故障类型相关的帖子
      if (searchResults.length === 0 && g.device_type) {
        const device = cleanKeyword(g.device_type)
        if (device) {
          try {
            const resp3 = await api.community.list({ 
              device_type: device,
              page_size: 5 
            })
            if (resp3?.items?.length) {
              if (g.fault_type) {
                const faultWords = extractKeywords(cleanKeyword(g.fault_type))
                searchResults = resp3.items.filter((post: any) => {
                  if (!post.fault_type) return false
                  const postFault = cleanKeyword(post.fault_type)
                  return faultWords.some(word => postFault.includes(word))
                })
              } else {
                searchResults = resp3.items
              }
            }
          } catch (e) {}
        }
      }
      
      // 方法4：最后尝试关键词搜索
      if (searchResults.length === 0) {
        let keyword = ''
        if (g.fault_type) {
          keyword = cleanKeyword(g.fault_type) || ''
        } else if (g.device_type) {
          keyword = cleanKeyword(g.device_type) || ''
        }
        if (keyword) {
          try {
            const resp4 = await api.community.list({ 
              keyword: keyword.substring(0, 20),
              page_size: 5 
            })
            if (resp4?.items?.length) {
              searchResults = resp4.items
            }
          } catch (e) {}
        }
      }
      
      if (searchResults.length > 0) {
        relatedPosts.value = searchResults
      }
    }
  } catch (error) {
    console.error('加载方案详情失败:', error)
  } finally {
    loadingDetail.value = false
  }
}

// 清理关键词：去掉编号前缀
const cleanKeyword = (str: string): string => {
  if (!str) return ''
  // 去掉数字编号：1.  9.1  1.2.3
  let cleaned = str.replace(/^\d+[\.\、]\s*/, '')
  // 去掉中文编号：一、二、三...  一、  九、...
  cleaned = cleaned.replace(/^[一二三四五六七八九十]+[\、，]\s*/, '')
  // 去掉多余空格
  cleaned = cleaned.trim()
  return cleaned.length >= 2 ? cleaned.substring(0, 20) : ''
}

// 提取有意义的关键词（使用滑动窗口提取2-4字符组合）
const extractKeywords = (str: string): string[] => {
  if (!str) return []
  const verbs = ['拆卸', '安装', '更换', '检查', '维修', '清洗', '调整', '测试', '保养', '与']
  let result = str
  verbs.forEach(v => {
    result = result.split(v).join(' ')
  })
  result = result.replace(/\d+/g, ' ')
  result = result.replace(/[\s\/\-]+/g, '')
  const keywords: string[] = []
  for (let len = 2; len <= 4 && len <= result.length; len++) {
    for (let i = 0; i <= result.length - len; i++) {
      const kw = result.substring(i, i + len)
      if (!keywords.includes(kw)) {
        keywords.push(kw)
      }
    }
  }
  return keywords
}

const goToPost = (postId: number) => {
  router.push(`/community/${postId}`)
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
    ElMessage('删除成功')
    closeDetailModal()
    loadList()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage('删除失败')
  }
}

onMounted(() => {
  loadList()
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

.related-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.related-heading {
  margin: 0 0 12px;
  font-size: 15px;
  color: #166534;
}

.related-post-item {
  padding: 10px 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background 0.15s;
}

.related-post-item:hover {
  background: #dcfce7;
}

.related-post-item .related-post-title {
  margin: 0 0 4px;
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
}

.related-post-item .related-post-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #94a3b8;
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

<template>
  <Layout>
    <div class="community-container">
      <div class="list-section">
        <div class="list-header">
          <div class="header-left">
            <h2>经验社区</h2>
            <div class="filter-bar">
              <input 
                v-model="keyword" 
                type="text" 
                placeholder="搜索帖子..."
                @keyup.enter="loadPosts"
              />
              <button class="search-btn" @click="loadPosts">搜索</button>
            </div>
          </div>
          <button class="publish-btn" @click="showPublishModal = true">
            + 发布经验
          </button>
        </div>
        
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
        
        <div v-else-if="posts.length === 0" class="empty-state">
          <p>暂无帖子</p>
          <p class="empty-hint">成为第一个分享经验的人吧</p>
        </div>
        
        <div v-else class="post-list">
          <div 
            v-for="post in posts" 
            :key="post.id" 
            class="post-card"
            @click="openDetailModal(post.id)"
          >
            <div class="post-info">
              <h3 class="post-title">{{ post.title }}</h3>
              <div class="post-meta">
                <span class="post-device">{{ post.device_type }}</span>
                <span class="post-fault">{{ post.fault_type }}</span>
                <span class="post-author">{{ post.author_name }}</span>
                <span class="post-stats">
                  <span>👁 {{ post.views || 0 }}</span>
                  <span>👍 {{ post.likes || 0 }}</span>
                </span>
              </div>
              <p class="post-excerpt">{{ getExcerpt(post.content) }}</p>
            </div>
            <div class="post-date">{{ formatDate(post.created_at) }}</div>
          </div>
        </div>
        
        <div v-if="total > pageSize" class="pagination">
          <button 
            class="page-btn" 
            :disabled="page <= 1"
            @click="changePage(page - 1)"
          >上一页</button>
          <span class="page-info">第 {{ page }} / {{ totalPages }} 页</span>
          <button 
            class="page-btn" 
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
          >下一页</button>
        </div>
      </div>
      
      <div v-if="showDetailModal" class="modal-overlay detail-modal-overlay" @click.self="closeDetailModal">
        <div class="modal-content detail-modal-content">
          <div class="modal-header">
            <h3>{{ postDetail?.title }}</h3>
            <button class="close-btn" @click="closeDetailModal">×</button>
          </div>
          <div class="modal-body detail-modal-body">
            <div v-if="loadingDetail" class="loading-state">
              <div class="loading-spinner"></div>
              <p>加载中...</p>
            </div>
            <div v-else-if="postDetail">
              <div class="detail-meta">
                <span class="meta-item">作者：{{ postDetail.author_name }}</span>
                <span class="meta-item">设备类型：{{ postDetail.device_type }}</span>
                <span class="meta-item">故障类型：{{ postDetail.fault_type }}</span>
                <span class="meta-item">浏览：{{ postDetail.views || 0 }} 次</span>
                <span class="meta-item">发布时间：{{ formatDate(postDetail.created_at) }}</span>
              </div>
              <div class="detail-body" v-html="formatContent(postDetail.content)"></div>
            </div>
          </div>
          <div class="modal-footer detail-modal-footer">
            <button 
              class="action-btn like-btn" 
              @click.stop="likePost"
              :class="{ liked: isLiked }"
            >
              👍 {{ postDetail?.likes || 0 }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="showPublishModal" class="modal-overlay" @click.self="showPublishModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>发布经验分享</h3>
            <button class="close-btn" @click="showPublishModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>标题</label>
              <input v-model="publishForm.title" type="text" placeholder="请输入标题" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>设备类型</label>
                <input v-model="publishForm.device_type" type="text" placeholder="如：发动机" />
              </div>
              <div class="form-group">
                <label>故障类型</label>
                <input v-model="publishForm.fault_type" type="text" placeholder="如：异响" />
              </div>
            </div>
            <div class="form-group">
              <label>你的昵称</label>
              <input v-model="publishForm.author_name" type="text" placeholder="匿名用户" />
            </div>
            <div class="form-group">
              <label>详细内容</label>
              <textarea 
                v-model="publishForm.content" 
                rows="8" 
                placeholder="请详细描述故障现象、排查过程、解决方法..."
              ></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="cancel-btn" @click="showPublishModal = false">取消</button>
            <button class="submit-btn" @click="publishPost" :disabled="publishing">
              {{ publishing ? '发布中...' : '发布' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'
import { markdownToHtml } from '../utils/format'


const route = useRoute()
const posts = ref<any[]>([])
const postDetail = ref<any>(null)
const loading = ref(false)
const loadingDetail = ref(false)
const isLiked = ref(false)

const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showPublishModal = ref(false)
const showDetailModal = ref(false)
const publishing = ref(false)
const publishForm = ref({
  title: '',
  device_type: '',
  fault_type: '',
  author_name: '',
  content: ''
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split('T')[0]
}

const formatContent = (content: string) => {
  return markdownToHtml(content)
}

const getExcerpt = (content: string) => {
  if (!content) return ''
  return content.substring(0, 100) + (content.length > 100 ? '...' : '')
}

const loadPosts = async () => {
  loading.value = true
  try {
    const response = await api.community.list({
      keyword: keyword.value,
      page: page.value,
      page_size: pageSize.value
    })
    if (response.items) {
      posts.value = response.items
      total.value = response.total || 0
    }
  } catch (error) {
    console.error('加载帖子列表失败:', error)
  } finally {
    loading.value = false
  }
}

const openDetailModal = async (id: number) => {
  showDetailModal.value = true
  isLiked.value = false
  loadingDetail.value = true
  try {
    const response = await api.community.get(id)
    if (response.post) {
      postDetail.value = response.post
    }
  } catch (error) {
    console.error('加载帖子详情失败:', error)
  } finally {
    loadingDetail.value = false
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  postDetail.value = null
}

const changePage = (newPage: number) => {
  page.value = newPage
  loadPosts()
}

const likePost = async () => {
  if (!postDetail.value || isLiked.value) return
  try {
    const response = await api.community.like(postDetail.value.id)
    if (response.success) {
      postDetail.value.likes = response.likes
      isLiked.value = true
    }
  } catch (error) {
    console.error('点赞失败:', error)
  }
}

const publishPost = async () => {
  if (!publishForm.value.title || !publishForm.value.content) {
    alert('请填写标题和内容')
    return
  }
  
  publishing.value = true
  try {
    const response = await api.community.create(publishForm.value)
    if (response.post_id) {
      alert('发布成功，等待审核通过后展示')
      showPublishModal.value = false
      publishForm.value = {
        title: '',
        device_type: '',
        fault_type: '',
        author_name: '',
        content: ''
      }
      loadPosts()
    }
  } catch (error) {
    console.error('发布失败:', error)
    alert('发布失败，请稍后重试')
  } finally {
    publishing.value = false
  }
}

onMounted(() => {
  loadPosts()
  const postId = route.params.postId
  if (postId) {
    openDetailModal(Number(postId))
  }
})
</script>

<style scoped>
.community-container {
  max-width: 1000px;
  margin: 0 auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 12px;
  font-size: 22px;
  color: #1e293b;
}

.filter-bar {
  display: flex;
  gap: 8px;
}

.filter-bar input {
  padding: 8px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
  width: 280px;
}

.search-btn {
  padding: 8px 16px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.search-btn:hover {
  background: #1d4ed8;
}

.publish-btn {
  padding: 10px 20px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.publish-btn:hover {
  background: #059669;
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

.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.post-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.post-title {
  margin: 0 0 8px;
  font-size: 16px;
  color: #1e293b;
}

.post-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.post-stats {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.post-excerpt {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.post-date {
  font-size: 13px;
  color: #94a3b8;
  white-space: nowrap;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.page-btn {
  padding: 6px 16px;
  background: white;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #64748b;
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
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.like-btn {
  background: #f1f5f9;
  color: #64748b;
}

.like-btn:hover {
  background: #e2e8f0;
}

.like-btn.liked {
  background: #fef3c7;
  color: #d97706;
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

.detail-body :deep(h1) {
  font-size: 22px;
  font-weight: bold;
  margin: 20px 0 12px;
  color: #1e293b;
}

.detail-body :deep(h2) {
  font-size: 19px;
  font-weight: bold;
  margin: 16px 0 10px;
  color: #1e293b;
}

.detail-body :deep(h3) {
  font-size: 16px;
  font-weight: bold;
  margin: 12px 0 8px;
  color: #1e293b;
}

.detail-body :deep(p) {
  margin: 10px 0;
}

.detail-body :deep(ul),
.detail-body :deep(ol) {
  margin: 10px 0;
  padding-left: 24px;
}

.detail-body :deep(li) {
  margin: 5px 0;
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
  max-width: 600px;
  max-height: 90vh;
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

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row .form-group {
  flex: 1;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  padding: 8px 16px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background: #e2e8f0;
}

.submit-btn {
  padding: 8px 20px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-btn:hover:not(:disabled) {
  background: #059669;
}

.detail-modal-overlay {
  z-index: 2000;
}

.detail-modal-content {
  max-width: 800px;
  width: 92%;
}

.detail-modal-body {
  padding: 0;
}

.detail-modal-footer {
  justify-content: flex-end;
}

.detail-modal-footer .action-btn {
  padding: 8px 18px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.detail-modal-footer .like-btn.liked {
  background: #fef3c7;
  color: #d97706;
}
</style>

<template>
  <Layout>
    <div class="admin-container">
      <div class="admin-header">
        <h2>管理员后台</h2>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
      
      <div class="admin-tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'users' }"
          @click="activeTab = 'users'"
        >用户管理</button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'posts' }"
          @click="activeTab = 'posts'"
        >帖子审核</button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'knowledge' }"
          @click="activeTab = 'knowledge'"
        >知识库管理</button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'stats' }"
          @click="activeTab = 'stats'"
        >系统统计</button>
      </div>
      
      <div v-if="activeTab === 'users'" class="tab-content">
        <div class="content-header">
          <h3>用户列表</h3>
          <input 
            v-model="userSearch" 
            type="text" 
            placeholder="搜索用户名..."
            class="search-input"
          />
        </div>
        <div v-if="loadingUsers" class="loading-state">加载中...</div>
        <div v-else class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>注册时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.email || '-' }}</td>
                <td>
                  <select 
                    :value="user.role" 
                    @change="updateRole(user.id, ($event.target as HTMLSelectElement).value)"
                    class="role-select"
                  >
                    <option value="user">普通用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <button 
                    class="delete-btn" 
                    @click="deleteUser(user.id)"
                    :disabled="user.id === 1"
                  >删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div v-if="activeTab === 'posts'" class="tab-content">
        <div class="content-header">
          <h3>待审核帖子</h3>
          <select v-model="postFilter" class="filter-select">
            <option value="all">全部</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">已拒绝</option>
          </select>
        </div>
        <div v-if="loadingPosts" class="loading-state">加载中...</div>
        <div v-else class="posts-list">
          <div v-for="post in filteredPosts" :key="post.id" class="post-item">
            <div class="post-info">
              <h4>{{ post.title }}</h4>
              <div class="post-meta">
                <span>{{ post.author_name }}</span>
                <span>{{ post.device_type }}</span>
                <span>{{ post.fault_type }}</span>
                <span class="status-badge" :class="post.status">
                  {{ getStatusText(post.status) }}
                </span>
              </div>
              <p>{{ getExcerpt(post.content) }}</p>
            </div>
            <div class="post-actions" v-if="post.status === 'pending'">
              <button class="approve-btn" @click="approvePost(post.id)">通过</button>
              <button class="reject-btn" @click="rejectPost(post.id)">拒绝</button>
            </div>
            <div class="post-actions" v-else>
              <button class="delete-btn" @click="deletePost(post.id)">删除</button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="activeTab === 'knowledge'" class="tab-content">
        <div class="content-header">
          <h3>知识库管理</h3>
          <select v-model="knowledgeFilter" class="filter-select">
            <option value="all">全部</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">已拒绝</option>
          </select>
        </div>
        <div v-if="loadingKnowledge" class="loading-state">加载中...</div>
        <div v-else class="knowledge-list">
          <div v-for="item in filteredKnowledge" :key="item.id" class="knowledge-item">
            <div class="knowledge-info">
              <h4>{{ item.title }}</h4>
              <div class="knowledge-meta">
                <span>{{ item.device_type }}</span>
                <span>{{ item.source }}</span>
                <span class="status-badge" :class="item.status">
                  {{ getStatusText(item.status) }}
                </span>
              </div>
            </div>
            <div class="knowledge-actions">
              <button 
                v-if="item.status === 'pending'" 
                class="approve-btn" 
                @click="approveKnowledge(item.id)"
              >通过</button>
              <button 
                v-if="item.status !== 'rejected'" 
                class="reject-btn" 
                @click="rejectKnowledge(item.id)"
              >拒绝</button>
              <button class="delete-btn" @click="deleteKnowledge(item.id)">删除</button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="activeTab === 'stats'" class="tab-content">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_users }}</div>
            <div class="stat-label">总用户数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_posts }}</div>
            <div class="stat-label">总帖子数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.pending_posts }}</div>
            <div class="stat-label">待审核帖子</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_knowledge }}</div>
            <div class="stat-label">知识库条目</div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'

const router = useRouter()

const activeTab = ref('users')
const users = ref<any[]>([])
const posts = ref<any[]>([])
const knowledge = ref<any[]>([])
const stats = ref({
  total_users: 0,
  total_posts: 0,
  pending_posts: 0,
  total_knowledge: 0
})

const userSearch = ref('')
const postFilter = ref('all')
const knowledgeFilter = ref('all')

const loadingUsers = ref(false)
const loadingPosts = ref(false)
const loadingKnowledge = ref(false)

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  return users.value.filter(u => u.username.includes(userSearch.value))
})

const filteredPosts = computed(() => {
  if (postFilter.value === 'all') return posts.value
  return posts.value.filter(p => p.status === postFilter.value)
})

const filteredKnowledge = computed(() => {
  if (knowledgeFilter.value === 'all') return knowledge.value
  return knowledge.value.filter(k => k.status === knowledgeFilter.value)
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split('T')[0]
}

const getExcerpt = (content: string) => {
  if (!content) return ''
  return content.substring(0, 100) + (content.length > 100 ? '...' : '')
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return map[status] || status
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await api.admin.listUsers()
    users.value = response.users || []
  } catch (error) {
    console.error('加载用户失败:', error)
  } finally {
    loadingUsers.value = false
  }
}

const loadPosts = async () => {
  loadingPosts.value = true
  try {
    const response = await api.community.listPending()
    posts.value = response.items || []
  } catch (error) {
    console.error('加载帖子失败:', error)
  } finally {
    loadingPosts.value = false
  }
}

const loadKnowledge = async () => {
  loadingKnowledge.value = true
  try {
    const response = await api.knowledge.list({ status: 'all' })
    knowledge.value = response.knowledge_list || []
  } catch (error) {
    console.error('加载知识库失败:', error)
  } finally {
    loadingKnowledge.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await api.admin.getStats()
    stats.value = response.data || stats.value
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const updateRole = async (userId: number, role: string) => {
  try {
    await api.admin.updateRole(userId, role)
  } catch (error) {
    console.error('更新角色失败:', error)
  }
}

const deleteUser = async (userId: number) => {
  if (!confirm('确定要删除该用户吗？')) return
  try {
    await api.admin.deleteUser(userId)
    loadUsers()
  } catch (error) {
    console.error('删除用户失败:', error)
  }
}

const approvePost = async (postId: number) => {
  try {
    await api.community.approve(postId)
    loadPosts()
  } catch (error) {
    console.error('审核失败:', error)
  }
}

const rejectPost = async (postId: number) => {
  try {
    await api.community.reject(postId)
    loadPosts()
  } catch (error) {
    console.error('拒绝失败:', error)
  }
}

const deletePost = async (postId: number) => {
  if (!confirm('确定要删除该帖子吗？')) return
  try {
    await api.community.delete(postId)
    loadPosts()
  } catch (error) {
    console.error('删除帖子失败:', error)
  }
}

const approveKnowledge = async (id: number) => {
  try {
    await api.knowledge.approve(id)
    loadKnowledge()
  } catch (error) {
    console.error('审核失败:', error)
  }
}

const rejectKnowledge = async (id: number) => {
  try {
    await api.admin.rejectKnowledge(id)
    loadKnowledge()
  } catch (error) {
    console.error('拒绝失败:', error)
  }
}

const deleteKnowledge = async (id: number) => {
  if (!confirm('确定要删除该知识库条目吗？')) return
  try {
    await api.admin.deleteKnowledge(id)
    loadKnowledge()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}

const loadTabData = () => {
  switch (activeTab.value) {
    case 'users':
      loadUsers()
      break
    case 'posts':
      loadPosts()
      break
    case 'knowledge':
      loadKnowledge()
      break
    case 'stats':
      loadStats()
      break
  }
}

onMounted(() => {
  loadTabData()
})
</script>

<style scoped>
.admin-container {
  max-width: 1200px;
  margin: 0 auto;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.admin-header h2 {
  margin: 0;
  font-size: 22px;
  color: #1e293b;
}

.logout-btn {
  padding: 8px 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.logout-btn:hover {
  background: #dc2626;
}

.admin-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.tab-btn {
  padding: 10px 20px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
}

.tab-btn.active {
  background: #2563eb;
  color: white;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h3 {
  margin: 0;
  font-size: 18px;
  color: #334155;
}

.search-input, .filter-select {
  padding: 8px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 14px;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #64748b;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.data-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #64748b;
  font-size: 13px;
}

.data-table tbody tr:hover {
  background: #f8fafc;
}

.role-select {
  padding: 4px 8px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 13px;
}

.delete-btn {
  padding: 4px 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.posts-list, .knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-item, .knowledge-item {
  background: white;
  padding: 16px 20px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.post-info, .knowledge-info {
  flex: 1;
}

.post-info h4, .knowledge-info h4 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #1e293b;
}

.post-meta, .knowledge-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.post-info p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.pending {
  background: #fef3c7;
  color: #d97706;
}

.status-badge.approved {
  background: #dcfce7;
  color: #16a34a;
}

.status-badge.rejected {
  background: #fee2e2;
  color: #dc2626;
}

.post-actions, .knowledge-actions {
  display: flex;
  gap: 8px;
  margin-left: 16px;
}

.approve-btn {
  padding: 6px 14px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.approve-btn:hover {
  background: #059669;
}

.reject-btn {
  padding: 6px 14px;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.reject-btn:hover {
  background: #d97706;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #1e293b;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
}
</style>

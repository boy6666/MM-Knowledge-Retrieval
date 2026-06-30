<template>
  <Layout>
    <div class="profile-container">
      <div v-if="!userStore.isLoggedIn" class="not-logged-in">
        <p>请先登录查看个人中心</p>
        <router-link to="/login" class="login-link">去登录</router-link>
      </div>

      <template v-else>
        <div class="profile-header">
          <div class="avatar">{{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
          <div class="user-info">
            <h2>{{ userStore.userInfo?.username || '用户' }}</h2>
            <p>{{ userStore.isAdmin ? '管理员' : '普通用户' }}</p>
          </div>
        </div>

        <div class="profile-content">
          <div class="section">
            <h3>基本信息</h3>
            <div class="info-list">
              <div class="info-item">
                <label>用户名</label>
                <span>{{ userStore.userInfo?.username || '-' }}</span>
              </div>
              <div class="info-item">
                <label>邮箱</label>
                <span>{{ userStore.userInfo?.email || '未绑定' }}</span>
              </div>
              <div class="info-item">
                <label>角色</label>
                <span>{{ userStore.isAdmin ? '管理员' : '普通用户' }}</span>
              </div>
              <div class="info-item">
                <label>注册时间</label>
                <span>{{ formatDate(userStore.userInfo?.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="section">
            <h3>数据统计</h3>
            <div v-if="stats" class="stats-grid">
              <div class="stat-card">
                <div class="stat-number">{{ stats.my_guidance }}</div>
                <div class="stat-label">检修方案</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ stats.my_posts }}</div>
                <div class="stat-label">社区帖子</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ stats.total_knowledge }}</div>
                <div class="stat-label">知识库条目</div>
              </div>
            </div>
            <div v-else class="loading-stats">加载中...</div>
          </div>

          <div class="section">
            <h3>快捷操作</h3>
            <div class="action-list">
              <router-link to="/guidance" class="action-item">
                <span>我的检修方案</span>
                <span class="action-arrow">→</span>
              </router-link>
              <router-link to="/community" class="action-item">
                <span>我的社区帖子</span>
                <span class="action-arrow">→</span>
              </router-link>
            </div>
          </div>

          <div class="section">
            <button class="logout-btn" @click="handleLogout">退出登录</button>
          </div>
        </div>
      </template>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const stats = ref<any>(null)

const formatDate = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  return dateStr.split('T')[0]
}

const loadStats = async () => {
  try {
    const response = await api.profile.getStats({ user_id: userStore.userInfo?.id })
    if (response?.data) {
      stats.value = response.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/')
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    loadStats()
  }
})
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 0 auto;
}

.profile-header {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar {
  width: 80px;
  height: 80px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
}

.user-info h2 {
  font-size: 24px;
  margin-bottom: 4px;
}

.user-info p {
  opacity: 0.9;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.section h3 {
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
}

.not-logged-in {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.not-logged-in p {
  font-size: 16px;
  color: #64748b;
  margin-bottom: 16px;
}

.login-link {
  display: inline-block;
  padding: 10px 24px;
  background: #2563eb;
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.info-item label {
  color: #64748b;
}

.info-item span {
  font-weight: 500;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  text-align: center;
  padding: 20px 12px;
  background: #f8fafc;
  border-radius: 10px;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

.loading-stats {
  text-align: center;
  color: #94a3b8;
  padding: 20px;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
  text-decoration: none;
  color: #1e293b;
  font-size: 14px;
  transition: background 0.2s;
}

.action-item:hover {
  background: #f8fafc;
}

.action-arrow {
  color: #94a3b8;
  font-size: 16px;
}

.logout-btn {
  width: 100%;
  padding: 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
</style>

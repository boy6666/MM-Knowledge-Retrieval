<template>
  <Layout>
    <div class="dashboard">
      <div class="welcome-section">
        <h2>欢迎使用设备检修知识检索与作业系统</h2>
        <p>基于多模态大模型技术，为您提供智能化的设备检修辅助服务</p>
      </div>
      
      <div class="quick-actions">
        <div class="action-card" @click="$router.push('/search')">
          <div class="action-icon">搜索</div>
          <div class="action-content">
            <h3>智能检索</h3>
            <p>快速检索检修方案、故障案例和技术文档</p>
          </div>
        </div>
        
        <div class="action-card" @click="$router.push('/guidance')">
          <div class="action-icon">指引</div>
          <div class="action-content">
            <h3>作业指引</h3>
            <p>获取标准化的检修流程和步骤指引</p>
          </div>
        </div>
        
        <div class="action-card" @click="$router.push('/knowledge')">
          <div class="action-icon">知识</div>
          <div class="action-content">
            <h3>知识管理</h3>
            <p>上传、审核和管理检修知识库</p>
          </div>
        </div>
      </div>
      
      <div class="recent-section">
        <h3>最近检修记录</h3>
        <div class="recent-list" v-if="recentRecords.length > 0">
          <div class="recent-item" v-for="item in recentRecords" :key="item.id">
            <div class="recent-info">
              <div class="recent-title">{{ item.title }}</div>
              <div class="recent-meta">{{ item.device_type || '通用设备' }} · {{ statusMap[item.status] || item.status }}</div>
            </div>
            <div class="recent-date">{{ formatDate(item.created_at) }}</div>
          </div>
        </div>
        <div v-else class="empty-recent">
          <p>暂无检修记录</p>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Layout from '../components/Layout.vue'

const recentRecords = ref<any[]>([])

const statusMap: Record<string, string> = {
  created: '待开始',
  in_progress: '进行中',
  completed: '已完成'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return dateStr.split('T')[0]
}

const loadRecentRecords = async () => {
  recentRecords.value = []
}

onMounted(() => {
  loadRecentRecords()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  padding: 40px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.welcome-section h2 {
  font-size: 28px;
  margin-bottom: 12px;
}

.welcome-section p {
  font-size: 16px;
  opacity: 0.9;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.action-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.action-icon {
  font-size: 20px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #eff6ff;
  border-radius: 12px;
  font-weight: bold;
  color: #2563eb;
}

.action-content h3 {
  font-size: 18px;
  margin-bottom: 4px;
}

.action-content p {
  font-size: 13px;
  color: #64748b;
}

.recent-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.recent-section h3 {
  margin-bottom: 16px;
  font-size: 18px;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.recent-title {
  font-weight: 500;
  font-size: 15px;
}

.recent-meta {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.recent-date {
  font-size: 13px;
  color: #94a3b8;
}
</style>
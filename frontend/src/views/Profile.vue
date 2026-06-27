<template>
  <Layout>
    <div class="profile-container">
      <div class="profile-header">
        <div class="avatar">用户</div>
        <div class="user-info">
          <h2>用户</h2>
          <p>普通用户</p>
        </div>
      </div>
      
      <div class="profile-content">
        <div class="section">
          <h3>基本信息</h3>
          <div class="info-list">
            <div class="info-item">
              <label>用户名</label>
              <span>user</span>
            </div>
            <div class="info-item">
              <label>邮箱</label>
              <span>user@example.com</span>
            </div>
            <div class="info-item">
              <label>角色</label>
              <span>普通用户</span>
            </div>
            <div class="info-item">
              <label>注册时间</label>
              <span>2026-06-01</span>
            </div>
          </div>
        </div>
        
        <div class="section">
          <h3>设置</h3>
          <div class="setting-list">
            <div class="setting-item">
              <span>修改密码</span>
              <button class="setting-btn">修改</button>
            </div>
            <div class="setting-item">
              <span>绑定邮箱</span>
              <button class="setting-btn">绑定</button>
            </div>
          </div>
        </div>
        
        <div class="section">
          <button class="logout-btn">退出登录</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import Layout from '../components/Layout.vue'

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

.setting-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.setting-btn {
  padding: 6px 16px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
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

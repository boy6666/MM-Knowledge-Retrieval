<template>
  <div class="layout-container">
    <aside class="sidebar">
      <div class="logo">设备检修助手</div>
      <nav class="nav-menu">
        <template v-if="!userStore.isAdmin">
          <router-link to="/" class="nav-item" active-class="active">
            <span>首页</span>
          </router-link>
          <router-link to="/chat" class="nav-item" active-class="active">
            <span>AI助手</span>
          </router-link>
          <router-link to="/search" class="nav-item" active-class="active">
            <span>知识检索</span>
          </router-link>
          <router-link to="/guidance" class="nav-item" active-class="active">
            <span>检修方案</span>
          </router-link>
          <router-link to="/community" class="nav-item" active-class="active">
            <span>经验社区</span>
          </router-link>
          <router-link to="/knowledge" class="nav-item" active-class="active">
            <span>知识管理</span>
          </router-link>
          <router-link to="/profile" class="nav-item" active-class="active">
            <span>个人中心</span>
          </router-link>
        </template>
        <router-link v-if="userStore.isAdmin" to="/admin" class="nav-item" active-class="active">
          <span>管理后台</span>
        </router-link>
      </nav>
    </aside>
    <main class="main-content">
      <header class="header">
        <div class="header-right">
          <template v-if="userStore.isLoggedIn">
            <span class="user-info">欢迎, {{ userStore.userInfo?.username }}</span>
            <button class="logout-btn" @click="handleLogout">退出</button>
          </template>
          <template v-else>
            <router-link to="/login" class="auth-link">登录</router-link>
            <router-link to="/register" class="auth-link">注册</router-link>
          </template>
        </div>
      </header>
      <div class="content-wrapper">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const handleLogout = () => {
  userStore.logout()
  window.location.href = '/login'
}

onMounted(() => {
  userStore.init()
})
</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 220px;
  background-color: #1e293b;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
}

.logo {
  font-size: 16px;
  font-weight: bold;
  padding: 20px 16px;
  border-bottom: 1px solid #334155;
}

.nav-menu {
  flex: 1;
  padding: 12px;
}

.nav-item {
  display: block;
  padding: 10px 12px;
  border-radius: 6px;
  color: #e2e8f0;
  text-decoration: none;
  margin-bottom: 4px;
  transition: background-color 0.2s;
}

.nav-item:hover {
  background-color: #334155;
}

.nav-item.active {
  background-color: #334155;
  color: white;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f1f5f9;
}

.header {
  height: 60px;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  font-size: 14px;
  color: #475569;
}

.logout-btn {
  padding: 6px 14px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.logout-btn:hover {
  background: #dc2626;
}

.auth-link {
  font-size: 14px;
  color: #2563eb;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
}

.auth-link:hover {
  background: #eff6ff;
}

.content-wrapper {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>

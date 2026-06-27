import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Search from '../views/Search.vue'
import Guidance from '../views/Guidance.vue'
import Community from '../views/Community.vue'
import Knowledge from '../views/Knowledge.vue'
import KnowledgeDetail from '../views/KnowledgeDetail.vue'
import Profile from '../views/Profile.vue'
import Chat from '../views/Chat.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Admin from '../views/Admin.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: false }
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
    meta: { requiresAuth: false }
  },
  {
    path: '/guidance',
    name: 'Guidance',
    component: Guidance,
    meta: { requiresAuth: false }
  },
  {
    path: '/guidance/:taskId',
    name: 'GuidanceDetail',
    component: Guidance,
    meta: { requiresAuth: false }
  },
  {
    path: '/community',
    name: 'Community',
    component: Community,
    meta: { requiresAuth: false }
  },
  {
    path: '/community/:postId',
    name: 'CommunityDetail',
    component: Community,
    meta: { requiresAuth: false }
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: Knowledge,
    meta: { requiresAuth: false }
  },
  {
    path: '/knowledge/:id',
    name: 'KnowledgeDetail',
    component: KnowledgeDetail,
    meta: { requiresAuth: false }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false, isAuthPage: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false, isAuthPage: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.isAuthPage) {
    if (token) {
      next('/')
    } else {
      next()
    }
    return
  }
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  if (to.meta.requiresAdmin && token) {
    try {
      const response = await fetch('/api/profile/info')
      const data = await response.json()
      if (data.user?.role !== 'admin') {
        next('/')
        return
      }
    } catch {
      next('/login')
      return
    }
  }
  
  next()
})

export default router

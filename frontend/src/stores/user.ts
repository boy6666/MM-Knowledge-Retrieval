import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<any>(null)
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  const login = async (username: string, password: string) => {
    try {
      const response = await api.auth.login(username, password)
      if (response.access_token) {
        token.value = response.access_token
        localStorage.setItem('token', response.access_token)
        await fetchUserInfo()
        return true
      }
      return false
    } catch (error) {
      console.error('登录失败:', error)
      return false
    }
  }

  const register = async (username: string, password: string, email?: string) => {
    try {
      const response = await api.auth.register(username, password, email)
      if (response.user_id) {
        return true
      }
      return false
    } catch (error) {
      console.error('注册失败:', error)
      return false
    }
  }

  const fetchUserInfo = async () => {
    try {
      const response = await api.profile.getInfo()
      if (response && response.username) {
        userInfo.value = response
      } else if (response && response.user) {
        userInfo.value = response.user
      }
    } catch (error: any) {
      if (error.response?.status === 403 || error.response?.status === 401) {
        token.value = ''
        userInfo.value = null
        localStorage.removeItem('token')
      }
      console.error('获取用户信息失败:', error)
    }
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const init = async () => {
    if (token.value) {
      await fetchUserInfo()
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    login,
    register,
    logout,
    init
  }
})

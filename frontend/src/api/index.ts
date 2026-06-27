import axios from 'axios'

const instance = axios.create({
  baseURL: '/api',
  timeout: 30000
})

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

type ApiResponse<T = any> = T

export const api = {
  auth: {
    register: (username: string, password: string, email?: string): Promise<ApiResponse> =>
      instance.post('/auth/register', { username, password, email }),
    login: (username: string, password: string): Promise<ApiResponse> =>
      instance.post('/auth/token', new URLSearchParams({ username, password, grant_type: 'password' }))
  },
  search: {
    text: (query: string): Promise<ApiResponse<{ query: string; results: any[]; suggestion?: any }>> =>
      instance.post('/search/text', new URLSearchParams({ query })),
    image: (image: File): Promise<ApiResponse> => {
      const formData = new FormData()
      formData.append('image', image)
      return instance.post('/search/image', formData)
    },
    hybrid: (formData: FormData): Promise<ApiResponse> =>
      instance.post('/search/hybrid', formData),
    suggest: (query: string): Promise<ApiResponse<{ suggestion: any }>> =>
      instance.get(`/search/suggest?query=${encodeURIComponent(query)}`),
  },
  guidance: {
    generate: (data: { device_type: string; fault_type: string; user_id?: number }): Promise<ApiResponse<{ guidance_id: number | null; title: string; content: string; device_type: string; fault_type: string; summary: string }>> =>
      instance.post('/guidance/generate', null, { params: data }),
    save: (data: { title: string; device_type: string; fault_type: string; content: string; source_type?: string; user_id?: number }): Promise<ApiResponse<{ guidance_id: number; guidance: any }>> =>
      instance.post('/guidance/save', null, { params: data }),
    get: (guidanceId: number): Promise<ApiResponse<{ guidance: any }>> =>
      instance.get(`/guidance/${guidanceId}`),
    listMine: (params?: { user_id?: number; page?: number; page_size?: number }): Promise<ApiResponse<{ items: any[]; total: number; page: number; page_size: number }>> =>
      instance.get('/guidance/list/mine', { params }),
    listPublic: (params?: { device_type?: string; fault_type?: string; keyword?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: any[]; total: number; page: number; page_size: number }>> =>
      instance.get('/guidance/list/public', { params }),
    delete: (guidanceId: number, params?: { user_id?: number }): Promise<ApiResponse<{ success: boolean }>> =>
      instance.delete(`/guidance/${guidanceId}`, { params }),
    togglePublic: (guidanceId: number, is_public: boolean, params?: { user_id?: number }): Promise<ApiResponse<{ success: boolean; is_public: boolean }>> =>
      instance.post(`/guidance/${guidanceId}/public`, null, { params: { is_public, ...params } })
  },
  community: {
    list: (params?: { device_type?: string; fault_type?: string; keyword?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: any[]; total: number; page: number; page_size: number }>> =>
      instance.get('/community/list', { params }),
    get: (postId: number): Promise<ApiResponse<{ post: any }>> =>
      instance.get(`/community/${postId}`),
    create: (data: { title: string; device_type: string; fault_type: string; content: string; images?: string; author_id?: number; author_name?: string }): Promise<ApiResponse<{ post_id: number; post: any }>> =>
      instance.post('/community/create', null, { params: data }),
    listMine: (params?: { author_id?: number; status?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: any[]; total: number; page: number; page_size: number }>> =>
      instance.get('/community/list/mine', { params }),
    like: (postId: number): Promise<ApiResponse<{ success: boolean; likes: number }>> =>
      instance.post(`/community/${postId}/like`),
    delete: (postId: number, params?: { author_id?: number }): Promise<ApiResponse<{ success: boolean }>> =>
      instance.delete(`/community/${postId}`, { params }),
    listPending: (params?: { page?: number; page_size?: number }): Promise<ApiResponse<{ items: any[]; total: number; page: number; page_size: number }>> =>
      instance.get('/community/admin/pending', { params }),
    approve: (postId: number, params?: { reviewer_id?: number; comment?: string }): Promise<ApiResponse<{ success: boolean; post: any }>> =>
      instance.post(`/community/admin/${postId}/approve`, null, { params }),
    reject: (postId: number, params?: { reviewer_id?: number; comment?: string }): Promise<ApiResponse<{ success: boolean; post: any }>> =>
      instance.post(`/community/admin/${postId}/reject`, null, { params })
  },
  admin: {
    listUsers: (): Promise<ApiResponse<{ users: any[] }>> =>
      instance.get('/admin/users'),
    updateRole: (userId: number, role: string): Promise<ApiResponse<{ success: boolean }>> =>
      instance.post(`/admin/users/${userId}/role`, null, { params: { role } }),
    deleteUser: (userId: number): Promise<ApiResponse<{ success: boolean }>> =>
      instance.delete(`/admin/users/${userId}`),
    getStats: (): Promise<ApiResponse<{ data: any }>> =>
      instance.get('/admin/stats'),
    rejectKnowledge: (id: number): Promise<ApiResponse> =>
      instance.post(`/admin/knowledge/${id}/reject`),
    deleteKnowledge: (id: number): Promise<ApiResponse> =>
      instance.delete(`/admin/knowledge/${id}`)
  },
  knowledge: {
    upload: (formData: FormData): Promise<ApiResponse> =>
      instance.post('/knowledge/upload', formData),
    add: (data: { title: string; content: string; category?: string; device_type?: string }): Promise<ApiResponse> =>
      instance.post('/knowledge/add', new URLSearchParams(data)),
    list: (params?: { category?: string; device_type?: string; status?: string }): Promise<ApiResponse<{ knowledge_list: any[] }>> =>
      instance.get('/knowledge/list', { params }),
    get: (id: number): Promise<ApiResponse<{ id: number; title: string; content: string; device_type: string; source: string }>> =>
      instance.get(`/knowledge/${id}`),
    getChunks: (id: number): Promise<ApiResponse<{ chunks: any[]; total: number }>> =>
      instance.get(`/knowledge/${id}/chunks`),
    approve: (id: number): Promise<ApiResponse> =>
      instance.post(`/knowledge/${id}/approve`)
  },
  profile: {
    setLLMConfig: (config: { mode: string; provider: string; modelName: string; apiKey: string; apiBase: string; localPath: string }): Promise<ApiResponse> =>
      instance.post('/profile/llm-config', config),
    testLLMConfig: (config: { provider: string; modelName: string; apiKey: string; apiBase: string }): Promise<ApiResponse> =>
      instance.post('/profile/test-llm', config),
    getStats: (params?: { user_id?: number }): Promise<ApiResponse<{ data: { my_guidance: number; my_posts: number; uploaded_docs: number; total_knowledge: number } }>> =>
      instance.get('/profile/stats', { params }),
    getInfo: (): Promise<ApiResponse<{ user: any }>> =>
      instance.get('/profile/info')
  },
  chat: {
    new: (): Promise<ApiResponse<{ conversation_id: string; message_count: number }>> =>
      instance.post('/chat/new'),
    get: (conversationId: string): Promise<ApiResponse<{ conversation_id: string; messages: any[] }>> =>
      instance.get(`/chat/${conversationId}`),
    chat: (conversationId: string, formData: FormData): Promise<ApiResponse<{ response: string; related_images: any[]; provider: string; difficulty: string }>> =>
      instance.post(`/chat/${conversationId}/chat`, formData),
    delete: (conversationId: string): Promise<ApiResponse> =>
      instance.delete(`/chat/${conversationId}`),
    speechToText: (audio: File): Promise<ApiResponse<{ text: string }>> => {
      const formData = new FormData()
      formData.append('audio', audio)
      return instance.post('/chat/speech-to-text', formData)
    },
    videoAnalyze: (video: File): Promise<ApiResponse<{ description: string; query: string; frame_image_url: string }>> => {
      const formData = new FormData()
      formData.append('video', video)
      return instance.post('/chat/video-analyze', formData)
    },
    imageGenerate: (prompt: string): Promise<ApiResponse<{ prompt: string; image_url: string }>> =>
      instance.post('/chat/image-generate', new URLSearchParams({ prompt }))
  }
}
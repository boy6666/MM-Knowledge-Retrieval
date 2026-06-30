<template>
  <Layout>
    <div class="knowledge-container">
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'list' }"
          @click="activeTab = 'list'"
        >知识列表</button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'upload' }"
          @click="activeTab = 'upload'"
        >上传文档</button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'add' }"
          @click="activeTab = 'add'"
        >添加知识</button>
      </div>
      
      <div v-if="activeTab === 'list'" class="list-section">
        <div class="filter-bar">
          <select v-model="filterCategory" class="filter-select">
            <option value="">全部分类</option>
            <option value="manual">手册</option>
            <option value="case">案例</option>
            <option value="guide">指南</option>
          </select>
          <select v-model="filterStatus" class="filter-select">
            <option value="">全部状态</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
          </select>
        </div>
        <div class="knowledge-list">
          <div 
            v-for="item in knowledgeList" 
            :key="item.id" 
            class="knowledge-card"
          >
            <div class="knowledge-header">
              <div class="knowledge-title">{{ item.title }}</div>
              <div 
                class="status-tag" 
                :class="{ pending: item.status === 'pending', approved: item.status === 'approved' }"
              >
                {{ item.status === 'pending' ? '待审核' : '已通过' }}
              </div>
            </div>
            <div class="knowledge-info">
              <span class="info-item">{{ categoryMap[item.category] || item.category }}</span>
              <span class="info-divider">|</span>
              <span class="info-item">{{ item.device_type || '通用' }}</span>
            </div>
            <div class="knowledge-content">{{ item.content }}</div>
            <div class="knowledge-actions">
              <button class="action-btn" @click="router.push(`/knowledge/${item.id}`)">查看详情</button>
              <button 
                v-if="item.status === 'pending'" 
                class="approve-btn"
                @click="approveItem(item.id)"
              >审核通过</button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="activeTab === 'upload'" class="upload-section">
        <h3>上传文档</h3>
        <div class="upload-form">
          <div class="form-group">
            <label>文档标题</label>
            <input v-model="uploadTitle" type="text" placeholder="请输入文档标题" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="uploadCategory" class="form-select">
              <option value="manual">手册</option>
              <option value="case">案例</option>
              <option value="guide">指南</option>
            </select>
          </div>
          <div class="form-group">
            <label>设备类型</label>
            <input v-model="uploadDeviceType" type="text" placeholder="请输入设备类型" />
          </div>
          <div class="form-group">
            <label>选择文件</label>
            <input 
              ref="uploadFile"
              type="file" 
              accept=".pdf" 
              class="file-input"
              @change="handleFileSelect"
            />
            <div v-if="selectedFile" class="file-info">
              {{ selectedFile.name }}
            </div>
          </div>
          <button class="submit-btn" @click="handleUpload">上传</button>
        </div>
      </div>
      
      <div v-if="activeTab === 'add'" class="add-section">
        <h3>添加知识</h3>
        <div class="add-form">
          <div class="form-group">
            <label>知识标题</label>
            <input v-model="addTitle" type="text" placeholder="请输入知识标题" />
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="addCategory" class="form-select">
              <option value="manual">手册</option>
              <option value="case">案例</option>
              <option value="guide">指南</option>
            </select>
          </div>
          <div class="form-group">
            <label>设备类型</label>
            <input v-model="addDeviceType" type="text" placeholder="请输入设备类型" />
          </div>
          <div class="form-group">
            <label>知识内容</label>
            <textarea v-model="addContent" rows="8" placeholder="请输入知识内容"></textarea>
          </div>
          <button class="submit-btn" @click="handleAdd">添加</button>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus"
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { api } from '../api'

const router = useRouter()

const activeTab = ref('list')
const filterCategory = ref('')
const filterStatus = ref('')

const knowledgeList = ref<any[]>([])

const uploadTitle = ref('')
const uploadCategory = ref('manual')
const uploadDeviceType = ref('')
const uploadFile = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

const addTitle = ref('')
const addCategory = ref('manual')
const addDeviceType = ref('')
const addContent = ref('')

const categoryMap: Record<string, string> = {
  manual: '手册',
  case: '案例',
  guide: '指南'
}

const loadKnowledgeList = async () => {
  try {
    const params: any = {}
    if (filterCategory.value) params.category = filterCategory.value
    if (filterStatus.value) params.status = filterStatus.value
    const result = await api.knowledge.list(params)
    knowledgeList.value = result.knowledge_list || []
  } catch (error) {
    console.error('获取知识列表失败:', error)
    knowledgeList.value = []
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  selectedFile.value = target.files?.[0] || null
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage('请选择文件')
    return
  }
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('title', uploadTitle.value || selectedFile.value.name.replace('.pdf', ''))
  formData.append('category', uploadCategory.value)
  if (uploadDeviceType.value) {
    formData.append('device_type', uploadDeviceType.value)
  }
  
  try {
    await api.knowledge.upload(formData)
    ElMessage('上传成功')
    uploadTitle.value = ''
    uploadDeviceType.value = ''
    selectedFile.value = null
    if (uploadFile.value) {
      uploadFile.value.value = ''
    }
    if (activeTab.value === 'list') {
      loadKnowledgeList()
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage('上传失败')
  }
}

const handleAdd = async () => {
  if (!addTitle.value || !addContent.value) {
    ElMessage('请填写标题和内容')
    return
  }
  
  try {
    await api.knowledge.add({
      title: addTitle.value,
      content: addContent.value,
      category: addCategory.value,
      device_type: addDeviceType.value || undefined
    })
    ElMessage('添加成功，待审核')
    addTitle.value = ''
    addContent.value = ''
    addDeviceType.value = ''
    if (activeTab.value === 'list') {
      loadKnowledgeList()
    }
  } catch (error) {
    console.error('添加失败:', error)
    ElMessage('添加失败')
  }
}

const approveItem = async (id: number) => {
  try {
    await api.knowledge.approve(id)
    const item = knowledgeList.value.find(i => i.id === id)
    if (item) {
      item.status = 'approved'
    }
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage('审核失败')
  }
}

watch([filterCategory, filterStatus], () => {
  loadKnowledgeList()
})

onMounted(() => {
  loadKnowledgeList()
})
</script>

<style scoped>
.knowledge-container {
  max-width: 1000px;
  margin: 0 auto;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.tab-btn {
  padding: 10px 20px;
  border: 1px solid #cbd5e1;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.tab-btn.active {
  background-color: #2563eb;
  color: white;
  border-color: #2563eb;
}

.list-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.knowledge-card {
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.knowledge-title {
  font-weight: 600;
  font-size: 16px;
}

.status-tag {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-tag.pending {
  background-color: #fef3c7;
  color: #d97706;
}

.status-tag.approved {
  background-color: #dcfce7;
  color: #166534;
}

.knowledge-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.info-divider {
  color: #cbd5e1;
}

.knowledge-content {
  font-size: 14px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 12px;
}

.knowledge-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.approve-btn {
  padding: 6px 12px;
  background-color: #22c55e;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.upload-section, .add-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.upload-section h3, .add-section h3 {
  margin-bottom: 20px;
  font-size: 18px;
}

.upload-form, .add-form {
  max-width: 500px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.file-input {
  width: 100%;
}

.file-info {
  margin-top: 8px;
  font-size: 13px;
  color: #2563eb;
}

.submit-btn {
  width: 100%;
  height: 42px;
  background-color: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
</style>
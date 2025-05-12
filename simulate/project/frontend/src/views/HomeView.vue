<template>
  <div class="home-view" role="region" aria-label="任务列表页面">
    <header class="header" role="banner">
      <h1>任务列表</h1>
      <el-input
        v-model="newTaskDescription"
        placeholder="请输入新任务"
        class="task-input"
        aria-label="输入新任务"
        @keyup.enter="handleAddTask"
      >
        <template #append>
          <el-button
            :disabled="!newTaskDescription.trim()"
            aria-label="添加任务"
            @click="handleAddTask"
          >
            添加
          </el-button>
        </template>
      </el-input>
    </header>
    <main class="task-list" role="list" aria-live="polite">
      <div v-if="loading" class="loading-state" role="status">加载中...</div>
      <div v-else-if="tasks.length === 0" class="empty-state" role="status">
        暂无任务
      </div>
      <TaskCard
        v-for="task in tasks"
        :key="task.id"
        :task="task"
        class="task-card-item"
        role="listitem"
      />
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useTaskStore } from '@/stores/taskStore'
import TaskCard from '@/components/TaskCard.vue'

export default defineComponent({
  name: 'HomeView',
  components: {
    TaskCard,
  },
  setup() {
    const taskStore = useTaskStore()
    const newTaskDescription = ref<string>('')
    const loading = ref<boolean>(false)

    const fetchActiveTasks = async () => {
      try {
        loading.value = true
        await taskStore.fetchTasks(false)
      } catch (error) {
        console.error('Failed to fetch active tasks:', error)
      } finally {
        loading.value = false
      }
    }
    // 添加计算属性过滤未完成任务
    const activeTasks = computed(() => {
      return taskStore.tasks.filter((task) => !task.completed)
    })

    const handleAddTask = async () => {
      if (!newTaskDescription.value.trim()) return
      try {
        loading.value = true
        await taskStore.addTask(newTaskDescription.value)
        newTaskDescription.value = ''
        // 重新获取活动任务以确保数据一致
        await fetchActiveTasks()
      } catch (error) {
        console.error('Failed to add task:', error)
        // 可以在这里添加用户通知
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      console.log('HomeView initialized')
      fetchActiveTasks()
    })

    return {
      tasks: activeTasks,
      loading,
      newTaskDescription,
      handleAddTask,
    }
  },
})
</script>

<style scoped>
.home-view {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.header {
  margin-bottom: 20px;
}

.task-input {
  margin-top: 10px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.loading-state,
.empty-state {
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.task-card-item {
  transition: transform 0.3s ease;
}

.task-card-item:hover {
  transform: scale(1.02);
}

@media (max-width: 768px) {
  .home-view {
    padding: 15px;
  }

  .header h1 {
    font-size: 20px;
  }

  .task-input {
    margin-top: 8px;
  }

  .task-list {
    gap: 8px;
  }
}
</style>

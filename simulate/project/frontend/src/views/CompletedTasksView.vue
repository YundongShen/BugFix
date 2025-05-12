<template>
  <div class="completed-tasks-view">
    <header class="header" role="banner" aria-label="已完成任务页面">
      <h1>已完成任务</h1>
    </header>
    <main class="task-container" role="main">
      <div v-if="loading" class="loading-indicator" aria-live="polite">
        加载中...
      </div>
      <div
        v-else-if="tasks.length === 0"
        class="empty-state"
        aria-live="polite"
      >
        暂无已完成任务
      </div>
      <div v-else class="task-list">
        <TaskCard
          v-for="task in tasks"
          :key="task.id"
          :task="task"
          class="task-card-item"
          role="listitem"
          @task-updated="handleTaskUpdated"
        />
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, computed } from 'vue'
import { useTaskStore } from '@/stores/taskStore'
import TaskCard from '@/components/TaskCard.vue'

export default defineComponent({
  name: 'CompletedTasksView',
  components: {
    TaskCard,
  },
  setup() {
    const taskStore = useTaskStore()
    const loading = ref(false)

    const tasks = computed(() => taskStore.completedTasks)

    const handleTaskUpdated = () => {
      taskStore.fetchTasks(true)
    }

    onMounted(async () => {
      try {
        loading.value = true
        await taskStore.fetchTasks(true)
      } catch (error) {
        console.error('Failed to fetch completed tasks:', error)
      } finally {
        loading.value = false
      }
    })

    return {
      tasks,
      loading,
      handleTaskUpdated,
    }
  },
})
</script>

<style scoped>
.completed-tasks-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.header h1 {
  font-size: 24px;
  margin-bottom: 20px;
  text-align: center;
  color: #303133;
}

.task-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.loading-indicator,
.empty-state {
  text-align: center;
  font-size: 16px;
  color: #909399;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-card-item {
  transition: transform 0.3s ease;
}

.task-card-item:hover {
  transform: scale(1.02);
}

@media (max-width: 768px) {
  .header h1 {
    font-size: 20px;
  }

  .task-container {
    padding: 10px;
  }

  .task-list {
    gap: 8px;
  }
}
</style>

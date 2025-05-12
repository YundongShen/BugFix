<template>
  <div class="task-card" :class="{ completed: task.completed }">
    <div class="task-content">
      <el-checkbox
        :model-value="task.completed"
        class="task-checkbox"
        @change="handleCompleteTask"
      />
      <span class="task-description">{{ task.description }}</span>
    </div>
    <el-button
      type="danger"
      icon="el-icon-delete"
      circle
      class="delete-button"
      @click="handleDeleteTask"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'
import { Task } from '@/stores/taskStore'
import { useTaskStore } from '@/stores/taskStore'

export default defineComponent({
  name: 'TaskCard',
  props: {
    task: {
      type: Object as PropType<Task>,
      required: true,
    },
  },
  emits: ['task-updated', 'task-deleted'],
  setup(props, { emit }) {
    const taskStore = useTaskStore()

    const handleCompleteTask = async () => {
      try {
        const updatedTask = await taskStore.completeTask(props.task.id)
        emit('task-updated', updatedTask)
      } catch (error) {
        console.error('Failed to mark task as completed:', error)
      }
    }

    const handleDeleteTask = async () => {
      try {
        await taskStore.deleteTask(props.task.id)
        emit('task-deleted', props.task.id)
      } catch (error) {
        console.error('Failed to delete task:', error)
      }
    }

    return {
      handleCompleteTask,
      handleDeleteTask,
    }
  },
})
</script>

<style scoped>
.task-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background-color: #fff;
  transition:
    background-color 0.3s ease,
    transform 0.3s ease;
}

.task-card:hover {
  transform: scale(1.02);
}

.task-card.completed {
  background-color: #f0f9eb;
}

.task-content {
  display: flex;
  align-items: center;
}

.task-checkbox {
  margin-right: 12px;
}

.task-description {
  font-size: 16px;
  color: #303133;
  text-decoration: none;
}

.task-card.completed .task-description {
  color: #909399;
  text-decoration: line-through;
}

.delete-button {
  margin-left: 12px;
}
</style>

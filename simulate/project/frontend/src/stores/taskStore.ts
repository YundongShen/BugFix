import { defineStore } from 'pinia'
import axios from 'axios'
import { ref, computed } from 'vue'

interface Task {
  id: number
  description: string
  completed: boolean
  created_at: string
}

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // 计算属性
  const activeTasks = computed(() => tasks.value.filter((t) => !t.completed))
  const completedTasks = computed(() => tasks.value.filter((t) => t.completed))

  // Fetch tasks based on completion status
  const fetchTasks = async (completed: boolean) => {
    try {
      loading.value = true
      const response = await axios.get('/tasks', { params: { completed } })
      if (response.status === 200) {
        // 先移除所有当前状态的任务
        tasks.value = tasks.value.filter((task) => task.completed !== completed)
        // 然后添加新获取的任务
        tasks.value = [...tasks.value, ...response.data]
        error.value = null
      } else {
        throw new Error(`Unexpected status code: ${response.status}`)
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch tasks'
      console.error('Error fetching tasks:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // Add a new task
  const addTask = async (description: string) => {
    try {
      const response = await axios.post('/tasks', { description })
      if (response.status === 201) {
        // 确保新任务有completed: false状态
        const newTask = { ...response.data, completed: false }
        // 添加到任务列表开头
        tasks.value.unshift(newTask)
        error.value = null
        return newTask // 返回新任务以便调用方使用
      }
      throw new Error(`Unexpected status code: ${response.status}`)
    } catch (err: any) {
      error.value = err.message || 'Failed to add task'
      console.error('Error adding task:', err)
      throw err // 重新抛出错误让调用方处理
    }
  }

  // Mark a task as completed
  const completeTask = async (taskId: number) => {
    try {
      const response = await axios.put(`/tasks/${taskId}/complete`)
      if (response.status === 200) {
        const updatedTask = response.data
        const taskIndex = tasks.value.findIndex((task) => task.id === taskId)
        if (taskIndex !== -1) {
          tasks.value[taskIndex] = updatedTask
        }
        error.value = null
        return updatedTask // 返回更新后的任务
      }
      throw new Error(`Unexpected status code: ${response.status}`)
    } catch (err: any) {
      error.value = err.message || 'Failed to mark task as completed'
      console.error('Error marking task as completed:', err)
      throw err
    }
  }

  // Delete a task
  const deleteTask = async (taskId: number) => {
    try {
      const response = await axios.delete(`/tasks/${taskId}`)
      if (response.status === 200) {
        tasks.value = tasks.value.filter((task) => task.id !== taskId)
        error.value = null
      } else {
        throw new Error(`Unexpected status code: ${response.status}`)
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete task'
      console.error('Error deleting task:', err)
    }
  }

  return {
    tasks,
    loading,
    error,
    fetchTasks,
    addTask,
    completeTask,
    deleteTask,
  }
})

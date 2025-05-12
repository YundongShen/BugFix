import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import CompletedTasksView from '@/views/CompletedTasksView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: { title: '任务列表' },
  },
  {
    path: '/completed',
    name: 'CompletedTasks',
    component: CompletedTasksView,
    meta: { title: '已完成任务' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, _, next) => {
  document.title = (to.meta.title as string) || 'Todo List'
  next()
})

export default router

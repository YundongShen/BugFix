<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <nav class="navbar" role="navigation" aria-label="主导航栏">
          <router-link
            to="/"
            class="nav-item"
            active-class="active"
            aria-current="page"
          >
            主页
          </router-link>
          <router-link
            to="/completed"
            class="nav-item"
            active-class="active"
            aria-current="page"
          >
            已完成任务
          </router-link>
        </nav>
      </el-header>
      <el-main class="app-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'App',
  mounted() {
    console.log('App component initialized')
  },
})
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

.app-header {
  background-color: #409eff;
  color: white;
  padding: 10px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar {
  display: flex;
  gap: 20px;
}

.nav-item {
  text-decoration: none;
  color: white;
  font-size: 18px;
  font-weight: bold;
  transition: color 0.3s ease;
  padding: 5px 10px;
  border-radius: 4px;
}

.nav-item:hover {
  color: #f0f9eb;
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  color: #f0f9eb;
  border-bottom: 2px solid #f0f9eb;
  background-color: rgba(255, 255, 255, 0.1);
}

.app-content {
  padding: 20px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 10px;
  }

  .nav-item {
    font-size: 16px;
    padding: 8px 12px;
  }
}
</style>

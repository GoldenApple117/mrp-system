<template>
  <div id="app-container">
    <el-container style="height: 100vh">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="app-aside">
        <div class="logo-area">
          <span v-if="!isCollapse" class="logo-text">MRP II 系统</span>
          <span v-else class="logo-text-short">MRP</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          :collapse="isCollapse"
          background-color="#1d1e2c"
          text-color="#a0a4b8"
          active-text-color="#409eff"
        >
          <el-menu-item index="/materials">
            <el-icon><Box /></el-icon>
            <span>物料管理</span>
          </el-menu-item>
          <el-menu-item index="/bom">
            <el-icon><Connection /></el-icon>
            <span>BOM管理</span>
          </el-menu-item>
          <el-menu-item index="/inventory">
            <el-icon><List /></el-icon>
            <span>库存管理</span>
          </el-menu-item>
          <el-menu-item index="/mps">
            <el-icon><Calendar /></el-icon>
            <span>MPS 主计划</span>
          </el-menu-item>
          <el-menu-item index="/mrp">
            <el-icon><Cpu /></el-icon>
            <span>MRP 运算</span>
          </el-menu-item>
          <el-menu-item index="/purchase">
            <el-icon><ShoppingCart /></el-icon>
            <span>采购管理</span>
          </el-menu-item>
          <el-menu-item index="/production">
            <el-icon><SetUp /></el-icon>
            <span>生产管理</span>
          </el-menu-item>
          <el-menu-item index="/routings">
            <el-icon><Connection /></el-icon>
            <span>工艺路线</span>
          </el-menu-item>
          <el-menu-item index="/reports">
            <el-icon><DataAnalysis /></el-icon>
            <span>报表分析</span>
          </el-menu-item>
          <el-menu-item index="/crp">
            <el-icon><TrendCharts /></el-icon>
            <span>CRP产能计划</span>
          </el-menu-item>
          <el-menu-item index="/inspection">
            <el-icon><Stamp /></el-icon>
            <span>检验盘点</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容 -->
      <el-container>
        <el-header class="app-header">
          <el-button text @click="isCollapse = !isCollapse">
            <el-icon :size="20"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          </el-button>
          <span class="page-title">{{ pageTitle }}</span>
          <div style="flex:1"></div>
          <el-tag size="small" type="success">系统运行中</el-tag>
        </el-header>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  const map = {
    '/materials': '物料主数据管理',
    '/bom': 'BOM 物料清单管理',
    '/inventory': '库存管理与出入库',
    '/mps': 'MPS 主生产计划',
    '/mrp': 'MRP 物料需求计算',
    '/purchase': '采购管理',
    '/production': '生产车间管理',
    '/reports': '报表与分析',
    '/crp': 'CRP产能需求计划',
    '/inspection': '检验与盘点管理',
  }
  return map[route.path] || 'MRP II 物料需求计划系统'
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  background: #f0f2f5;
}

.app-aside {
  background: #1d1e2c !important;
  overflow: hidden;
  transition: width 0.3s;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.logo-text {
  color: #409eff;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 2px;
}

.logo-text-short {
  color: #409eff;
  font-size: 16px;
  font-weight: 700;
}

.app-header {
  background: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 60px;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

.el-menu {
  border-right: none !important;
}

.el-menu-item {
  font-size: 14px !important;
  height: 48px !important;
  line-height: 48px !important;
}

.el-menu-item.is-active {
  background-color: rgba(64,158,255,0.1) !important;
}
</style>

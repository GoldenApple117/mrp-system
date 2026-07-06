<template>
  <div class="login-page" ref="pageRef">
    <!-- 动态粒子/电路背景 Canvas -->
    <canvas ref="canvasRef" class="bg-canvas"></canvas>
    <!-- 鼠标拖尾 Canvas -->
    <canvas ref="trailCanvasRef" class="trail-canvas"></canvas>

    <!-- CSS 几何轨道环（确保可见） -->
    <div class="orbit-ring orbit-outer">
      <svg viewBox="0 0 800 700" class="orbit-svg">
        <polygon points="400,20 729,209 603,550 197,550 71,209" fill="none" stroke="#3b82f6" stroke-width="1.2" opacity="0.35"/>
      </svg>
    </div>
    <div class="orbit-ring orbit-mid">
      <svg viewBox="0 0 600 600" class="orbit-svg">
        <circle cx="300" cy="300" r="220" fill="none" stroke="#6366f1" stroke-width="0.8" stroke-dasharray="10,16" opacity="0.28"/>
      </svg>
    </div>
    <div class="orbit-ring orbit-inner">
      <svg viewBox="0 0 400 400" class="orbit-svg">
        <polygon points="200,30 347,115 291,290 109,290 53,115" fill="none" stroke="#3b82f6" stroke-width="1" opacity="0.32"/>
      </svg>
    </div>

    <!-- 渐变光晕层 -->
    <div class="glow-layer">
      <div class="glow-orb glow-orb-1"></div>
      <div class="glow-orb glow-orb-2"></div>
    </div>

    <!-- 网格纹理覆盖 -->
    <div class="grid-overlay"></div>

    <!-- ====== 浮空品牌 Hero ====== -->
    <div class="hero-section">
      <div class="hero-logo-wrap">
        <img :src="yottaLogoUrl" alt="YOTTA IMAGE" class="hero-logo" />
        <div class="hero-logo-glow"></div>
      </div>
      <h1 class="hero-title">MRP II</h1>
      <p class="hero-subtitle">物料需求计划管理系统</p>
    </div>

    <!-- 玻璃态登录卡片容器 -->
    <div class="card-container" ref="cardContainerRef" @mousemove="handleCardTilt" @mouseleave="handleCardLeave">
      <!-- 边框流光 -->
      <div class="card-border-glow"></div>
      <!-- 脉冲光环（卡片外） -->
      <div class="pulse-ring pulse-ring-1"></div>
      <div class="pulse-ring pulse-ring-2"></div>

      <!-- 主卡片（纯表单） -->
      <div class="glass-card" :style="tiltStyle">

        <!-- 动态问候 + 时间图标 -->
        <div class="greeting-row">
          <span class="greeting-text">{{ greetingText }}</span>
          <span class="greeting-emoji">{{ greetingEmoji }}</span>
        </div>

        <!-- 会话过期提示（非错误） -->
        <transition name="error-shake">
          <div v-if="infoMsg" class="info-bar">
            <div class="info-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                <path d="M8 7.5v-3M8 11v.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <span class="info-text">{{ infoMsg }}</span>
          </div>
        </transition>

        <!-- 错误提示 -->
        <transition name="error-shake">
          <div v-if="errorMsg" class="error-bar">
            <div class="error-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
                <path d="M8 4.5v3.5M8 11v.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <span class="error-text">{{ errorMsg }}</span>
          </div>
        </transition>

        <!-- 登录表单 -->
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          @submit.prevent="handleLogin"
          class="login-form"
        >
          <!-- 用户名 -->
          <div class="input-group" :class="{ 'is-floating': form.username || usernameFocused, 'has-error': fieldErrors.username }">
            <div class="input-field">
              <div class="input-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="5" r="3" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M3 14c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </div>
              <label class="float-label">用户名</label>
              <input
                v-model="form.username"
                type="text"
                class="native-input"
                autocomplete="username"
                @focus="usernameFocused = true; infoMsg = ''; errorMsg = ''"
                @blur="usernameFocused = false; validateField('username')"
              />
              <div class="input-glow"></div>
            </div>
            <transition name="field-err-slide">
              <span v-if="fieldErrors.username" class="field-error-msg">{{ fieldErrors.username }}</span>
            </transition>
          </div>
          <el-form-item prop="username" class="sr-only">
            <el-input v-model="form.username" />
          </el-form-item>

          <!-- 密码 -->
          <div class="input-group" :class="{ 'is-floating': form.password || passwordFocused, 'has-error': fieldErrors.password }">
            <div class="input-field">
              <div class="input-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <rect x="2.5" y="7" width="11" height="7" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M5 7V5a3 3 0 1 1 6 0v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="8" cy="10.5" r="0.8" fill="currentColor"/>
                </svg>
              </div>
              <label class="float-label">密码</label>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="native-input"
                autocomplete="current-password"
                @focus="passwordFocused = true; infoMsg = ''; errorMsg = ''"
                @blur="passwordFocused = false; validateField('password')"
                @keyup.enter="handleLogin"
              />
              <button
                type="button"
                class="input-eye"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              >
                <svg v-if="!showPassword" width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 8s2.5-4.5 6-4.5S14 8 14 8s-2.5 4.5-6 4.5S2 8 2 8z" stroke="currentColor" stroke-width="1.5"/>
                  <circle cx="8" cy="8" r="2" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 8s2.5-4.5 6-4.5S14 8 14 8s-2.5 4.5-6 4.5S2 8 2 8z" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M3 3l10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
              <div class="input-glow"></div>
            </div>
            <transition name="field-err-slide">
              <span v-if="fieldErrors.password" class="field-error-msg">{{ fieldErrors.password }}</span>
            </transition>
          </div>
          <el-form-item prop="password" class="sr-only">
            <el-input v-model="form.password" />
          </el-form-item>

          <!-- 选项行 -->
          <div class="options-row">
            <label class="remember-label">
              <input type="checkbox" v-model="rememberMe" class="remember-check" />
              <span class="check-mark"></span>
              <span class="remember-text">记住此设备</span>
            </label>
            <span class="forgot-link">忘记密码？</span>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            class="submit-btn"
            :class="{ 'submit-btn--loading': loading }"
            :disabled="loading"
            @click="handleLogin"
          >
            <span class="submit-btn-bg"></span>
            <span class="submit-btn-shine"></span>
            <span class="submit-btn-text" :class="{ 'opacity-0': loading }">登 录</span>
            <span v-if="loading" class="submit-btn-spinner">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="animate-spin">
                <circle cx="10" cy="10" r="8" stroke="rgba(255,255,255,0.2)" stroke-width="2.5"/>
                <path d="M10 2a8 8 0 0 1 8 8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </span>
          </button>
        </el-form>

        <!-- 底部提示 -->
        <transition name="hint-fade">
          <div v-if="showHint" class="hint-strip">
            <span class="hint-text">演示账号 admin / admin123</span>
            <button class="hint-close" @click="showHint = false">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M3 3l6 6M9 3l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </transition>
      </div>
    </div>

    <!-- 底部 Powered by -->
    <div class="powered-by">
      <span class="powered-text">Powered by</span>
      <img :src="yottaLogoUrl" alt="YOTTA IMAGE" class="powered-logo" />
    </div>

    <!-- 装饰浮动元素 -->
    <div class="float-dot float-dot-1"></div>
    <div class="float-dot float-dot-2"></div>
    <div class="float-dot float-dot-3"></div>
    <div class="float-dot float-dot-4"></div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'
import yottaLogoUrl from '@/assets/yotta-logo.png'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const loading = ref(false)
const errorMsg = ref('')
const infoMsg = ref('')
const rememberMe = ref(false)
const showHint = ref(true)
const showPassword = ref(false)
const formRef = ref(null)
const pageRef = ref(null)
const canvasRef = ref(null)
const trailCanvasRef = ref(null)
const cardContainerRef = ref(null)

const form = reactive({
  username: '',
  password: '',
})

// ====== 记住我自动登录 ======
const REMEMBER_KEY = 'mrp_remember_login'

onMounted(() => {
  // 过期会话检测
  if (route.query.expired === '1' || route.query.session_expired === '1') {
    infoMsg.value = '会话已过期，请重新登录'
    router.replace({ query: {} })
    return
  }

  // 记住我自动登录
  try {
    const saved = localStorage.getItem(REMEMBER_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      if (data.token && data.expiresAt && Date.now() < data.expiresAt) {
        auth.setAuth(data.token, data.user || { username: data.username || '' })
        router.replace('/dashboard')
        return
      } else {
        localStorage.removeItem(REMEMBER_KEY)
      }
    }
  } catch (e) { console.error('[MRP] 加载记住密码失败', e) }
})

// ====== 实时表单校验 ======
const fieldErrors = reactive({ username: '', password: '' })

function validateField(field) {
  const v = form[field].trim()
  if (v.length === 0) {
    fieldErrors[field] = field === 'username' ? '请输入用户名' : '请输入密码'
    return false
  }
  if (field === 'password' && v.length < 3) {
    fieldErrors[field] = '密码至少需要 3 个字符'
    return false
  }
  fieldErrors[field] = ''
  return true
}

watch(() => form.username, (v) => {
  if (errorMsg.value) errorMsg.value = ''
  if (v.length === 0 && fieldErrors.username) fieldErrors.username = ''
  else if (v.length > 0 && fieldErrors.username) validateField('username')
})
watch(() => form.password, (v) => {
  if (errorMsg.value) errorMsg.value = ''
  if (v.length === 0 && fieldErrors.password) fieldErrors.password = ''
  else if (v.length > 0 && fieldErrors.password) validateField('password')
})

// ====== 按钮水波纹 ======
function createRipple(e) {
  const btn = e.currentTarget
  const rect = btn.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)
  const x = e.clientX - rect.left - size / 2
  const y = e.clientY - rect.top - size / 2

  const ripple = document.createElement('span')
  ripple.className = 'ripple-effect'
  ripple.style.width = ripple.style.height = size + 'px'
  ripple.style.left = x + 'px'
  ripple.style.top = y + 'px'
  btn.appendChild(ripple)

  ripple.addEventListener('animationend', () => ripple.remove())
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// ====== 动态时间问候 ======
const greetingText = computed(() => {
  const h = new Date().getHours()
  if (h >= 6 && h < 12) return '早上好'
  if (h >= 12 && h < 18) return '下午好'
  return '晚上好'
})
const greetingEmoji = computed(() => {
  const h = new Date().getHours()
  if (h >= 6 && h < 12) return '☀️'
  if (h >= 12 && h < 18) return '🌤️'
  return '🌙'
})

// ====== 3D 视差卡片 ======
const tiltStyle = ref({ transform: '' })
let tiltTimeout = null

function handleCardTilt(e) {
  if (!cardContainerRef.value) return
  const rect = cardContainerRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  const rx = ((e.clientY - cy) / (rect.height / 2)) * -4  // max ±4deg
  const ry = ((e.clientX - cx) / (rect.width / 2)) * 4
  tiltStyle.value = {
    transform: `perspective(800px) rotateX(${rx.toFixed(1)}deg) rotateY(${ry.toFixed(1)}deg) scale3d(1.01, 1.01, 1)`,
    transition: 'transform 0.1s ease-out',
  }
}

function handleCardLeave() {
  tiltStyle.value = {
    transform: 'perspective(800px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
    transition: 'transform 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
  }
}

// ====== 鼠标拖尾 ======
let trailAnimId = null
let trailDots = []

function initCursorTrail() {
  if (!trailCanvasRef.value) return
  const canvas = trailCanvasRef.value
  const ctx = canvas.getContext('2d')
  const dpr = Math.min(window.devicePixelRatio || 1, 2)

  function resize() {
    canvas.width = window.innerWidth * dpr
    canvas.height = window.innerHeight * dpr
    canvas.style.width = window.innerWidth + 'px'
    canvas.style.height = window.innerHeight + 'px'
    ctx.scale(dpr, dpr)
  }

  resize()
  window.addEventListener('resize', resize)

  let lastX = mouseX, lastY = mouseY

  function draw() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)

    // 添加新拖尾点（仅当鼠标在页面内移动时）
    if (mouseX > 0 && mouseY > 0 && (mouseX !== lastX || mouseY !== lastY)) {
      trailDots.push({
        x: mouseX, y: mouseY,
        life: 1,
        size: Math.random() * 2.5 + 1,
      })
      lastX = mouseX; lastY = mouseY
    }

    // 限制数量
    if (trailDots.length > 60) trailDots.shift()

    // 绘制拖尾
    for (let i = 0; i < trailDots.length; i++) {
      const d = trailDots[i]
      d.life -= 0.025
      d.size -= 0.03
      if (d.life <= 0 || d.size <= 0) continue

      ctx.beginPath()
      ctx.arc(d.x, d.y, Math.max(d.size, 0.3), 0, Math.PI * 2)
      ctx.fillStyle = `rgba(59, 130, 246, ${d.life * 0.45})`
      ctx.fill()
    }

    // 清理死点
    trailDots = trailDots.filter(d => d.life > 0 && d.size > 0.2)

    trailAnimId = requestAnimationFrame(draw)
  }

  draw()
}
let animFrameId = null
let mouseX = -1000
let mouseY = -1000

function initParticles() {
  if (!canvasRef.value) return
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  let W = window.innerWidth, H = window.innerHeight
  const particles = []

  function resize() {
    W = window.innerWidth; H = window.innerHeight
    canvas.width = W * dpr; canvas.height = H * dpr
    canvas.style.width = W + 'px'; canvas.style.height = H + 'px'
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }

  const count = Math.min(Math.floor(W * H / 12000), 100)
  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      size: Math.random() * 2 + 0.5,
      alpha: Math.random() * 0.6 + 0.1,
      alphaSpeed: (Math.random() - 0.5) * 0.008,
    })
  }

  function draw(ts) {
    ctx.clearRect(0, 0, W, H)
    const t = (ts || performance.now()) * 0.001

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i]
      p.x += p.vx; p.y += p.vy
      p.alpha += p.alphaSpeed
      if (p.alpha > 0.7) p.alphaSpeed = -Math.abs(p.alphaSpeed)
      if (p.alpha < 0.08) p.alphaSpeed = Math.abs(p.alphaSpeed)
      if (p.x < -50) p.x = W + 50
      if (p.x > W + 50) p.x = -50
      if (p.y < -50) p.y = H + 50
      if (p.y > H + 50) p.y = -50

      // 鼠标吸引
      const dx = p.x - mouseX, dy = p.y - mouseY
      const dist = Math.sqrt(dx*dx + dy*dy)
      if (mouseX > 0 && dist < 180) { p.x += (dx/dist)*0.5; p.y += (dy/dist)*0.5 }

      // 连线
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j]
        const lx = p.x - q.x, ly = p.y - q.y
        const ld = Math.sqrt(lx*lx + ly*ly)
        if (ld < 120) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(q.x, q.y)
          ctx.strokeStyle = `rgba(59, 130, 246, ${0.12 * (1 - ld/120)})`
          ctx.lineWidth = 0.6
          ctx.stroke()
        }
      }

      // 画粒子
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(99, 148, 237, ${p.alpha})`
      if (p.size > 1.5) {
        ctx.shadowColor = 'rgba(59, 130, 246, 0.3)'
        ctx.shadowBlur = 3
      }
      ctx.fill()
      ctx.shadowBlur = 0
    }

    animFrameId = requestAnimationFrame(draw)
  }

  resize()
  draw(performance.now())

  window.addEventListener('resize', resize)
  window.addEventListener('mousemove', (e) => {
    mouseX = e.clientX
    mouseY = e.clientY
  })
}

// ====== 浮动标签焦点状态 ======
const usernameFocused = ref(false)
const passwordFocused = ref(false)

// ====== 输入框 focus/blur（用于浮动标签动画） ======
const focusedField = ref(null)
function handleFieldFocus(e) {
  focusedField.value = e.target
}
function handleFieldBlur() {
  focusedField.value = null
}

// ====== 登录逻辑 ======
async function handleLogin(e) {
  // 触发水波纹
  if (e && !loading.value) createRipple(e)

  // 实时校验
  const uValid = validateField('username')
  const pValid = validateField('password')
  if (!uValid || !pValid) return

  // 同步 Element Plus 表单校验
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  errorMsg.value = ''

  try {
    const res = await api.post('/auth/login', {
      username: form.username,
      password: form.password,
    })
    auth.setAuth(res.access_token, res.user)

    // 记住我：持久化 token 到 localStorage，7 天有效
    if (rememberMe.value) {
      localStorage.setItem(REMEMBER_KEY, JSON.stringify({
        token: res.access_token,
        user: res.user,
        username: form.username,
        expiresAt: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 天
      }))
    }

    // 登录成功动画：卡片放大 → 淡出 → 跳转
    const card = document.querySelector('.glass-card')
    if (card) {
      card.style.animation = 'none'
      card.style.opacity = '0'
      card.style.transform = 'scale(1.03)'
      card.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
    }
    setTimeout(() => router.push('/dashboard'), 500)
  } catch (e) {
    const detail = e?.response?.data?.detail
    errorMsg.value = typeof detail === 'string' ? detail : '用户名或密码错误，请重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  nextTick(() => {
    initParticles()
    initCursorTrail()
  })
})

onBeforeUnmount(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId)
  if (trailAnimId) cancelAnimationFrame(trailAnimId)
})
</script>

<style scoped>
/* ====== 全屏画布 ====== */
.login-page {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #0a0e17;
  overflow: hidden;
}

.bg-canvas {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
}

/* ── 鼠标拖尾 Canvas ── */
.trail-canvas {
  position: fixed;
  inset: 0;
  z-index: 4;
  pointer-events: none;
}

/* ── CSS 轨道环（确保渲染） ── */
.orbit-ring {
  position: absolute;
  z-index: 2;
  pointer-events: none;
}
.orbit-svg {
  width: 100%;
  height: 100%;
}
.orbit-outer {
  width: 76vw;
  height: 76vw;
  max-width: 900px;
  max-height: 900px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: orbit-spin-slow 40s linear infinite;
}
.orbit-mid {
  width: 56vw;
  height: 56vw;
  max-width: 660px;
  max-height: 660px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: orbit-spin-rev 30s linear infinite;
}
.orbit-inner {
  width: 34vw;
  height: 34vw;
  max-width: 400px;
  max-height: 400px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: orbit-spin-fast 25s linear infinite;
}

@keyframes orbit-spin-slow { to { transform: translate(-50%, -50%) rotate(360deg); } }
@keyframes orbit-spin-rev { to { transform: translate(-50%, -50%) rotate(-360deg); } }
@keyframes orbit-spin-fast { to { transform: translate(-50%, -50%) rotate(360deg); } }

/* ====== 光晕层 ====== */
.glow-layer {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(140px);
  animation: orb-float 12s ease-in-out infinite;
}
.glow-orb-1 {
  width: 600px;
  height: 600px;
  top: -200px;
  left: -100px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.40), transparent 65%);
  animation-delay: 0s;
}
.glow-orb-2 {
  width: 500px;
  height: 500px;
  bottom: -150px;
  right: -120px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.32), transparent 65%);
  animation-delay: -6s;
}

@keyframes orb-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 15px) scale(0.95); }
}

/* ====== 网格叠加层 ====== */
.grid-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse 70% 70% at center, black 30%, transparent 75%);
}

/* ====== 卡片容器 + 脉冲环 ====== */
.card-container {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 800px;
}

/* ── 边框流光 ── */
.card-border-glow {
  position: absolute;
  inset: -2px;
  border-radius: 22px;
  padding: 2px;
  background: conic-gradient(
    from 0deg,
    transparent 0deg,
    rgba(59, 130, 246, 0.4) 90deg,
    rgba(99, 102, 241, 0.3) 180deg,
    transparent 270deg,
    transparent 360deg
  );
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask-composite: xor;
  animation: border-rotate 6s linear infinite;
  pointer-events: none;
  opacity: 0.7;
}

@keyframes border-rotate {
  to { filter: hue-rotate(360deg); }
}

.pulse-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(59, 130, 246, 0.12);
  animation: pulse-expand 4s ease-out infinite;
  pointer-events: none;
}
.pulse-ring-1 {
  width: 420px;
  height: 420px;
  animation-delay: 0s;
}
.pulse-ring-2 {
  width: 420px;
  height: 420px;
  animation-delay: 2s;
}

@keyframes pulse-expand {
  0% { transform: scale(0.92); opacity: 0.5; }
  50% { opacity: 0.1; }
  100% { transform: scale(1.15); opacity: 0; }
}

/* ====== 玻璃态主卡片 ====== */
.glass-card {
  position: relative;
  width: 420px;
  padding: 32px 40px 36px;
  background: linear-gradient(145deg,
    rgba(20, 24, 38, 0.85) 0%,
    rgba(15, 18, 30, 0.9) 100%);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  backdrop-filter: blur(40px);
  box-shadow:
    0 8px 48px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.03) inset,
    0 0 120px rgba(59, 130, 246, 0.06);
  animation: card-appear 0.7s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}

@keyframes card-appear {
  0% { opacity: 0; transform: translateY(24px) scale(0.96); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── 动态问候 ── */
.greeting-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
  animation: fade-slide-up 0.6s 0.05s both;
}
.greeting-text {
  font-size: 15px;
  font-weight: 500;
  color: rgba(226, 232, 240, 0.85);
}
.greeting-emoji {
  font-size: 16px;
}

/* ====== 浮空品牌 Hero ====== */
.hero-section {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 28px;
  animation: hero-appear 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes hero-appear {
  0% { opacity: 0; transform: translateY(16px); }
  100% { opacity: 1; transform: translateY(0); }
}

.hero-logo-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-logo {
  position: relative;
  z-index: 1;
  height: 64px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 4px 20px rgba(59, 130, 246, 0.35));
}

.hero-logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 180px;
  height: 100px;
  transform: translate(-50%, -50%);
  background: radial-gradient(ellipse at center, rgba(59, 130, 246, 0.18), transparent 70%);
  filter: blur(30px);
  pointer-events: none;
  animation: hero-glow-pulse 4s ease-in-out infinite;
}

@keyframes hero-glow-pulse {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
}

.hero-title {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: #e8ecf1;
  margin: 16px 0 0;
}

.hero-subtitle {
  font-size: 13px;
  color: rgba(148, 163, 184, 0.6);
  margin: 6px 0 0;
  letter-spacing: 0.12em;
}

/* ====== 错误提示 ====== */
.error-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  animation: fade-slide-up 0.6s 0.1s both;
}

@keyframes fade-slide-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.error-icon {
  color: #f87171;
  flex-shrink: 0;
}
.error-text {
  font-size: 13px;
  color: #fca5a5;
  line-height: 1.4;
}

.error-shake-enter-active {
  animation: error-shake-in 0.4s ease;
}
@keyframes error-shake-in {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(6px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(4px); }
}

/* ── 会话过期提示（信息型，非错误） ── */
.info-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.18);
  border-radius: 12px;
  animation: fade-slide-up 0.6s 0.1s both;
}
.info-icon {
  color: rgba(96, 165, 250, 0.8);
  flex-shrink: 0;
}
.info-text {
  font-size: 13px;
  color: rgba(147, 197, 253, 0.8);
  line-height: 1.4;
}

/* ====== 登录表单 ====== */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ====== 自定义输入组（浮动标签） ====== */
.input-group {
  position: relative;
  animation: fade-slide-up 0.6s both;
}
.input-group:nth-child(1) { animation-delay: 0.25s; }
.input-group:nth-child(2) { animation-delay: 0.35s; }

.float-label {
  position: absolute;
  left: 48px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: rgba(148, 163, 184, 0.35);
  pointer-events: none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: left center;
  z-index: 0;
}

.is-floating .float-label,
.input-field:focus-within .float-label {
  top: 8px;
  transform: translateY(0) scale(0.7);
  color: rgba(59, 130, 246, 0.7);
}

.has-error .float-label,
.has-error.input-field:focus-within .float-label {
  color: rgba(239, 68, 68, 0.7);
}

.native-input {
  position: relative;
  z-index: 1;
  flex: 1;
  height: 48px;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #e8ecf1;
  font-family: inherit;
  padding: 16px 12px 4px 0;
}
.native-input::placeholder {
  color: transparent;
}
.native-input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 30px rgba(15, 18, 30, 0.95) inset !important;
  -webkit-text-fill-color: #e8ecf1 !important;
  caret-color: #e8ecf1;
}

/* ── 内联字段错误 ── */
.field-error-msg {
  display: block;
  font-size: 10px;
  color: #f87171;
  margin-top: 4px;
  padding-left: 4px;
  letter-spacing: 0.03em;
}
.field-err-slide-enter-active {
  transition: all 0.2s ease;
}
.field-err-slide-leave-active {
  transition: all 0.15s ease;
}
.field-err-slide-enter-from,
.field-err-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* 错误状态输入框变红 */
.has-error .input-field {
  border-color: rgba(239, 68, 68, 0.35) !important;
}
.has-error .input-field:focus-within {
  border-color: rgba(239, 68, 68, 0.5) !important;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.06) !important;
}
.has-error .input-icon {
  color: rgba(239, 68, 68, 0.5) !important;
}

/* ── 输入框容器 ── */
.input-field {
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}
.input-field:focus-within {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(59, 130, 246, 0.04);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}

.input-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 48px;
  flex-shrink: 0;
  color: rgba(148, 163, 184, 0.35);
  transition: color 0.3s;
}
.input-field:focus-within .input-icon {
  color: rgba(59, 130, 246, 0.6);
}

.input-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 12px;
  transition: opacity 0.3s;
  opacity: 0;
  box-shadow: inset 0 0 20px rgba(59, 130, 246, 0.06);
}
.input-field:focus-within .input-glow {
  opacity: 1;
}

/* 密码可见性切换 */
.input-eye {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 48px;
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(148, 163, 184, 0.3);
  transition: color 0.2s;
  flex-shrink: 0;
}
.input-eye:hover {
  color: rgba(148, 163, 184, 0.6);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ====== 选项行 ====== */
.options-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  animation: fade-slide-up 0.6s 0.45s both;
}

.remember-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}
.remember-check {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.check-mark {
  width: 16px;
  height: 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.remember-check:checked + .check-mark {
  background: rgba(59, 130, 246, 0.8);
  border-color: rgba(59, 130, 246, 0.8);
}
.remember-check:checked + .check-mark::after {
  content: '';
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translateY(-1px);
}
.remember-text {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.5);
}

.forgot-link {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.3);
  cursor: not-allowed;
  user-select: none;
}

/* ====== 登录按钮 ====== */
.submit-btn {
  position: relative;
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.35em;
  color: #fff;
  overflow: hidden;
  animation: fade-slide-up 0.6s 0.55s both;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.submit-btn-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
  transition: opacity 0.3s;
}
.submit-btn-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    105deg,
    transparent 30%,
    rgba(255, 255, 255, 0.08) 45%,
    rgba(255, 255, 255, 0.12) 50%,
    rgba(255, 255, 255, 0.08) 55%,
    transparent 70%
  );
  background-size: 200% 100%;
  animation: btn-shine 3s ease-in-out infinite;
  pointer-events: none;
}
@keyframes btn-shine {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(37, 99, 235, 0.35);
}
.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}
.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.8;
}
.submit-btn--loading .submit-btn-bg {
  opacity: 0.6;
}

.submit-btn-text {
  position: relative;
  z-index: 2;
  transition: opacity 0.2s;
}

.submit-btn-spinner {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

/* ── 水波纹效果 ── */
.ripple-effect {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0);
  animation: ripple-anim 0.6s ease-out forwards;
  pointer-events: none;
  z-index: 1;
}
@keyframes ripple-anim {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

/* ====== 底部提示 ====== */
.hint-strip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.3);
  animation: fade-slide-up 0.6s 0.65s both;
}
.hint-text {
  user-select: none;
}
.hint-close {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  padding: 2px;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.hint-close:hover {
  opacity: 1;
}

.hint-fade-enter-active { transition: opacity 0.2s ease; }
.hint-fade-leave-active { transition: opacity 0.15s ease; }
.hint-fade-enter-from,
.hint-fade-leave-to { opacity: 0; }

/* ====== Powered by 脚标 ====== */
.powered-by {
  position: absolute;
  bottom: 28px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 8px;
}
.powered-text {
  font-size: 10px;
  color: rgba(148, 163, 184, 0.25);
  letter-spacing: 0.1em;
}
.powered-logo {
  height: 12px;
  width: auto;
  opacity: 0.25;
  filter: grayscale(1);
}

/* ====== 浮动装饰点 ====== */
.float-dot {
  position: absolute;
  z-index: 3;
  pointer-events: none;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.15);
  animation: float-rotate 20s linear infinite;
}
.float-dot-1 { width: 4px; height: 4px; top: 22%; left: 18%; animation-delay: 0s; }
.float-dot-2 { width: 6px; height: 6px; top: 68%; right: 14%; animation-delay: -5s; }
.float-dot-3 { width: 3px; height: 3px; top: 35%; right: 25%; animation-delay: -10s; }
.float-dot-4 { width: 5px; height: 5px; bottom: 25%; left: 22%; animation-delay: -15s; }

@keyframes float-rotate {
  0% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(30px, -20px) rotate(90deg); }
  50% { transform: translate(10px, 10px) rotate(180deg); }
  75% { transform: translate(-20px, -10px) rotate(270deg); }
  100% { transform: translate(0, 0) rotate(360deg); }
}

/* ====== Element Plus 表单隐藏 ====== */
:deep(.el-form-item) {
  display: none;
}

/* ====== 旋转动画 ====== */
.animate-spin {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ====== 响应式 ====== */
@media (max-width: 480px) {
  .hero-logo { height: 48px; }
  .hero-title { font-size: 21px; }
  .hero-logo-glow { display: none; }
  .glass-card {
    width: calc(100vw - 32px);
    padding: 28px 24px 28px;
    border-radius: 16px;
  }
  .pulse-ring { display: none; }
  .float-dot { display: none; }
  .orbit-ring { display: none; }
}
</style>

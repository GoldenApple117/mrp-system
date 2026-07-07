import { h } from 'vue'
import { ElNotification } from 'element-plus'

/**
 * 可撤销删除操作
 * @param {Function} deleteFn — 执行删除的异步函数
 * @param {Function} restoreFn — 恢复数据的异步函数（接收备份数据）
 * @param {Object} options — { label: 显示名称, onDeleted: 删除成功回调 }
 * @returns {Promise<void>}
 */
export async function undoableDelete(deleteFn, restoreFn, options = {}) {
  const { label = '数据', undoTimeout = 8000 } = options

  try {
    const backup = await deleteFn()

    ElNotification({
      title: '已删除',
      message: h('div', { style: 'display:flex;align-items:center;gap:8px' }, [
        h('span', `「${label}」已删除`),
        h(
          'el-button',
          {
            type: 'primary',
            link: true,
            size: 'small',
            style: 'margin-left:auto',
            onClick: async () => {
              try {
                await restoreFn(backup)
                ElNotification.closeAll()
                ElNotification({
                  title: '已恢复',
                  message: `「${label}」已恢复`,
                  type: 'success',
                  duration: 2000,
                })
              } catch {
                ElNotification({ title: '恢复失败', message: '请手动重新创建', type: 'error' })
              }
            },
          },
          '撤销',
        ),
      ]),
      type: 'success',
      duration: undoTimeout,
    })

    if (options.onDeleted) options.onDeleted()
  } catch {
    // 删除失败由 api 拦截器统一处理
  }
}

/**
 * 创建一个可撤销的操作
 * 用于需要确认的操作（先确认→执行→可撤销）
 */
export async function confirmThenDelete({ message, title, label }, deleteFn, restoreFn) {
  const { ElMessageBox } = await import('element-plus')
  try {
    await ElMessageBox.confirm(message, title, { type: 'warning' })
    await undoableDelete(deleteFn, restoreFn, { label })
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

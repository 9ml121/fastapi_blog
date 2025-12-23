import { ref, onUnmounted } from 'vue'

/**
 * 设置倒计时
 * @param initialSeconds 倒计时初始秒数，默认60秒
 * @returns
 */
export function useCountdown(initialSeconds = 60) {
  const countdown = ref(0)
  let timer: number | null = null

  // 启动倒计时
  function start() {
    // 防止重复启动：先清理旧定时器
    if (timer) {
      clearInterval(timer)
    }

    countdown.value = initialSeconds
    timer = window.setInterval(() => {
      countdown.value--
      if (countdown.value <= 0 && timer) {
        clearInterval(timer)
        timer = null
      }
    }, 1000)
  }

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  // 返回响应式数据
  return { countdown, start }
}

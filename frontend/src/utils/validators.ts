/**
 * 验证规则配置（与后端保持一致）
 */
export const VALIDATION_RULES = {
  PASSWORD_MIN_LENGTH: 8,
  CODE_LENGTH: 6,
}

/**
 * 邮箱格式验证
 */
export function validateEmail(email: string): string | null {
  if (!email) return '请输入邮箱地址'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return '请输入有效的邮箱地址'
  return null  // null 表示无错误
}

/**
 * 验证码验证（6位数字）
 */
export function validateCode(code: string): string | null {
  if (!code) return '请输入验证码'
  if (!/^\d{6}$/.test(code)) return '验证码为 6 位数字'
  return null
}

/**
 * 密码验证（与后端 validate_password_complexity 保持一致）
 * 规则：至少8位 + 包含数字 + 包含字母
 */
export function validatePassword(password: string): string | null {
  if (!password) return '请输入密码'
  if (password.length < VALIDATION_RULES.PASSWORD_MIN_LENGTH) {
    return `密码至少 ${VALIDATION_RULES.PASSWORD_MIN_LENGTH} 位`
  }
  if (!/\d/.test(password)) return '密码必须包含至少一个数字'
  if (!/[a-zA-Z]/.test(password)) return '密码必须包含至少一个字母'
  return null
}

/**
 * 确认密码验证
 */
export function validateConfirmPassword(password: string, confirmPassword: string): string | null {
  if (!confirmPassword) return '请再次输入密码'
  if (password !== confirmPassword) return '两次密码输入不一致'
  return null
}

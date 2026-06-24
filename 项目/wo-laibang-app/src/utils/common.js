export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }
  if (obj instanceof Date) {
    return new Date(obj.getTime())
  }
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item))
  }
  if (typeof obj === 'object') {
    const cloned = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone(obj[key])
      }
    }
    return cloned
  }
}

export const Validator = {
  isPhone(phone) {
    return /^1[3-9]\d{9}$/.test(phone)
  },

  isEmail(email) {
    return /^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/.test(email)
  },

  isIdCard(idCard) {
    return /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$/.test(idCard)
  },

  isPassword(password, minLen = 6, maxLen = 20) {
    if (!password) return false
    const len = password.length
    return len >= minLen && len <= maxLen
  },

  isPositiveNumber(num) {
    const n = Number(num)
    return !isNaN(n) && n > 0
  },

  isNonNegativeNumber(num) {
    const n = Number(num)
    return !isNaN(n) && n >= 0
  },

  hasValue(val) {
    return val !== null && val !== undefined && val !== ''
  },

  minLength(str, min) {
    return str && str.length >= min
  },

  maxLength(str, max) {
    return !str || str.length <= max
  },

  isUrl(url) {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }
}

export function generateId(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

export function truncateText(text, maxLen, suffix = '...') {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.substring(0, maxLen) + suffix
}

export function getInitials(name) {
  if (!name) return ''
  return name.charAt(0).toUpperCase()
}

export function getAvatarBg(name) {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1',
    '#96CEB4', '#FFEAA7', '#DDA0DD',
    '#98D8C8', '#F7DC6F', '#BB8FCE'
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

export function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function retry(fn, retries = 3, delay = 1000) {
  return new Promise((resolve, reject) => {
    const attempt = (n) => {
      fn()
        .then(resolve)
        .catch((err) => {
          if (n <= 0) {
            reject(err)
          } else {
            setTimeout(() => attempt(n - 1), delay)
          }
        })
    }
    attempt(retries)
  })
}

export default {
  deepClone,
  Validator,
  generateId,
  formatFileSize,
  truncateText,
  getInitials,
  getAvatarBg,
  sleep,
  retry
}

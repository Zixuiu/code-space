const env = import.meta.env

const ENV = {
  DEVELOPMENT: 'development',
  PRODUCTION: 'production'
}

const currentEnv = env.VITE_APP_ENV || ENV.DEVELOPMENT

const toBool = (val, defaultValue = false) => {
  if (val === 'true') return true
  if (val === 'false') return false
  return defaultValue
}

const CONFIG = {
  env: currentEnv,
  isDev: currentEnv === ENV.DEVELOPMENT,
  isProd: currentEnv === ENV.PRODUCTION,

  API_BASE_URL: env.VITE_API_BASE_URL || 'https://api.wolaibang.com',

  WS_BASE_URL: env.VITE_WS_BASE_URL || 'wss://api.wolaibang.com',

  GAODE_MAP_KEY: env.VITE_GAODE_MAP_KEY || '',

  TENCENT_MAP_KEY: env.VITE_TENCENT_MAP_KEY || '',

  USE_MOCK: toBool(env.VITE_USE_MOCK, true),

  requestTimeout: 30000,

  uploadTimeout: 60000,

  wechatAppId: env.VITE_WECHAT_APP_ID || '',

  aliPayAppId: env.VITE_ALIPAY_APP_ID || '',

  JPUSH_APP_KEY: env.VITE_JPUSH_APP_KEY || ''
}

export default CONFIG

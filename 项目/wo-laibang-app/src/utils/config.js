const ENV = {
  DEVELOPMENT: 'development',
  PRODUCTION: 'production'
}

const currentEnv = ENV.DEVELOPMENT

const CONFIG = {
  env: currentEnv,

  API_BASE_URL: currentEnv === ENV.PRODUCTION
    ? 'https://api.wolaibang.com'
    : 'https://api.wolaibang.com',

  WS_BASE_URL: currentEnv === ENV.PRODUCTION
    ? 'wss://api.wolaibang.com'
    : 'wss://api.wolaibang.com',

  GAODE_MAP_KEY: '',

  TENCENT_MAP_KEY: '',

  USE_MOCK: true,

  requestTimeout: 30000,

  uploadTimeout: 60000,

  wechatAppId: '',

  aliPayAppId: '',

  JPUSH_APP_KEY: ''
}

export default CONFIG

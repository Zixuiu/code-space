import { post, get, put } from '@/utils/request'

export const walletApi = {
  getWalletInfo() {
    return get('/api/wallet/info')
  },

  recharge(amount, payMethod) {
    return post('/api/wallet/recharge', { amount, payMethod })
  },

  getRechargeConfig(payMethod) {
    return get('/api/wallet/recharge-config', { payMethod })
  },

  withdraw(amount, account, accountType) {
    return post('/api/wallet/withdraw', { amount, account, accountType })
  },

  transfer(toUserId, amount, remark) {
    return post('/api/wallet/transfer', { toUserId, amount, remark })
  },

  getTransactionList(params) {
    return get('/api/wallet/transactions', params)
  },

  bindAlipay(account, name) {
    return post('/api/wallet/bind-alipay', { account, name })
  },

  bindBankCard(cardNumber, bankName, name) {
    return post('/api/wallet/bind-bank', { cardNumber, bankName, name })
  },

  getBindAccounts() {
    return get('/api/wallet/bind-accounts')
  },

  unbindAccount(accountType) {
    return put('/api/wallet/unbind', { accountType })
  }
}

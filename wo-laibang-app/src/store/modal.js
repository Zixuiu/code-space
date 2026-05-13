import { defineStore } from 'pinia'

export const useModalStore = defineStore('modal', {
	state: () => ({
		confirmVisible: false,
		confirm: {
			title: '提示',
			content: '',
			confirmText: '确定',
			cancelText: '取消',
			onConfirm: null,
			onCancel: null
		}
	}),
	actions: {
		showConfirm(options) {
			this.confirm = {
				title: options.title || '提示',
				content: options.content || '',
				confirmText: options.confirmText || '确定',
				cancelText: options.cancelText || '取消',
				onConfirm: options.onConfirm || null,
				onCancel: options.onCancel || null
			}
			this.confirmVisible = true
		},
		handleConfirm() {
			this.confirmVisible = false
			if (this.confirm.onConfirm) {
				this.confirm.onConfirm()
			}
		},
		handleCancel() {
			this.confirmVisible = false
			if (this.confirm.onCancel) {
				this.confirm.onCancel()
			}
		}
	}
})
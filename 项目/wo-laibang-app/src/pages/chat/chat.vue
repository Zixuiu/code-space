<template>
  <view class="chat-container">
    <view class="header">
      <view class="header-left"></view>
      <view class="header-info">
        <view class="header-title-row">
          <text class="header-title">{{ nickname }}</text>
          <text v-if="roleLabel" class="role-label">{{ roleLabel }}</text>
        </view>
        <text class="header-status">在线</text>
      </view>
      <view class="header-right">
        <view v-if="relatedOrder" class="chat-view-order-btn" @click="viewOrder">
          <text class="chat-view-order-text">订单</text>
        </view>
      </view>
    </view>

		<scroll-view
			class="message-list"
			scroll-y
			:scroll-top="scrollTop"
			scroll-with-animation
			@scrolltoupper="loadMore"
			@scroll="onScroll"
			id="messageList"
		>
			<view v-if="messages.length === 0" class="empty-chat">
				<IconFont name="message" :size="64" class="empty-icon" />
				<text class="empty-text">开始和邻居聊天吧~</text>
			</view>

			<view v-else class="messages-wrapper">
				<view
					v-for="(msg, index) in messages"
					:key="index"
					class="message-item"
					:class="{ 'message-self': msg.isSelf }"
				>
					<template v-if="!msg.isSelf">
						<view class="avatar" :style="{ background: getAvatarBg(nickname) }">
							<text class="avatar-text">{{ nickname.slice(0, 1) }}</text>
						</view>
						<view class="message-content">
							<view v-if="msg.type === 'text'" class="bubble bubble-other">
								<text class="bubble-text">{{ msg.text }}</text>
							</view>
							<view v-else-if="msg.type === 'image'" class="bubble image-bubble">
								<image
									class="chat-image"
									:src="msg.imageUrl"
									mode="widthFix"
									lazy-load="true"
									@click="previewImage(msg.imageUrl)"
								></image>
							</view>
							<text class="message-time">{{ formatTime(msg.time) }}</text>
						</view>
					</template>

					<template v-else>
						<view class="message-content self-content">
							<view v-if="msg.type === 'text'" class="bubble bubble-self">
								<text class="bubble-text self-text">{{ msg.text }}</text>
							</view>
							<view v-else-if="msg.type === 'image'" class="bubble image-bubble self-bubble">
								<image
									class="chat-image"
									:src="msg.imageUrl"
									mode="widthFix"
									lazy-load="true"
									@click="previewImage(msg.imageUrl)"
								></image>
							</view>
							<text class="message-time self-time">{{ formatTime(msg.time) }}</text>
						</view>
						<view class="avatar self-avatar">
							<text class="avatar-text">{{ userStore.currentUser.nickname ? userStore.currentUser.nickname.slice(0, 1) : '我' }}</text>
						</view>
					</template>
				</view>
			</view>
		</scroll-view>

		<view class="input-area" :style="{ paddingBottom: keyboardHeight > 0 ? keyboardHeight + 'px' : 'calc(24rpx + env(safe-area-inset-bottom))' }">
			<view class="input-main">
				<IconFont name="camera" :size="32" class="add-btn" @click="chooseImage" />
				<view class="input-wrapper">
					<input
					class="input-box"
					v-model="inputText"
					type="text"
					placeholder="输入消息..."
					confirm-type="send"
					:adjust-position="false"
					@focus="onInputFocus"
					@blur="onInputBlur"
					@confirm="sendMessage"
				/>
				</view>
				<text class="emoji-btn" @click="toggleEmoji" style="font-size: 40rpx;">😀</text>
				<view
					class="send-btn"
					:class="{ active: inputText.trim() }"
					@click="sendMessage"
				>
					<text class="send-text">发送</text>
				</view>
			</view>
			<view class="emoji-picker" v-if="showEmoji" @click.stop>
				<scroll-view class="emoji-scroll" scroll-y>
					<view class="emoji-grid">
						<text v-for="(emoji, idx) in emojis" :key="idx" class="emoji-item" @click="insertEmoji(emoji)">{{ emoji }}</text>
					</view>
				</scroll-view>
			</view>
		</view>

		<!-- 订单卡片弹窗 -->
		<OrderCardModal
			:visible="orderCardVisible"
			:order="currentOrder"
			@update:visible="orderCardVisible = $event"
			@view-detail="goToOrderDetail"
		/>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
import IconFont from '@/components/icon-font/icon-font.vue'
import websocketService from '@/utils/websocket'
import { getChatKey } from '@/utils/chat'
import OrderCardModal from '@/components/order-card-modal/order-card-modal.vue'

export default {
	components: {
		IconFont,
		OrderCardModal
	},
	setup() {
		const userStore = useUserStore()
		return { userStore }
	},
	data() {
		return {
			userId: '',
			nickname: '',
			inputText: '',
			messages: [],
			scrollTop: 0,
			isAtBottom: true,
			keyboardHeight: 0,
			showEmoji: false,
			emojis: ['😀', '😃', '😄', '😁', '😎', '🤩', '🥳', '😋', '😜', '🤪', '😝', '🤑', '🤗', '🤭', '🤫', '🤔', '👍', '👎', '👏', '🙌', '🧡', '💙', '💚', '💛', '💜', '🧡', '💯', '🔥', '✨', '🌟', '💫', '⭐', '🎉', '🎊', '❤️‍🔥', '😘', '🥰', '😍', '😊', '😗', '😙', '🥹', '😭', '🤯', '🥵', '🥶', '😈', '👿', '💀', '☠️', '👻', '👽', '👾', '🤖', '🎨', '🎭', '🎪', '🎬', '🎤', '🎧', '🎸', '🎹', '🎺', '🎻', '🪘', '🥁', '🎷', '🎵', '🎶', '💃', '🕺', '🎡', '🎢', '🎠', '🏆', '🥇', '🥈', '🥉', '🏅', '🎖️', '🏵️', '🎗️', '🎫', '🎟️', '🎁', '🎀', '🎈', '🎉', '🎊', '✨', '🌟', '💫', '⭐', '🪄', '🔮', '🧿', '💎', '💠', '🔵', '🟢', '🟡', '🔴', '🟣', '🟠', '🟤'],
			relatedOrder: null,
			orderCardVisible: false,
			currentOrder: null
		}
	},
	computed: {
		roleLabel() {
			if (!this.relatedOrder) return ''
			const currentUserId = this.userStore.currentUser?.id
			if (this.relatedOrder.publisher?.id === currentUserId) {
				return '接单人'
			} else if (this.relatedOrder.helper?.id === currentUserId) {
				return '发单人'
			}
			return ''
		}
	},
	onLoad(options) {
		this.userId = options.userId
		this.nickname = options.nickname || '邻居'
		this.loadMessages()
		this.markAsRead()
		this.loadRelatedOrder()
		this.initKeyboardListener()
		this.initWebSocket()
	},
	onShow() {
		this.loadMessages()
		this.markAsRead()
		this.initKeyboardListener()
		this.updateTabBarBadge()
	},
	onUnload() {
		this.removeWebSocketListeners()
		try {
			if (this.keyboardChangeCallback && uni.offKeyboardHeightChange) {
				uni.offKeyboardHeightChange(this.keyboardChangeCallback)
			}
		} catch (e) {
			console.log('移除键盘监听失败', e)
		}
	},
	methods: {
		initWebSocket() {
			websocketService.on('chat_message', this.handleIncomingMessage)
			websocketService.on('connect', this.onWsConnect)
			websocketService.on('disconnect', this.onWsDisconnect)
		},
		removeWebSocketListeners() {
			websocketService.off('chat_message', this.handleIncomingMessage)
			websocketService.off('connect', this.onWsConnect)
			websocketService.off('disconnect', this.onWsDisconnect)
		},
		handleIncomingMessage(payload) {
			if (payload.fromUserId == this.userId) {
				const msg = {
					id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
					type: payload.messageType || 'text',
					text: payload.content,
					imageUrl: payload.imageUrl,
					time: payload.timestamp || Date.now(),
					isSelf: false
				}
				this.messages.push(msg)
				this.saveMessages()
				this.$nextTick(() => {
					this.scrollToBottom(true)
				})
			}
		},
		onWsConnect() {
			console.log('Chat: WebSocket connected')
			this.resendPendingMessages()
		},
		onWsDisconnect() {
			console.log('Chat: WebSocket disconnected')
		},
		initKeyboardListener() {
			this.keyboardChangeCallback = (res) => {
				this.keyboardHeight = res.height
				if (res.height > 0) {
					setTimeout(() => {
						this.scrollToBottom()
					}, 100)
				}
			}
			uni.onKeyboardHeightChange(this.keyboardChangeCallback)
		},
		onInputFocus() {
			setTimeout(() => {
				this.scrollToBottom()
			}, 300)
		},
		loadMessages() {
			try {
				const allMessages = uni.getStorageSync('chatMessages') || {}
				const key = this.getChatKey()
				
				// Check if data is in new format (array under chat key)
				if (Array.isArray(allMessages[key])) {
					this.messages = allMessages[key]
				} else {
					// Old format: individual msg_xxx keys stored directly
					// Migrate: collect all msg_* entries and group by chat key
					const migrated = {}
					const msgKeys = Object.keys(allMessages).filter(k => k.startsWith('msg_'))
					if (msgKeys.length > 0) {
						const myChatKey = this.getChatKey()
						msgKeys.forEach(msgKey => {
							const msg = allMessages[msgKey]
							const senderId = msg.senderId || ''
							const receiverId = msg.receiverId || ''
							const chatK = [senderId, receiverId].sort().join('_')
							if (!migrated[chatK]) migrated[chatK] = []
							migrated[chatK].push(msg)
						})
						// Save migrated data
						Object.keys(migrated).forEach(chatK => {
							allMessages[chatK] = migrated[chatK]
						})
						// Remove old individual msg_* keys
						msgKeys.forEach(k => delete allMessages[k])
						uni.setStorageSync('chatMessages', allMessages)
						this.messages = migrated[myChatKey] || []
					} else {
						this.messages = []
					}
				}
			} catch (e) {
				console.error('加载消息失败:', e)
				this.messages = []
			}
			this.$nextTick(() => {
				this.scrollToBottom(true)
			})
		},
		getChatKey() {
			return getChatKey(this.userStore.currentUser?.id, this.userId)
		},
		saveMessages() {
			try {
				const allMessages = uni.getStorageSync('chatMessages') || {}
				const key = this.getChatKey()
				allMessages[key] = this.messages
				uni.setStorageSync('chatMessages', allMessages)
				this.updateConversation()
			} catch (e) {
				console.error('保存消息失败:', e)
				uni.showToast({ title: '消息保存失败', icon: 'none' })
			}
		},
		updateConversation() {
			try {
				const allConvs = uni.getStorageSync('conversations') || []
				const existingIndex = allConvs.findIndex(c => c.userId == this.userId)
				const lastMsg = this.messages.length > 0 ? this.messages[this.messages.length - 1] : null

				if (existingIndex >= 0) {
					allConvs[existingIndex].lastMessage = lastMsg ? (lastMsg.type === 'text' ? lastMsg.text : '[图片]') : ''
					allConvs[existingIndex].lastTime = Date.now()
					allConvs[existingIndex].unread = 0
					allConvs[existingIndex].online = true
				} else {
					const conv = {
						id: `conv_${this.userId}`,
						userId: this.userId,
						nickname: this.nickname,
						lastMessage: lastMsg ? (lastMsg.type === 'text' ? lastMsg.text : '[图片]') : '',
						lastTime: Date.now(),
						unread: 0,
						online: true
					}
					allConvs.unshift(conv)
				}
				uni.setStorageSync('conversations', allConvs)
			} catch (e) {
				console.error('更新会话失败:', e)
			}
		},
		markAsRead() {
			const allConvs = uni.getStorageSync('conversations') || []
			const index = allConvs.findIndex(c => c.userId == this.userId)
			if (index >= 0) {
				allConvs[index].unread = 0
				uni.setStorageSync('conversations', allConvs)
			}
			uni.$emit('updateMessageBadge')
		},
		toggleEmoji() {
			this.showEmoji = !this.showEmoji
			if (this.showEmoji) {
				this.$nextTick(() => {
					document.activeElement?.blur()
				})
			}
		},
		insertEmoji(emoji) {
			this.inputText += emoji
		},
		sendMessage() {
			if (!this.inputText.trim()) return

			const msg = {
				id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
				type: 'text',
				text: this.inputText.trim(),
				time: Date.now(),
				isSelf: true,
				sendStatus: 'sending'
			}

			this.messages.push(msg)
			this.inputText = ''
			this.saveMessages()
			this.$nextTick(() => {
				this.scrollToBottom(true)
			})

			if (websocketService.isConnected) {
				try {
					websocketService.sendMessage(this.userId, msg.text, 'text')
					msg.sendStatus = 'sent'
				} catch (e) {
					msg.sendStatus = 'failed'
					this.retrySendMessage(msg)
				}
			} else {
				msg.sendStatus = 'offline'
				this.savePendingMessage(msg)
			}
		},
		retrySendMessage(msg) {
			let retryCount = 0
			const maxRetries = 3
			const retryInterval = setInterval(() => {
				if (websocketService.isConnected) {
					try {
						websocketService.sendMessage(this.userId, msg.text, 'text')
						msg.sendStatus = 'sent'
						this.saveMessages()
						clearInterval(retryInterval)
					} catch (e) {
						retryCount++
						if (retryCount >= maxRetries) {
							msg.sendStatus = 'failed'
							this.saveMessages()
							clearInterval(retryInterval)
						}
					}
				} else {
					retryCount++
					if (retryCount >= maxRetries) {
						msg.sendStatus = 'failed'
						this.saveMessages()
						this.savePendingMessage(msg)
						clearInterval(retryInterval)
					}
				}
			}, 2000)
		},
		savePendingMessage(msg) {
			const pending = uni.getStorageSync('pendingMessages') || []
			pending.push({
				...msg,
				targetUserId: this.userId,
				targetNickname: this.nickname
			})
			uni.setStorageSync('pendingMessages', pending)
		},
		resendPendingMessages() {
			const pending = uni.getStorageSync('pendingMessages') || []
			if (pending.length === 0) return
			
			const userPending = pending.filter(m => m.targetUserId === this.userId)
			if (userPending.length === 0) return
			
			userPending.forEach(msg => {
				if (websocketService.isConnected) {
					try {
						websocketService.sendMessage(this.userId, msg.text, 'text')
						msg.sendStatus = 'sent'
					} catch (e) {
						msg.sendStatus = 'failed'
					}
				}
			})
			
			const otherPending = pending.filter(m => m.targetUserId !== this.userId)
			uni.setStorageSync('pendingMessages', otherPending)
		},
		chooseImage() {
			uni.chooseImage({
				count: 1,
				sizeType: ['compressed'],
				sourceType: ['album', 'camera'],
				success: (res) => {
					const tempFilePath = res.tempFilePaths[0]
					this.sendImage(tempFilePath)
				}
			})
		},
		sendImage(imageUrl) {
			const msg = {
				id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
				type: 'image',
				imageUrl: imageUrl,
				time: Date.now(),
				isSelf: true,
				sendStatus: 'sending'
			}

			this.messages.push(msg)
			this.saveMessages()
			this.$nextTick(() => {
				this.scrollToBottom(true)
			})

			if (websocketService.isConnected) {
				try {
					websocketService.sendImageMessage(this.userId, imageUrl)
					msg.sendStatus = 'sent'
				} catch (e) {
					msg.sendStatus = 'failed'
					this.retrySendImage(msg)
				}
			} else {
				msg.sendStatus = 'offline'
				this.savePendingMessage(msg)
			}
		},
		retrySendImage(msg) {
			let retryCount = 0
			const maxRetries = 3
			const retryInterval = setInterval(() => {
				if (websocketService.isConnected) {
					try {
						websocketService.sendImageMessage(this.userId, msg.imageUrl)
						msg.sendStatus = 'sent'
						this.saveMessages()
						clearInterval(retryInterval)
					} catch (e) {
						retryCount++
						if (retryCount >= maxRetries) {
							msg.sendStatus = 'failed'
							this.saveMessages()
							clearInterval(retryInterval)
						}
					}
				} else {
					retryCount++
					if (retryCount >= maxRetries) {
						msg.sendStatus = 'failed'
						this.saveMessages()
						this.savePendingMessage(msg)
						clearInterval(retryInterval)
					}
				}
			}, 2000)
		},
		previewImage(imageUrl) {
			uni.previewImage({
				urls: [imageUrl]
			})
		},
		scrollToBottom(force = false) {
			const query = uni.createSelectorQuery().in(this)
			query.select('.messages-wrapper').boundingClientRect()
			query.selectAll('.message-item').boundingClientRect()
			query.exec((res) => {
				if (res[0] && res[1] && res[1].length > 0) {
					const totalHeight = res[1].reduce((sum, item) => sum + item.height, 0) + (res[1].length - 1) * 16 + 100
					if (force || this.isAtBottom) {
						this.scrollTop = totalHeight + 1000
					} else {
						this.scrollTop = totalHeight
					}
				}
			})
		},
		getAvatarBg(name) {
			const colors = [
				'linear-gradient(135deg, #10B981, #34D399)',
				'linear-gradient(135deg, #3B82F6, #60A5FA)',
				'linear-gradient(135deg, #8B5CF6, #A78BFA)',
				'linear-gradient(135deg, #F59E0B, #FBBF24)',
				'linear-gradient(135deg, #EC4899, #F472B6)'
			]
			let hash = 0
			for (let i = 0; i < name.length; i++) {
				hash = name.charCodeAt(i) + ((hash << 5) - hash)
			}
			return colors[Math.abs(hash) % colors.length]
		},
		onScroll(e) {
			const scrollView = e.detail
			const scrollHeight = scrollView.scrollHeight
			const scrollTop = scrollView.scrollTop
			const clientHeight = scrollView.clientHeight
			this.isAtBottom = (scrollHeight - scrollTop - clientHeight) < 50
		},
		loadMore() {
		},
		formatTime(timestamp) {
			const date = new Date(timestamp)
			const hours = date.getHours().toString().padStart(2, '0')
			const minutes = date.getMinutes().toString().padStart(2, '0')
			return `${hours}:${minutes}`
		},
		loadRelatedOrder() {
			const allConversations = uni.getStorageSync('conversations') || []
			const conv = allConversations.find(c => c.userId == this.userId)
			if (conv && conv.relatedOrder) {
				this.relatedOrder = conv.relatedOrder
			}
		},
		viewOrder() {
			if (this.relatedOrder) {
				this.currentOrder = this.relatedOrder
				this.orderCardVisible = true
			}
		},
		goToOrderDetail() {
			if (this.currentOrder && this.currentOrder.needId) {
				this.orderCardVisible = false
				uni.navigateTo({
					url: `/pages/need-detail/need-detail?id=${this.currentOrder.needId}`
				})
			}
		}
	}
}
</script>

<style scoped>
.chat-container {
	height: 100vh;
	height: 100dvh;
	background: #F8FAFC;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 40rpx 48rpx;
	padding-top: 80rpx;
	background: #FFFFFF;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
	flex-shrink: 0;
}

.header-left {
	width: 88rpx;
}

.header-info {
	flex: 1;
	text-align: center;
}

.header-title-row {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.header-title {
	font-size: 34rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
}

.role-label {
	font-size: 22rpx;
	font-weight: 600;
	padding: 4rpx 16rpx;
	background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
	color: white;
	border-radius: 16rpx;
}

.header-status {
	font-size: 22rpx;
	color: #10B981;
	font-weight: 600;
}

.header-right {
	width: 88rpx;
}

.message-list {
	flex: 1;
	padding: 32rpx 40rpx;
	box-sizing: border-box;
	overflow-y: auto;
	-webkit-overflow-scrolling: touch;
}

.empty-chat {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	flex: 1;
}

.empty-icon {
	margin-bottom: 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.empty-text {
	font-size: 28rpx;
	color: #94A3B8;
}

.messages-wrapper {
	padding-bottom: 40rpx;
}

.message-item {
	display: flex;
	margin-bottom: 40rpx;
	align-items: flex-start;
	justify-content: flex-start;
}

.message-item.message-self {
	justify-content: flex-end;
}

.avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
}

.self-avatar {
	background: linear-gradient(135deg, #10B981, #34D399);
}

.avatar-text {
	font-size: 30rpx;
	font-weight: 700;
	color: #FFFFFF;
}

.message-content {
	max-width: 70%;
	margin: 0 32rpx;
}

.self-content {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}

.bubble {
	border-radius: 40rpx;
	padding: 24rpx 32rpx;
	position: relative;
}

.bubble-other {
	background: #FFFFFF;
	border-bottom-left-radius: 12rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.bubble-self {
	background: linear-gradient(135deg, #10B981, #059669);
	border-bottom-right-radius: 12rpx;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.25);
}

.bubble-text {
	font-size: 30rpx;
	color: #1E293B;
	line-height: 1.5;
}

.self-text {
	color: #FFFFFF;
}

.image-bubble {
	padding: 12rpx;
	background: #FFFFFF;
	border-radius: 32rpx;
}

.self-bubble {
	background: transparent;
}

.chat-image {
	max-width: 400rpx;
	border-radius: 24rpx;
}

.message-time {
	font-size: 22rpx;
	color: #94A3B8;
	margin-top: 12rpx;
	display: block;
}

.self-time {
	text-align: right;
}

.input-area {
	background: #FFFFFF;
	padding: 24rpx 40rpx;
	border-top: 2rpx solid #F1F5F9;
	z-index: 999;
}

.input-main {
	display: flex;
	align-items: center;
	gap: 24rpx;
}

.add-btn {
	width: 80rpx;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	cursor: pointer;
}

.input-wrapper {
	flex: 1;
	background: #F8FAFC;
	border-radius: 44rpx;
	border: 2rpx solid transparent;
	transition: all 0.3s;
	min-height: 88rpx;
	display: flex;
	align-items: center;
}

.input-wrapper:focus-within {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.1);
}

.input-box {
	flex: 1;
	padding: 20rpx 32rpx;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	height: 88rpx;
	line-height: 48rpx;
}

.send-btn {
	width: 88rpx;
	height: 88rpx;
	background: #E2E8F0;
	border-radius: 44rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s;
	flex-shrink: 0;
}

.send-btn.active {
	background: linear-gradient(135deg, #10B981, #059669);
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.send-text {
	font-size: 30rpx;
	font-weight: 700;
	color: #94A3B8;
}

.send-btn.active .send-text {
	color: #FFFFFF;
}

.send-icon {
	color: #FFFFFF;
	display: flex;
	align-items: center;
	justify-content: center;
}

.emoji-btn {
	font-size: 56rpx;
	padding: 16rpx;
	flex-shrink: 0;
}

.emoji-picker {
	background: #FFFFFF;
	border-top: 2rpx solid #E2E8F0;
	padding: 32rpx;
}

.emoji-scroll {
	max-height: 400rpx;
}

.emoji-grid {
	display: grid;
	grid-template-columns: repeat(8, 1fr);
	gap: 16rpx;
}

.emoji-item {
	font-size: 48rpx;
	text-align: center;
	padding: 12rpx;
	border-radius: 16rpx;
	transition: background 0.2s;
}

.emoji-item:active {
	background: #F1F5F9;
}

.chat-view-order-btn {
	background: linear-gradient(135deg, #10B981, #059669);
	padding: 8rpx 20rpx;
	border-radius: 24rpx;
}

.chat-view-order-text {
	color: #FFFFFF;
	font-size: 22rpx;
	font-weight: 600;
}
</style>
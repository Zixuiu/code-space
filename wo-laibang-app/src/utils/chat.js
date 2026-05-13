export function getChatKey(userId1, userId2) {
  const id1 = String(userId1 || 'anonymous')
  const id2 = String(userId2 || 'unknown')
  const ids = [id1, id2].sort()
  return `chat_${ids[0]}_${ids[1]}`
}

export function generateConversationKey(userId1, userId2) {
  return getChatKey(userId1, userId2)
}

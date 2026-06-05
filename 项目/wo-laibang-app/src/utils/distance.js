const EARTH_RADIUS = 6371

function toRad(deg) {
	return deg * (Math.PI / 180)
}

function formatDistance(meters) {
	if (meters < 0) return '距离未知'
	if (meters < 1000) {
		return `${Math.round(meters)}m`
	} else {
		const km = meters / 1000
		return `${km.toFixed(2)}km`
	}
}

function calculateDistance(lat1, lng1, lat2, lng2) {
	if (!lat1 || !lng1 || !lat2 || !lng2) {
		return -1
	}

	const lat1Rad = toRad(lat1)
	const lat2Rad = toRad(lat2)
	const deltaLat = toRad(lat2 - lat1)
	const deltaLng = toRad(lng2 - lng1)

	const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
		Math.cos(lat1Rad) * Math.cos(lat2Rad) *
		Math.sin(deltaLng / 2) * Math.sin(deltaLng / 2)

	const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))

	const distance = EARTH_RADIUS * c * 1000

	return Math.round(distance)
}

function getDistanceText(lat1, lng1, lat2, lng2) {
	const meters = calculateDistance(lat1, lng1, lat2, lng2)
	if (meters < 0) {
		return '距离未知'
	}
	return formatDistance(meters)
}

module.exports = {
	calculateDistance,
	formatDistance,
	getDistanceText,
	EARTH_RADIUS
}

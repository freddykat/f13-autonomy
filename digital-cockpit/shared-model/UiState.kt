package com.f13.cockpit.model

data class F13UiState(
    val vehicle: VehicleState = VehicleState(),
    val navigation: NavigationState = NavigationState(),
    val media: MediaState = MediaState(),
    val phone: PhoneState = PhoneState(),
    val adas: AdasState = AdasState(),
    val preferences: DisplayPreferences = DisplayPreferences()
)

data class VehicleState(
    val timestampMs: Long = 0,
    val speedKph: Double? = null,
    val rpm: Int? = null,
    val gear: String? = null,
    val fuelPercent: Double? = null,
    val outsideTempC: Double? = null,
    val driveMode: DriveMode = DriveMode.UNKNOWN,
    val speedLimitKph: Int? = null,
    val warningIds: List<String> = emptyList(),
    val dataHealthy: Boolean = false
)

enum class DriveMode {
    ECO_PRO,
    COMFORT,
    SPORT,
    SPORT_PLUS,
    UNKNOWN
}

data class NavigationState(
    val sequence: Long = 0,
    val timestampMs: Long = 0,
    val status: NavigationStatus = NavigationStatus.IDLE,
    val destination: String? = null,
    val currentRoad: String? = null,
    val nextRoad: String? = null,
    val maneuver: Maneuver = Maneuver.NONE,
    val maneuverDistanceM: Int? = null,
    val exitNumber: String? = null,
    val roundaboutExit: Int? = null,
    val etaEpochMs: Long? = null,
    val remainingDistanceM: Int? = null,
    val remainingDurationS: Int? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val routePolyline: List<GeoPoint> = emptyList(),
    val lanes: List<LaneGuidance> = emptyList()
)

enum class NavigationStatus {
    IDLE,
    ACTIVE,
    REROUTING,
    ARRIVED
}

enum class Maneuver {
    NONE,
    STRAIGHT,
    TURN_LEFT,
    TURN_RIGHT,
    SLIGHT_LEFT,
    SLIGHT_RIGHT,
    SHARP_LEFT,
    SHARP_RIGHT,
    UTURN_LEFT,
    UTURN_RIGHT,
    MERGE,
    FORK_LEFT,
    FORK_RIGHT,
    RAMP_LEFT,
    RAMP_RIGHT,
    ROUNDABOUT,
    EXIT_ROUNDABOUT,
    DESTINATION
}

data class GeoPoint(
    val lat: Double,
    val lon: Double
)

data class LaneGuidance(
    val directions: List<Maneuver>,
    val recommended: Boolean
)

data class MediaState(
    val sequence: Long = 0,
    val timestampMs: Long = 0,
    val source: MediaSource = MediaSource.NONE,
    val playback: PlaybackState = PlaybackState.STOPPED,
    val title: String? = null,
    val artist: String? = null,
    val album: String? = null,
    val station: String? = null,
    val frequencyMhz: Double? = null,
    val positionMs: Long? = null,
    val durationMs: Long? = null,
    val artworkId: String? = null,
    val canPlayPause: Boolean = false,
    val canNext: Boolean = false,
    val canPrevious: Boolean = false,
    val canSeek: Boolean = false
)

enum class MediaSource {
    NONE,
    SPOTIFY,
    ANDROID_MEDIA,
    BLUETOOTH,
    FM,
    DAB,
    CIC,
    CARPLAY,
    ANDROID_AUTO
}

enum class PlaybackState {
    STOPPED,
    PAUSED,
    PLAYING,
    BUFFERING
}

data class PhoneState(
    val state: CallState = CallState.IDLE,
    val displayName: String? = null,
    val number: String? = null,
    val callDurationS: Int? = null
)

enum class CallState {
    IDLE,
    INCOMING,
    OUTGOING,
    ACTIVE
}

data class AdasState(
    val timestampMs: Long = 0,
    val available: Boolean = false,
    val engaged: Boolean = false,
    val setSpeedKph: Int? = null,
    val leadVisible: Boolean = false,
    val laneLeftVisible: Boolean = false,
    val laneRightVisible: Boolean = false,
    val takeoverRequired: Boolean = false,
    val message: String? = null
)

data class DisplayPreferences(
    val radioNavMode: RadioNavMode = RadioNavMode.FULL,
    val clusterNavMode: ClusterNavMode = ClusterNavMode.CARD,
    val hudNavMode: HudNavMode = HudNavMode.GUIDANCE,
    val clusterMediaMode: ClusterMediaMode = ClusterMediaMode.AUTO,
    val theme: ClusterTheme = ClusterTheme.OEM_PLUS
)

enum class RadioNavMode { FULL, CARD, OFF }
enum class ClusterNavMode { MAP, CARD, OFF }
enum class HudNavMode { GUIDANCE, MINIMAL, OFF }
enum class ClusterMediaMode { AUTO, COMPACT, EXPANDED, OFF }
enum class ClusterTheme { OEM_PLUS, M_PERFORMANCE, M_TRACK, NAV_FOCUS, ADAS_FOCUS, NIGHT }

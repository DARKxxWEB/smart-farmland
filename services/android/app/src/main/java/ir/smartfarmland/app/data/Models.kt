package ir.smartfarmland.app.data

data class AuthTokens(
    val access_token: String,
    val refresh_token: String,
    val token_type: String,
    val expires_in: Long,
)

data class LoginBody(val username: String, val password: String)
data class RefreshBody(val refresh_token: String)
data class LogoutBody(val refresh_token: String)
data class ChangePasswordBody(val old_password: String, val new_password: String)
data class GenerateReportBody(val title: String, val interval: String = "hour")

data class Measurement(
    val metric: String = "",
    val value: Double = 0.0,
    val unit: String = "",
)

data class Summary(
    val reading_count: Int = 0,
    val sensor_count: Int = 0,
    val alert_count: Int = 0,
    val sensors: List<SensorStats> = emptyList(),
)

data class SensorStats(
    val sensor_id: String = "",
    val device_id: String = "",
    val kind: String = "",
    val metrics: List<MetricStats> = emptyList(),
    val last_recorded_at: String? = null,
)

data class MetricStats(
    val metric: String = "",
    val unit: String = "",
    val count: Int = 0,
    val min: Double = 0.0,
    val max: Double = 0.0,
    val avg: Double = 0.0,
    val last: Double = 0.0,
)

data class Reading(
    val id: String = "",
    val device_id: String = "",
    val sensor_id: String = "",
    val recorded_at: String? = null,
    val measurements: List<Measurement> = emptyList(),
    val source: String = "",
)

data class Sensor(
    val sensor_id: String = "",
    val device_id: String = "",
    val kind: String = "",
    val last_recorded_at: String? = null,
    val last_measurements: List<Measurement> = emptyList(),
)

data class Alert(
    val id: String = "",
    val severity: String = "",
    val message: String = "",
    val sensor_id: String = "",
    val device_id: String = "",
    val recorded_at: String? = null,
)

data class Report(
    val id: String = "",
    val title: String = "",
    val generated_by: String = "",
    val generated_at: String? = null,
    val from_time: String? = null,
    val to_time: String? = null,
)

data class UserProfile(
    val id: String = "",
    val username: String = "",
    val role: String = "",
    val is_active: Boolean = false,
)

data class Notification(
    val id: String = "",
    val title: String = "",
    val body: String = "",
    val created_at: String? = null,
    val read_at: String? = null,
)

data class ItemsResponse<T>(
    val items: List<T> = emptyList(),
    val unread_count: Int = 0,
)

data class ChangePasswordResponse(val message: String = "")

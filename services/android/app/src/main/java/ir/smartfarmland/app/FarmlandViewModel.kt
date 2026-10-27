package ir.smartfarmland.app

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import ir.smartfarmland.app.data.Alert
import ir.smartfarmland.app.data.ApiService
import ir.smartfarmland.app.data.createApiService
import ir.smartfarmland.app.data.ChangePasswordBody
import ir.smartfarmland.app.data.GenerateReportBody
import ir.smartfarmland.app.data.LoginBody
import ir.smartfarmland.app.data.Notification
import ir.smartfarmland.app.data.Reading
import ir.smartfarmland.app.data.Report
import ir.smartfarmland.app.data.Sensor
import ir.smartfarmland.app.data.Summary
import ir.smartfarmland.app.data.TokenStore
import ir.smartfarmland.app.data.UserProfile
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException
import org.json.JSONObject

enum class AppPage {
    OVERVIEW,
    READINGS,
    SENSORS,
    REPORTS,
    ALERTS,
    SETTINGS,
    LOGIN,
}

data class AppState(
    val page: AppPage = AppPage.LOGIN,
    val isLoading: Boolean = false,
    val error: String? = null,
    val notice: String? = null,
    val serverUrl: String = "",
    val username: String = "",
    val profile: UserProfile? = null,
    val summary: Summary? = null,
    val readings: List<Reading> = emptyList(),
    val sensors: List<Sensor> = emptyList(),
    val alerts: List<Alert> = emptyList(),
    val notifications: List<Notification> = emptyList(),
    val reports: List<Report> = emptyList(),
)

class FarmlandViewModel(application: Application) : AndroidViewModel(application) {
    private val tokenStore = TokenStore(application)
    private val settings = application.getSharedPreferences("smart_farmland_settings", Context.MODE_PRIVATE)
    private var service: ApiService
    var state = androidx.compose.runtime.mutableStateOf(AppState())
        private set

    init {
        val savedUrl = settings.getString(SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
        service = createApiService(savedUrl, tokenStore)
        state.value = state.value.copy(
            serverUrl = savedUrl,
            page = if (tokenStore.hasSession()) AppPage.OVERVIEW else AppPage.LOGIN,
        )
        if (tokenStore.hasSession()) loadOverview()
    }

    fun saveServerUrl(value: String): Boolean {
        val normalized = value.trim().trimEnd('/')
        val parsed = android.net.Uri.parse(normalized)
        if (parsed.scheme !in setOf("http", "https") || parsed.host.isNullOrBlank()) {
            state.value = state.value.copy(error = "نشانی سرور باید با http:// یا https:// و نام میزبان معتبر وارد شود.")
            return false
        }
        val baseUrl = "$normalized/"
        settings.edit().putString(SERVER_URL, baseUrl).apply()
        service = createApiService(baseUrl, tokenStore)
        state.value = state.value.copy(serverUrl = baseUrl, error = null, notice = "نشانی سرور ذخیره شد.")
        if (tokenStore.hasSession()) loadOverview()
        return true
    }

    fun login(username: String, password: String) {
        runRequest {
            val tokens = service.login(LoginBody(username.trim(), password))
            tokenStore.save(tokens)
            state.value = state.value.copy(
                page = AppPage.OVERVIEW,
                username = username.trim(),
                error = null,
                notice = null,
            )
            refreshOverview()
        }
    }

    fun selectPage(page: AppPage) {
        if (page == AppPage.LOGIN) return
        state.value = state.value.copy(page = page, error = null, notice = null)
        when (page) {
            AppPage.OVERVIEW -> loadOverview()
            AppPage.READINGS -> loadReadings()
            AppPage.SENSORS -> loadSensors()
            AppPage.REPORTS -> loadReports()
            AppPage.ALERTS -> loadAlerts()
            AppPage.SETTINGS -> loadProfile()
            AppPage.LOGIN -> Unit
        }
    }

    fun refresh() {
        when (state.value.page) {
            AppPage.OVERVIEW -> loadOverview()
            AppPage.READINGS -> loadReadings()
            AppPage.SENSORS -> loadSensors()
            AppPage.REPORTS -> loadReports()
            AppPage.ALERTS -> loadAlerts()
            AppPage.SETTINGS -> loadProfile()
            AppPage.LOGIN -> Unit
        }
    }

    fun generateReport() {
        runRequest {
            service.generateReport(GenerateReportBody(title = "گزارش مزرعه"))
            state.value = state.value.copy(notice = "گزارش با موفقیت ایجاد شد.")
            refreshReports()
        }
    }

    fun markNotificationRead(notificationId: String) {
        runRequest {
            val updated = service.markNotificationRead(notificationId)
            state.value = state.value.copy(
                notifications = state.value.notifications.map {
                    if (it.id == updated.id) updated else it
                },
            )
        }
    }

    fun changePassword(oldPassword: String, newPassword: String, confirmation: String) {
        if (newPassword != confirmation) {
            state.value = state.value.copy(error = "رمز عبور جدید و تکرار آن یکسان نیستند.")
            return
        }
        if (!newPassword.matches(Regex("^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{10,}$"))) {
            state.value = state.value.copy(error = "رمز جدید باید حداقل ۱۰ نویسه و شامل حرف کوچک، حرف بزرگ و عدد باشد.")
            return
        }
        runRequest {
            service.changePassword(ChangePasswordBody(oldPassword, newPassword))
            tokenStore.clear()
            state.value = AppState(
                page = AppPage.LOGIN,
                serverUrl = state.value.serverUrl,
                notice = "رمز عبور تغییر کرد؛ برای ادامه دوباره وارد شوید.",
            )
        }
    }

    fun logout() {
        runRequest {
            val refreshToken = tokenStore.refreshToken()
            val logoutError = try {
                if (refreshToken != null) {
                    service.logout(ir.smartfarmland.app.data.LogoutBody(refreshToken))
                }
                null
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                error.localizedMessageForUser()
            } finally {
                tokenStore.clear()
            }
            state.value = AppState(
                page = AppPage.LOGIN,
                serverUrl = state.value.serverUrl,
                notice = if (logoutError == null) {
                    "با موفقیت خارج شدید."
                } else {
                    "از این دستگاه خارج شدید؛ اما ارتباط با سرور برای بستن نشست برقرار نشد."
                },
            )
        }
    }

    fun clearMessages() {
        state.value = state.value.copy(error = null, notice = null)
    }

    private fun loadOverview() {
        runRequest { refreshOverview() }
    }

    private fun loadReadings() = runRequest {
        state.value = state.value.copy(readings = service.latestReadings().items)
    }

    private fun loadSensors() = runRequest {
        state.value = state.value.copy(sensors = service.sensors().items)
    }

    private fun loadReports() = runRequest { refreshReports() }

    private fun loadAlerts() = runRequest {
        val alerts = service.alerts().items
        val notifications = service.notifications().items
        state.value = state.value.copy(alerts = alerts, notifications = notifications)
    }

    private fun loadProfile() = runRequest {
        val profile = service.currentUser()
        state.value = state.value.copy(profile = profile, username = profile.username)
    }

    private suspend fun refreshOverview() {
        val (summary, readings) = coroutineScope {
            val summaryRequest = async { service.summary() }
            val readingsRequest = async { service.latestReadings().items }
            summaryRequest.await() to readingsRequest.await()
        }
        state.value = state.value.copy(summary = summary, readings = readings)
    }

    private suspend fun refreshReports() {
        state.value = state.value.copy(reports = service.reports().items)
    }

    private fun runRequest(action: suspend () -> Unit) {
        viewModelScope.launch {
            state.value = state.value.copy(isLoading = true, error = null, notice = null)
            try {
                action()
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                val isUnauthorized = error is HttpException &&
                    error.code() == 401 &&
                    state.value.page != AppPage.LOGIN
                if (isUnauthorized) tokenStore.clear()
                state.value = state.value.copy(
                    page = if (isUnauthorized) AppPage.LOGIN else state.value.page,
                    error = if (isUnauthorized) {
                        "نشست شما منقضی شده است؛ لطفاً دوباره وارد شوید."
                    } else {
                        error.localizedMessageForUser()
                    },
                )
            } finally {
                state.value = state.value.copy(isLoading = false)
            }
        }
    }

    private fun Exception.localizedMessageForUser(): String = when (this) {
        is HttpException -> {
            val body = response()?.errorBody()?.string()
            val detail = body?.let {
                runCatching {
                    val json = JSONObject(it)
                    json.optString("detail").ifBlank { json.optString("message") }
                }.getOrNull()
            }
            detail?.takeIf(String::isNotBlank) ?: "درخواست با خطای ${code()} مواجه شد."
        }
        is IOException -> "ارتباط با سرور برقرار نشد؛ نشانی سرور و اتصال شبکه را بررسی کنید."
        else -> localizedMessage ?: "عملیات ناموفق بود."
    }

    private companion object {
        const val SERVER_URL = "server_url"
        const val DEFAULT_SERVER_URL = "http://10.0.2.2:8000/"
    }
}

package ir.smartfarmland.app.data

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody

interface ApiService {
    @POST("auth/login")
    suspend fun login(@Body body: LoginBody): AuthTokens

    @POST("auth/logout")
    suspend fun logout(@Body body: LogoutBody): Map<String, Boolean>

    @POST("auth/change-password")
    suspend fun changePassword(@Body body: ChangePasswordBody): ChangePasswordResponse

    @GET("auth/me")
    suspend fun currentUser(): UserProfile

    @GET("bi/summary")
    suspend fun summary(): Summary

    @GET("telemetry/readings/latest")
    suspend fun latestReadings(): ItemsResponse<Reading>

    @GET("telemetry/sensors")
    suspend fun sensors(): ItemsResponse<Sensor>

    @GET("bi/alerts")
    suspend fun alerts(): ItemsResponse<Alert>

    @GET("bi/reports")
    suspend fun reports(): ItemsResponse<Report>

    @POST("bi/reports")
    suspend fun generateReport(@Body body: GenerateReportBody): Report

    @GET("notifications")
    suspend fun notifications(): ItemsResponse<Notification>

    @PATCH("notifications/{id}/read")
    suspend fun markNotificationRead(@Path("id") id: String): Notification
}

fun createApiService(
    baseUrl: String,
    tokenStore: TokenStore,
): ApiService {
    val refreshClient = okhttp3.OkHttpClient.Builder()
        .callTimeout(java.time.Duration.ofSeconds(15))
        .build()

    val client = okhttp3.OkHttpClient.Builder()
        .addInterceptor { chain ->
            val accessToken = tokenStore.accessToken()
            val isAuthEndpoint = chain.request().url.encodedPath.let {
                it.endsWith("/auth/login") ||
                    it.endsWith("/auth/refresh") ||
                    it.endsWith("/auth/logout")
            }
            val request = chain.request().newBuilder()
                .header("Accept", "application/json")
                .apply {
                    if (!accessToken.isNullOrBlank() && !isAuthEndpoint) {
                        header("Authorization", "Bearer $accessToken")
                    }
                }
                .build()
            chain.proceed(request)
        }
        .authenticator { _, response ->
            synchronized(tokenStore) {
                val requestPath = response.request.url.encodedPath
                if (
                    requestPath.endsWith("/auth/login") ||
                    requestPath.endsWith("/auth/refresh") ||
                    requestPath.endsWith("/auth/logout")
                ) {
                    return@synchronized null
                }
                val oldToken = response.request.header("Authorization")
                    ?.removePrefix("Bearer ")
                val currentToken = tokenStore.accessToken()
                if (!currentToken.isNullOrBlank() && currentToken != oldToken) {
                    return@synchronized response.request.newBuilder()
                        .header("Authorization", "Bearer $currentToken")
                        .build()
                }

                val refreshToken = tokenStore.refreshToken() ?: return@synchronized null
                val refreshRequest = okhttp3.Request.Builder()
                    .url("${baseUrl.trimEnd('/')}/api/v1/auth/refresh")
                    .post(
                        com.google.gson.Gson().toJson(RefreshBody(refreshToken))
                            .toRequestBody("application/json; charset=utf-8".toMediaType()),
                    )
                    .build()
                val refreshResponse = try {
                    refreshClient.newCall(refreshRequest).execute()
                } catch (_: java.io.IOException) {
                    return@synchronized null
                }
                refreshResponse.use { refreshed ->
                    if (!refreshed.isSuccessful) {
                        tokenStore.clear()
                        return@synchronized null
                    }
                    val body = refreshed.body?.string() ?: return@synchronized null
                    val tokens = com.google.gson.Gson().fromJson(body, AuthTokens::class.java)
                    if (tokens.access_token.isBlank() || tokens.refresh_token.isBlank()) {
                        tokenStore.clear()
                        return@synchronized null
                    }
                    tokenStore.save(tokens)
                    response.request.newBuilder()
                        .header("Authorization", "Bearer ${tokens.access_token}")
                        .build()
                }
            }
        }
        .callTimeout(java.time.Duration.ofSeconds(30))
        .build()

    val normalizedBaseUrl = baseUrl.trimEnd('/') + "/api/v1/"
    return retrofit2.Retrofit.Builder()
        .baseUrl(normalizedBaseUrl)
        .client(client)
        .addConverterFactory(retrofit2.converter.gson.GsonConverterFactory.create())
        .build()
        .create(ApiService::class.java)
}

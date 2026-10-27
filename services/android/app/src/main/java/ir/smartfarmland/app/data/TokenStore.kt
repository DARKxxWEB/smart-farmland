package ir.smartfarmland.app.data

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class TokenStore(context: Context) {
    private val preferences = EncryptedSharedPreferences.create(
        context,
        "smart_farmland_session",
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    @Synchronized
    fun save(tokens: AuthTokens) {
        preferences.edit()
            .putString(ACCESS_TOKEN, tokens.access_token)
            .putString(REFRESH_TOKEN, tokens.refresh_token)
            .apply()
    }

    @Synchronized
    fun accessToken(): String? = preferences.getString(ACCESS_TOKEN, null)

    @Synchronized
    fun refreshToken(): String? = preferences.getString(REFRESH_TOKEN, null)

    @Synchronized
    fun hasSession(): Boolean = !accessToken().isNullOrBlank()

    @Synchronized
    fun clear() {
        preferences.edit().clear().apply()
    }

    private companion object {
        const val ACCESS_TOKEN = "access_token"
        const val REFRESH_TOKEN = "refresh_token"
    }
}

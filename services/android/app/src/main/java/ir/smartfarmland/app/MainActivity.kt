package ir.smartfarmland.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection

class MainActivity : ComponentActivity() {
    private val viewModel: FarmlandViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MaterialTheme(
                colorScheme = lightColorScheme(
                    primary = Forest,
                    onPrimary = Color.White,
                    secondary = Leaf,
                    onSecondary = Color.White,
                    background = Paper,
                    onBackground = Ink,
                    surface = Color.White,
                    onSurface = Ink,
                    surfaceVariant = Color(0xFFEDF2EA),
                    onSurfaceVariant = Color(0xFF536158),
                    outline = Color(0xFFDCE4DA),
                    error = Color(0xFFB3261E),
                ),
            ) {
                androidx.compose.runtime.CompositionLocalProvider(
                    LocalLayoutDirection provides LayoutDirection.Rtl,
                ) {
                    Surface(
                        modifier = Modifier.fillMaxSize(),
                        color = Paper,
                    ) {
                        FarmlandApp(viewModel)
                    }
                }
            }
        }
    }
}

val Forest = Color(0xFF24563D)
val Leaf = Color(0xFF74A85C)
val Paper = Color(0xFFF5F7F2)
val Ink = Color(0xFF1F2C23)

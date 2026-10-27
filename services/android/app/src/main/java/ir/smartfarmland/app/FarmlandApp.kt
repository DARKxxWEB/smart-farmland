package ir.smartfarmland.app

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.animation.Crossfade
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ListAlt
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.automirrored.filled.ShowChart
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationRail
import androidx.compose.material3.NavigationRailItem
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.ButtonDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material3.ExperimentalMaterial3Api
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale
import ir.smartfarmland.app.data.Alert
import ir.smartfarmland.app.data.Measurement
import ir.smartfarmland.app.data.Notification
import ir.smartfarmland.app.data.Reading
import ir.smartfarmland.app.data.Report
import ir.smartfarmland.app.data.Sensor

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FarmlandApp(viewModel: FarmlandViewModel) {
    val state by viewModel.state
    var showServerDialog by remember { mutableStateOf(false) }

    if (showServerDialog) {
        ServerUrlDialog(
            initialValue = state.serverUrl,
            error = state.error,
            onDismiss = { showServerDialog = false },
            onSave = {
                if (viewModel.saveServerUrl(it)) showServerDialog = false
            },
        )
    }

    if (state.page == AppPage.LOGIN) {
        LoginScreen(
            state = state,
            onLogin = viewModel::login,
            onServerClick = { showServerDialog = true },
            onClearMessages = viewModel::clearMessages,
        )
        return
    }

    BoxWithConstraints(Modifier.fillMaxSize()) {
        val availableWidth = this.maxWidth
        val useRail = availableWidth >= 600.dp
        val contentMaxWidth = if (availableWidth >= 840.dp) 1120.dp else 760.dp

        Scaffold(
            containerColor = Paper,
            topBar = {
                Column {
                    TopAppBar(
                        title = {
                            Column {
                                Text(pageTitle(state.page), fontWeight = FontWeight.Bold, fontSize = 18.sp)
                                Text(
                                    state.profile?.username?.ifBlank { state.username } ?: state.username,
                                    fontSize = 11.sp,
                                    color = Forest,
                                )
                            }
                        },
                        actions = {
                            IconButton(onClick = viewModel::refresh, enabled = !state.isLoading) {
                                Icon(Icons.Default.Refresh, contentDescription = "به‌روزرسانی")
                            }
                            IconButton(onClick = { viewModel.selectPage(AppPage.SETTINGS) }) {
                                Icon(Icons.Default.Settings, contentDescription = "تنظیمات")
                            }
                        }
                    )
                    if (state.isLoading) {
                        LinearProgressIndicator(
                            modifier = Modifier.fillMaxWidth(),
                            color = Forest,
                            trackColor = Color(0xFFE1E9DE),
                        )
                    }
                }
            },
            bottomBar = {
                if (!useRail) {
                    NavigationBar(containerColor = Color.White) {
                        primaryPages.forEach { page ->
                            NavigationItem(
                                label = pageTitle(page),
                                page = page,
                                selectedPage = state.page,
                                icon = pageIcon(page),
                                onSelect = viewModel::selectPage,
                            )
                        }
                    }
                }
            },
        ) { padding ->
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
            ) {
                if (useRail) {
                    NavigationRail(
                        containerColor = Color.White,
                        header = {
                            Icon(
                                Icons.Default.Eco,
                                contentDescription = "هوشمند مزرعه",
                                tint = Forest,
                                modifier = Modifier.padding(vertical = 16.dp).size(28.dp),
                            )
                        },
                    ) {
                        allPages.forEach { page ->
                            NavigationRailItem(
                                selected = state.page == page,
                                onClick = { viewModel.selectPage(page) },
                                icon = { Icon(pageIcon(page), contentDescription = null) },
                                label = { Text(pageTitle(page), fontSize = 10.sp) },
                                alwaysShowLabel = false,
                            )
                        }
                    }
                }
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight()
                        .padding(horizontal = if (availableWidth >= 840.dp) 28.dp else 16.dp)
                        .padding(top = 12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    state.error?.let { MessageCard(it, isError = true) }
                    state.notice?.let { MessageCard(it, isError = false) }
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .widthIn(max = contentMaxWidth)
                            .weight(1f),
                    ) {
                        Crossfade(targetState = state.page, label = "page-navigation") { page ->
                            when (page) {
                                AppPage.OVERVIEW -> OverviewScreen(
                                    state.summary,
                                    state.readings,
                                    state.isLoading,
                                    onNavigate = viewModel::selectPage,
                                )
                                AppPage.READINGS -> ReadingsScreen(state.readings, state.isLoading)
                                AppPage.SENSORS -> SensorsScreen(state.sensors, state.isLoading)
                                AppPage.REPORTS -> ReportsScreen(state.reports, state.isLoading, viewModel::generateReport)
                                AppPage.ALERTS -> AlertsScreen(
                                    state.alerts,
                                    state.notifications,
                                    state.isLoading,
                                    viewModel::markNotificationRead,
                                )
                                AppPage.SETTINGS -> SettingsScreen(
                                    serverUrl = state.serverUrl,
                                    profileName = state.profile?.username.orEmpty(),
                                    profileRole = state.profile?.role.orEmpty(),
                                    isLoading = state.isLoading,
                                    onSaveServer = viewModel::saveServerUrl,
                                    onChangePassword = viewModel::changePassword,
                                    onLogout = viewModel::logout,
                                )
                                AppPage.LOGIN -> Unit
                            }
                        }
                    }
                }
            }
        }
    }
}

private val primaryPages = listOf(
    AppPage.OVERVIEW,
    AppPage.READINGS,
    AppPage.SENSORS,
    AppPage.REPORTS,
    AppPage.ALERTS,
)

private val allPages = primaryPages + AppPage.SETTINGS

private fun pageTitle(page: AppPage): String = when (page) {
    AppPage.OVERVIEW -> "خانه"
    AppPage.READINGS -> "داده‌ها"
    AppPage.SENSORS -> "حسگرها"
    AppPage.REPORTS -> "گزارش"
    AppPage.ALERTS -> "هشدارها"
    AppPage.SETTINGS -> "تنظیمات"
    AppPage.LOGIN -> "ورود"
}

private fun pageIcon(page: AppPage) = when (page) {
    AppPage.OVERVIEW -> Icons.Default.Home
    AppPage.READINGS -> Icons.AutoMirrored.Filled.ShowChart
    AppPage.SENSORS -> Icons.AutoMirrored.Filled.ListAlt
    AppPage.REPORTS -> Icons.Default.Description
    AppPage.ALERTS -> Icons.Default.Notifications
    AppPage.SETTINGS -> Icons.Default.Settings
    AppPage.LOGIN -> Icons.Default.Home
}

@Composable
private fun RowScope.NavigationItem(
    label: String,
    page: AppPage,
    selectedPage: AppPage,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    onSelect: (AppPage) -> Unit,
) {
    NavigationBarItem(
        selected = selectedPage == page,
        onClick = { onSelect(page) },
        icon = { Icon(icon, contentDescription = label) },
        label = { Text(label, fontSize = 10.sp) },
    )
}

@Composable
private fun LoginScreen(
    state: AppState,
    onLogin: (String, String) -> Unit,
    onServerClick: () -> Unit,
    onClearMessages: () -> Unit,
) {
    var username by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    Column(
        modifier = Modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Card(
            modifier = Modifier.fillMaxWidth().widthIn(max = 440.dp),
            shape = RoundedCornerShape(28.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        ) {
            Column(
                modifier = Modifier.padding(horizontal = 24.dp, vertical = 28.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Box(
                    modifier = Modifier
                        .size(72.dp)
                        .clip(RoundedCornerShape(24.dp))
                        .background(Brush.linearGradient(listOf(Forest, Leaf))),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(Icons.Default.Eco, contentDescription = null, tint = Color.White, modifier = Modifier.size(36.dp))
                }
                Spacer(Modifier.height(18.dp))
                Text("هوشمند مزرعه", fontSize = 25.sp, fontWeight = FontWeight.Bold, color = Forest)
                Text(
                    "مدیریت مزرعه، از هر جا",
                    modifier = Modifier.padding(top = 6.dp),
                    color = Color(0xFF68766D),
                    fontSize = 13.sp,
                )
                Spacer(Modifier.height(24.dp))
                state.error?.let { MessageCard(it, isError = true) }
                state.notice?.let { MessageCard(it, isError = false) }
                OutlinedTextField(
                    value = username,
                    onValueChange = { username = it; onClearMessages() },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("نام کاربری") },
                    leadingIcon = { Icon(Icons.Default.AccountCircle, contentDescription = null) },
                    singleLine = true,
                    shape = RoundedCornerShape(14.dp),
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it; onClearMessages() },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("رمز عبور") },
                    leadingIcon = { Icon(Icons.Default.Lock, contentDescription = null) },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    shape = RoundedCornerShape(14.dp),
                )
                Spacer(Modifier.height(18.dp))
                Button(
                    onClick = { onLogin(username, password) },
                    enabled = !state.isLoading && username.isNotBlank() && password.isNotBlank(),
                    modifier = Modifier.fillMaxWidth().height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Forest),
                ) {
                    if (state.isLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            color = Color.White,
                            strokeWidth = 2.dp,
                        )
                    } else {
                        Text("ورود به حساب", fontWeight = FontWeight.SemiBold)
                    }
                }
                TextButton(onClick = onServerClick, modifier = Modifier.padding(top = 8.dp)) {
                    Text("تنظیم نشانی سرور", fontSize = 12.sp)
                }
                Text(
                    state.serverUrl,
                    fontSize = 10.sp,
                    color = Color(0xFF7B857E),
                )
            }
        }
    }
}

@Composable
private fun OverviewScreen(
    summary: ir.smartfarmland.app.data.Summary?,
    readings: List<Reading>,
    loading: Boolean,
    onNavigate: (AppPage) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 14.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            WelcomeCard(onNavigate)
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SummaryCard("حسگرها", summary?.sensor_count, Icons.AutoMirrored.Filled.ListAlt, Modifier.weight(1f))
                SummaryCard("اندازه‌گیری", summary?.reading_count, Icons.AutoMirrored.Filled.ShowChart, Modifier.weight(1f))
                SummaryCard("هشدارها", summary?.alert_count, Icons.Default.Notifications, Modifier.weight(1f))
            }
        }
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                SectionTitle("آخرین اندازه‌گیری‌ها")
                TextButton(onClick = { onNavigate(AppPage.READINGS) }) {
                    Text("مشاهده همه", fontSize = 12.sp)
                }
            }
        }
        if (readings.isEmpty()) {
            item {
                if (loading) LoadingCard()
                else EmptyCard("هنوز داده‌ای برای نمایش ثبت نشده است.")
            }
        } else {
            items(readings.take(8), key = { it.id }) { ReadingCard(it) }
        }
    }
}

@Composable
private fun WelcomeCard(onNavigate: (AppPage) -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Forest),
    ) {
        Row(
            modifier = Modifier
                .background(Brush.horizontalGradient(listOf(Forest, Color(0xFF367451))))
                .padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Column(Modifier.weight(1f)) {
                Text("پایش هوشمند، رشد پایدار", color = Color(0xFFD8EBD1), fontSize = 12.sp)
                Text(
                    "همه‌چیز درباره مزرعه‌ات",
                    color = Color.White,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(top = 7.dp),
                )
                Text(
                    "آخرین داده‌ها و وضعیت حسگرها را یک‌جا ببین.",
                    color = Color(0xFFE5F0E7),
                    fontSize = 12.sp,
                    modifier = Modifier.padding(top = 6.dp),
                )
                TextButton(
                    onClick = { onNavigate(AppPage.SENSORS) },
                    contentPadding = PaddingValues(horizontal = 0.dp, vertical = 4.dp),
                    colors = ButtonDefaults.textButtonColors(contentColor = Color.White),
                ) {
                    Text("رفتن به حسگرها  ←", color = Color.White, fontWeight = FontWeight.SemiBold)
                }
            }
            Icon(Icons.Default.Eco, contentDescription = null, tint = Color(0xFFB9D6A4), modifier = Modifier.size(44.dp))
        }
    }
}

@Composable
private fun SummaryCard(
    title: String,
    value: Int?,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .clip(RoundedCornerShape(11.dp))
                    .background(Color(0xFFEAF3E7)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(icon, contentDescription = null, tint = Forest, modifier = Modifier.size(18.dp))
            }
            Text(
                value?.let(::formatNumber) ?: "—",
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold,
                color = Forest,
            )
            Text(title, fontSize = 10.sp, color = Color(0xFF68766D), maxLines = 1)
        }
    }
}

@Composable
private fun ReadingsScreen(readings: List<Reading>, loading: Boolean) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { SectionTitle("آخرین قرائت هر حسگر") }
        if (readings.isEmpty()) {
            item {
                if (loading) LoadingCard()
                else EmptyCard("هیچ اندازه‌گیری‌ای ثبت نشده است.")
            }
        }
        items(readings, key = { it.id }) { ReadingCard(it) }
    }
}

@Composable
private fun ReadingCard(reading: Reading) {
    DataCard(title = reading.sensor_id.ifBlank { "حسگر" }, subtitle = "دستگاه ${reading.device_id}  ·  ${displayDate(reading.recorded_at)}") {
        MeasurementList(reading.measurements)
    }
}

@Composable
private fun SensorsScreen(sensors: List<Sensor>, loading: Boolean) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(minSize = 280.dp),
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item(span = { GridItemSpan(maxLineSpan) }) { SectionTitle("حسگرهای ثبت‌شده") }
        if (sensors.isEmpty()) {
            item(span = { GridItemSpan(maxLineSpan) }) {
                if (loading) LoadingCard()
                else EmptyCard("هنوز حسگری در سامانه ثبت نشده است.")
            }
        }
        items(sensors, key = { "${it.device_id}-${it.sensor_id}" }) { sensor ->
            DataCard(
                title = sensor.sensor_id,
                subtitle = "دستگاه ${sensor.device_id}  ·  ${sensor.kind}  ·  ${displayDate(sensor.last_recorded_at)}",
            ) {
                if (sensor.last_measurements.isEmpty()) {
                    Text("هنوز اندازه‌گیری‌ای ثبت نشده است.", color = Forest, fontSize = 12.sp)
                } else {
                    MeasurementList(sensor.last_measurements)
                }
            }
        }
    }
}

@Composable
private fun ReportsScreen(reports: List<Report>, loading: Boolean, onGenerate: () -> Unit) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(minSize = 280.dp),
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    SectionTitle("گزارش‌های مزرعه")
                    Text("گزارش بر اساس داده‌های ثبت‌شده", fontSize = 11.sp, color = Forest)
                }
                Button(
                    onClick = onGenerate,
                    enabled = !loading,
                    colors = ButtonDefaults.buttonColors(containerColor = Forest),
                ) {
                    Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(18.dp))
                    Text("ایجاد")
                }
            }
        }
        if (reports.isEmpty()) {
            item(span = { GridItemSpan(maxLineSpan) }) {
                if (loading) LoadingCard()
                else EmptyCard("گزارشی موجود نیست؛ برای ساخت گزارش، دکمه ایجاد را بزنید.")
            }
        }
        items(reports, key = { it.id }) {
            DataCard(title = it.title, subtitle = "تهیه‌شده توسط ${it.generated_by.ifBlank { "مدیر مزرعه" }}  ·  ${displayDate(it.generated_at)}")
        }
    }
}

@Composable
private fun AlertsScreen(
    alerts: List<Alert>,
    notifications: List<Notification>,
    loading: Boolean,
    onMarkRead: (String) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item { SectionTitle("هشدارهای مزرعه") }
        if (alerts.isEmpty()) {
            item {
                if (loading) LoadingCard()
                else EmptyCard("هشداری برای نمایش وجود ندارد.")
            }
        }
        items(alerts, key = { it.id }) { alert ->
            DataCard(
                title = alert.severity.ifBlank { "هشدار" },
                subtitle = "${alert.sensor_id}  ·  ${displayDate(alert.recorded_at)}",
            ) { Text(alert.message, fontSize = 13.sp) }
        }
        item { SectionTitle("اعلان‌ها") }
        if (notifications.isEmpty()) {
            item {
                if (loading) LoadingCard()
                else EmptyCard("اعلانی ثبت نشده است.")
            }
        }
        items(notifications, key = { it.id }) { notification ->
            NotificationCard(notification, onMarkRead)
        }
    }
}

@Composable
private fun NotificationCard(notification: Notification, onMarkRead: (String) -> Unit) {
    DataCard(
        title = notification.title,
        subtitle = displayDate(notification.created_at),
    ) {
        Text(notification.body, fontSize = 13.sp)
        if (notification.read_at == null) {
            TextButton(onClick = { onMarkRead(notification.id) }) {
                Icon(Icons.Default.Check, contentDescription = null, modifier = Modifier.size(16.dp))
                Text("علامت‌گذاری به‌عنوان خوانده‌شده")
            }
        }
    }
}

@Composable
private fun SettingsScreen(
    serverUrl: String,
    profileName: String,
    profileRole: String,
    isLoading: Boolean,
    onSaveServer: (String) -> Boolean,
    onChangePassword: (String, String, String) -> Unit,
    onLogout: () -> Unit,
) {
    var url by remember(serverUrl) { mutableStateOf(serverUrl) }
    var oldPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var confirmation by remember { mutableStateOf("") }
    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SectionTitle("تنظیمات حساب")
        DataCard(
            title = profileName.ifBlank { "حساب کاربری" },
            subtitle = profileRole.ifBlank { "مدیر مزرعه" },
        ) { Icon(Icons.Default.AccountCircle, contentDescription = null, tint = Forest) }
        OutlinedTextField(url, { url = it }, modifier = Modifier.fillMaxWidth(), label = { Text("نشانی سرور") }, singleLine = true)
        OutlinedButton(onClick = { onSaveServer(url) }, modifier = Modifier.fillMaxWidth()) {
            Text("ذخیره نشانی سرور")
        }
        HorizontalDivider()
        Text("تغییر رمز عبور", fontWeight = FontWeight.Bold, color = Forest)
        PasswordField(oldPassword, { oldPassword = it }, "رمز عبور فعلی")
        PasswordField(newPassword, { newPassword = it }, "رمز عبور جدید")
        PasswordField(confirmation, { confirmation = it }, "تکرار رمز عبور جدید")
        Button(
            onClick = { onChangePassword(oldPassword, newPassword, confirmation) },
            enabled = !isLoading,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = Forest),
        ) {
            Icon(Icons.Default.Lock, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("ذخیره رمز جدید")
        }
        OutlinedButton(onClick = onLogout, enabled = !isLoading, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.AutoMirrored.Filled.Logout, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("خروج از حساب")
        }
    }
}

@Composable
private fun PasswordField(value: String, onChange: (String) -> Unit, label: String) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        modifier = Modifier.fillMaxWidth(),
        label = { Text(label) },
        singleLine = true,
        visualTransformation = PasswordVisualTransformation(),
    )
}

@Composable
private fun ServerUrlDialog(
    initialValue: String,
    error: String?,
    onDismiss: () -> Unit,
    onSave: (String) -> Unit,
) {
    var value by remember(initialValue) { mutableStateOf(initialValue) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("نشانی API") },
        text = {
            Column {
                Text("آدرس ریشه سرویس، بدون /api/v1؛ در شبیه‌ساز اندروید معمولاً 10.0.2.2 است.")
                Spacer(Modifier.height(10.dp))
                OutlinedTextField(value, { value = it }, label = { Text("http://10.0.2.2:8000") }, singleLine = true)
                error?.let {
                    Text(
                        it,
                        color = MaterialTheme.colorScheme.error,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                }
            }
        },
        confirmButton = { TextButton(onClick = { onSave(value) }) { Text("ذخیره") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("انصراف") } },
    )
}

@Composable
private fun MeasurementList(measurements: List<Measurement>) {
    Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
        measurements.forEach {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(it.metric, fontSize = 12.sp, color = Forest)
                Text("${formatNumber(it.value)} ${it.unit}".trim(), fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
private fun DataCard(
    title: String,
    subtitle: String,
    content: @Composable () -> Unit = {},
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Text(title, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Color(0xFF1F2C23))
            Text(subtitle, fontSize = 11.sp, color = Color(0xFF6D7A70))
            content()
        }
    }
}

@Composable
private fun SectionTitle(title: String) {
    Text(
        title,
        fontSize = 17.sp,
        fontWeight = FontWeight.Bold,
        color = Color(0xFF1F2C23),
        modifier = Modifier.padding(vertical = 3.dp),
    )
}

@Composable
private fun EmptyCard(message: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(Icons.Default.Eco, contentDescription = null, tint = Leaf, modifier = Modifier.size(30.dp))
            Text(
                message,
                modifier = Modifier.padding(top = 10.dp),
                fontSize = 12.sp,
                color = Color(0xFF68766D),
            )
        }
    }
}

@Composable
private fun LoadingCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(22.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Forest, strokeWidth = 2.dp)
            Spacer(Modifier.width(10.dp))
            Text("در حال دریافت اطلاعات…", fontSize = 12.sp, color = Color(0xFF68766D))
        }
    }
}

@Composable
private fun MessageCard(message: String, isError: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isError) Color(0xFFFFF0EF) else Color(0xFFEAF5E8),
        ),
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                if (isError) Icons.Default.ErrorOutline else Icons.Default.Check,
                contentDescription = null,
                tint = if (isError) Color(0xFFB3261E) else Forest,
            )
            Spacer(Modifier.width(8.dp))
            Text(
                message,
                modifier = Modifier.weight(1f),
                fontSize = 12.sp,
                color = if (isError) Color(0xFF8A2823) else Forest,
            )
        }
    }
}

private val persianDateFormatter = DateTimeFormatter
    .ofPattern("yyyy/MM/dd  HH:mm", Locale.forLanguageTag("fa-IR"))

private fun displayDate(value: String?): String {
    if (value.isNullOrBlank()) return "بدون تاریخ"
    return try {
        Instant.parse(value)
            .atZone(ZoneId.systemDefault())
            .format(persianDateFormatter)
    } catch (_: DateTimeParseException) {
        value.replace('T', ' ').removeSuffix("Z")
    }
}

private fun formatNumber(value: Number): String =
    java.text.NumberFormat.getNumberInstance(Locale.forLanguageTag("fa-IR")).format(value)

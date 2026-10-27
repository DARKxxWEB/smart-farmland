# Smart Farmland Android

Native Android client written in Kotlin and Jetpack Compose. The Persian RTL app
uses the existing gateway API; it does not connect directly to backend services
or databases.

## Features

- Sign in, token refresh, sign out, and encrypted local token storage
- Farm overview, latest readings, sensor catalog, BI alerts, and notifications
- Report listing and generation
- Account profile and password change
- Editable gateway URL
- Adaptive bottom navigation on phones and navigation rail on tablets/foldables
- Responsive sensor/report grids, accessible system-bar insets, and farm branding

## Build

Requirements: JDK 17 or newer and Android SDK Platform 37. The Gradle wrapper
downloads and uses the project's configured Gradle version.

From this directory:

```bash
./gradlew :app:assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

## Connect to the local backend

Start the repository's Docker Compose stack first. The default gateway URL is
`http://10.0.2.2:8000/`, which routes to the host machine from the Android
Studio emulator. The login page and Settings screen can change this URL.

For a physical device connected over USB, forward the gateway port before
opening the app:

```bash
adb reverse tcp:8000 tcp:8000
```

Then set the server URL to `http://127.0.0.1:8000/`. For a production deployment,
use an HTTPS gateway URL. Cleartext HTTP is enabled only in the debug manifest
for local development; release builds require HTTPS.

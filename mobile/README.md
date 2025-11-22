# MavunoSure Mobile App

Android application for Village Agents to capture and verify crop insurance claims.

## Setup

### Prerequisites
- Android Studio Hedgehog (2023.1.1) or later
- JDK 17
- Android SDK with API level 24+ (Android 7.0+)
- Kotlin 1.9+

### Installation

1. Open the project in Android Studio
2. Sync Gradle files
3. Create `local.properties` file with your Android SDK path:
```
sdk.dir=/path/to/Android/sdk
```

4. Build and run on emulator or device

## Project Structure

```
mobile/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/mavunosure/
│   │   │   │   ├── data/          # Data layer (repositories, local DB)
│   │   │   │   ├── domain/        # Domain models and use cases
│   │   │   │   ├── ui/            # UI layer (Compose screens, ViewModels)
│   │   │   │   ├── di/            # Dependency injection (Hilt)
│   │   │   │   ├── network/       # API clients
│   │   │   │   └── MainActivity.kt
│   │   │   ├── res/
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   └── build.gradle.kts
├── build.gradle.kts
└── settings.gradle.kts
```

## Tech Stack

- Language: Kotlin
- UI: Jetpack Compose
- Architecture: MVVM + Clean Architecture
- DI: Hilt
- Database: Room
- Networking: Retrofit + OkHttp
- Camera: CameraX
- ML: TensorFlow Lite
- Location: Google Play Services Location
- Async: Coroutines + Flow
- Background Work: WorkManager

## Features

- Offline-first architecture
- Real-time ML inference with TFLite
- Anti-fraud camera validation
- Encrypted local storage
- Auto-sync when online

## Building

### Debug Build
```bash
./gradlew assembleDebug
```

### Release Build
```bash
./gradlew assembleRelease
```

## Testing

### Unit Tests
```bash
./gradlew test
```

### Instrumented Tests
```bash
./gradlew connectedAndroidTest
```

## TFLite Model

Place the `maize_disease_v1.tflite` model in:
```
app/src/main/assets/maize_disease_v1.tflite
```

Model will be loaded on app startup for real-time inference.

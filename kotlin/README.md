# Timehash Kotlin

Kotlin implementation of Timehash for hierarchical time indexing.

## Installation

### Gradle

```kotlin
dependencies {
    implementation("com.naver:timehash:0.1.0")
}
```

### Maven

```xml
<dependency>
    <groupId>com.naver</groupId>
    <artifactId>timehash</artifactId>
    <version>0.1.0</version>
</dependency>
```

## Usage

```kotlin
import com.naver.timehash.Timehash

// Create Timehash instance with default measures
val th = Timehash()

// Generate query terms for a specific time
val queryTerms = th.getQueryTerms(1430) // 14:30
// Returns: listOf("12", "1214", "121430", "12143030", "1214303030")

// Generate index terms for a time range
val indexTerms = th.getIndexTerms("1140", "2100") // 11:40 - 21:00
// Returns: listOf("08113040", "081145", "12", "16", "2020")

// Custom measures
val customTh = Timehash(listOf(240, 60, 15, 5, 1))
```

## Example

```kotlin
import com.naver.timehash.Timehash

fun main() {
    val th = Timehash()
    
    // Business operating hours: 11:40 AM - 9:00 PM
    val keys = th.getIndexTerms("1140", "2100")
    println("Index keys: $keys")
    // Output: [08113040, 081145, 12, 16, 2020]
    
    // Query: Is business open at 2:30 PM?
    val queryKeys = th.getQueryTerms(1430)
    println("Query keys: $queryKeys")
    // Output: [12, 1214, 121430, 12143030, 1214303030]
    
    // Check if any query key matches any index key
    val isOpen = queryKeys.any { keys.contains(it) }
    println("Business is open: $isOpen")
}
```

## Running Examples

```bash
cd kotlin
./gradlew run --args="com.naver.timehash.example.BasicUsageKt"
```

## Running Tests

```bash
cd kotlin
./gradlew test
```

## API Reference

### `Timehash(measures: List<Int> = DEFAULT_MEASURES)`
Creates a Timehash instance with default measures `[400, 100, 15, 5, 1]` (4h, 1h, 15m, 5m, 1m).

### `getQueryTerms(hhmm: Int): List<String>`
Generates query terms for a specific time.
- **Parameters**: `hhmm` - Time in hhmm format (e.g., 1430 for 14:30)
- **Returns**: List of hierarchical hash keys

### `getIndexTerms(fromTime: String, toTime: String): List<String>`
Generates index terms for a time range.
- **Parameters**: 
  - `fromTime` - Start time in hhmm format string (e.g., "1140")
  - `toTime` - End time in hhmm format string (e.g., "2100")
- **Returns**: List of hierarchical hash keys covering the time range

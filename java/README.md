# Timehash Java

Java implementation of Timehash for hierarchical time indexing.

## Installation

Add to your `pom.xml`:

```xml
<dependency>
    <groupId>com.naver</groupId>
    <artifactId>timehash</artifactId>
    <version>1.0.0</version>
</dependency>
```

Or for Gradle:

```gradle
implementation 'com.naver:timehash:1.0.0'
```

## Usage

```java
import com.naver.timehash.Timehash;
import java.util.List;

// Create Timehash instance with default measures
Timehash th = new Timehash();

// Generate query terms for a specific time
List<String> queryTerms = th.getQueryTerms(1430); // 14:30
// Returns: ["12", "1214", "121430", "12143000", "1214300000"]

// Generate index terms for a time range
List<String> indexTerms = th.getIndexTerms("1140", "2100"); // 11:40 - 21:00
// Returns: ["08113040", "081145", "12", "16", "2020"]

// Custom measures
List<Integer> customMeasures = Arrays.asList(240, 60, 15, 5, 1);
Timehash customTh = new Timehash(customMeasures);
```

## Example

```java
Timehash th = new Timehash();

// Business operating hours: 11:40 AM - 9:00 PM
List<String> keys = th.getIndexTerms("1140", "2100");
System.out.println("Index keys: " + keys);
// Output: [08113040, 081145, 12, 16, 2020]

// Query: Is business open at 2:30 PM?
List<String> queryKeys = th.getQueryTerms(1430);
System.out.println("Query keys: " + queryKeys);
// Output: [12, 1214, 121430, 12143000, 1214300000]

// Check if any query key matches any index key
boolean isOpen = queryKeys.stream().anyMatch(keys::contains);
System.out.println("Business is open: " + isOpen);
```

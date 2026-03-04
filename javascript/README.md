# Timehash JavaScript

JavaScript/TypeScript implementation of Timehash for hierarchical time indexing.

## Installation

### npm

```bash
npm install timehash
```

### Browser

```html
<script src="timehash.js"></script>
```

## Usage

### Node.js / ES6 Modules

```javascript
import Timehash from 'timehash';

// Create Timehash instance with default measures
const th = new Timehash();

// Generate query terms for a specific time
const queryTerms = th.getQueryTerms(1430); // 14:30
// Returns: ['12', '1214', '121430', '12143000', '1214300000']

// Generate index terms for a time range
const indexTerms = th.getIndexTerms('1140', '2100'); // 11:40 - 21:00
// Returns: ['08113040', '081145', '12', '16', '2020']

// Custom measures
const customTh = new Timehash([240, 60, 15, 5, 1]); // 4h, 1h, 15m, 5m, 1m
```

### Browser

```html
<script src="timehash.js"></script>
<script>
const th = new Timehash();
const keys = th.getIndexTerms('1140', '2100');
console.log(keys);
</script>
```

## Example

```javascript
const th = new Timehash();

// Business operating hours: 11:40 AM - 9:00 PM
const keys = th.getIndexTerms('1140', '2100');
console.log('Index keys:', keys);
// Output: ['08113040', '081145', '12', '16', '2020']

// Query: Is business open at 2:30 PM?
const queryKeys = th.getQueryTerms(1430);
console.log('Query keys:', queryKeys);
// Output: ['12', '1214', '121430', '12143000', '1214300000']

// Check if any query key matches any index key
const isOpen = queryKeys.some(qk => keys.includes(qk));
console.log('Business is open:', isOpen);
```

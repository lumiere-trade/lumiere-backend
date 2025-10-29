# TASK 1.5: MESSAGE VALIDATION - TODO

## SESSION DATE: October 29, 2025

---

## ✅ COMPLETED TODAY (Phase 1 - ~3 hours)

### 1. ValidateMessageUseCase Implementation
- ✅ JSON structure validation
- ✅ Message size limits (1MB default, configurable)
- ✅ String length validation (10K chars default)
- ✅ Array size validation (1K items default)
- ✅ Recursive content validation for nested objects
- ✅ Control message detection (ping, pong, subscribe, unsubscribe)
- ✅ Clear, structured error messages
- ✅ ValidationResult dataclass

**Code**: `src/courier/application/use_cases/message_validation/validate_message.py`
**Lines**: ~150 LOC

### 2. Configuration Settings
- ✅ `max_message_size`: 1MB (1_048_576 bytes)
- ✅ `max_string_length`: 10,000 characters
- ✅ `max_array_size`: 1,000 items
- ✅ All settings configurable via YAML/ENV

**Code**: `src/courier/config/settings.py`
**Lines**: +18 LOC

### 3. DI Container Integration
- ✅ ValidateMessageUseCase singleton
- ✅ Configuration-based initialization
- ✅ `validation_failures` statistics counter

**Code**: `src/courier/di/container.py`
**Lines**: +20 LOC

### 4. WebSocket Endpoint Integration
- ✅ Validate all incoming JSON messages
- ✅ Send structured error responses on validation failure
- ✅ Handle control messages (ping, subscribe, unsubscribe)
- ✅ Acknowledge valid non-control messages
- ✅ Maintain legacy ping/pong text support
- ✅ Track validation failures in statistics

**Code**: `src/courier/presentation/api/routes/websocket.py`
**Lines**: +60 LOC

### 5. Error Response Format
```json
{
  "type": "error",
  "code": "VALIDATION_ERROR",
  "message": "Message validation failed",
  "errors": [
    "Message too large: 2000000 bytes (max: 1048576)",
    "String field 'description' too long: 15000 chars (max: 10000)"
  ]
}
```

---

## 📋 REMAINING WORK (Phase 2-3)

### Phase 2: Enhanced Validation & Event Size Limits (1-2 days)

#### 2.1 Event Validation Enhancement
- [ ] Add size limits to ValidateEventUseCase
- [ ] Validate event payload size
- [ ] Validate event metadata size
- [ ] Add event-specific validation rules
- [ ] Track oversized events in statistics

**Files to modify**:
- `src/courier/application/use_cases/validate_event.py`
- `src/courier/presentation/api/routes/publish.py`

**Estimated**: 2-3 hours

#### 2.2 Content Validation Rules
- [ ] Enum value validation (whitelist allowed values)
- [ ] Numeric range validation (min/max values)
- [ ] URL format validation
- [ ] Email format validation (if needed)
- [ ] Custom validation rules per message type

**New files**:
- `src/courier/domain/validation/` (validation rules)
- `src/courier/domain/validation/rules.py`
- `src/courier/domain/validation/validators.py`

**Estimated**: 3-4 hours

#### 2.3 Per-Message-Type Rate Limiting
- [ ] Extend RateLimiter to support per-type limits
- [ ] Configure different limits for different message types
- [ ] Track per-type rate limit violations
- [ ] Add per-type rate limit configuration

**Settings to add**:
```yaml
rate_limit_per_message_type:
  trade: 50        # 50 trade messages per minute
  candles: 100     # 100 candle updates per minute
  strategy: 10     # 10 strategy messages per minute
  default: 30      # default for unspecified types
```

**Files to modify**:
- `src/courier/infrastructure/rate_limiting/rate_limiter.py`
- `src/courier/config/settings.py`
- `src/courier/presentation/api/routes/websocket.py`

**Estimated**: 3-4 hours

---

### Phase 3: Testing & Monitoring (1 day)

#### 3.1 Unit Tests
- [ ] Test ValidateMessageUseCase with various inputs
- [ ] Test size limit enforcement
- [ ] Test string length validation
- [ ] Test array size validation
- [ ] Test nested object validation
- [ ] Test control message detection
- [ ] Test error message generation

**New file**: `tests/unit/application/use_cases/test_validate_message.py`
**Estimated**: 15-20 tests, 2-3 hours

#### 3.2 Integration Tests
- [ ] Test WebSocket validation end-to-end
- [ ] Test oversized message rejection
- [ ] Test malformed JSON handling
- [ ] Test control message handling
- [ ] Test error response format

**New file**: `tests/integration/test_message_validation.py`
**Estimated**: 10-15 tests, 2 hours

#### 3.3 E2E Tests
- [ ] Test WebSocket message validation via Docker
- [ ] Test validation error responses
- [ ] Test validation statistics tracking
- [ ] Test message type validation

**New file**: `tests/e2e/test_message_validation.py`
**Estimated**: 5-8 tests, 2 hours

#### 3.4 Statistics & Monitoring
- [ ] Add validation metrics to /stats endpoint
- [ ] Log validation failures with context
- [ ] Add validation failure breakdown by error type
- [ ] Add validation performance metrics

**Files to modify**:
- `src/courier/presentation/api/routes/health.py`
- `src/courier/di/container.py`

**Estimated**: 1-2 hours

---

## 📊 PROGRESS SUMMARY

### Completed
- **Phase 1**: WebSocket Message Validation ✅
- **Lines of Code**: ~250 LOC
- **Duration**: ~3 hours
- **Tests**: 344/344 passing (100%)

### Remaining
- **Phase 2**: Enhanced Validation & Rate Limiting
  - Event size limits
  - Content validation rules
  - Per-type rate limiting
  - **Estimated**: 8-11 hours (1-1.5 days)

- **Phase 3**: Testing & Monitoring
  - Unit tests (15-20 tests)
  - Integration tests (10-15 tests)
  - E2E tests (5-8 tests)
  - Statistics & monitoring
  - **Estimated**: 7-9 hours (1 day)

### Total Remaining: 15-20 hours (2-2.5 days)

---

## 🎯 NEXT SESSION PLAN

### Option A: Continue with Phase 2 (Recommended)
1. Add event size limits (2-3 hours)
2. Implement content validation rules (3-4 hours)
3. Add per-message-type rate limiting (3-4 hours)

### Option B: Write Tests First (Test-Driven)
1. Write unit tests for ValidateMessageUseCase (2-3 hours)
2. Write integration tests (2 hours)
3. Write E2E tests (2 hours)
4. Then continue with Phase 2

### Option C: Quick Win - Just Testing
1. Complete unit tests for what we have (2-3 hours)
2. Complete integration tests (2 hours)
3. Commit and move to next task

**Recommendation**: Option A - Continue momentum with Phase 2, then do all testing in Phase 3.

---

## 💡 NOTES & CONSIDERATIONS

### Security
- ✅ Size limits prevent DoS attacks
- ✅ Validation prevents malformed data
- ⏳ Need content validation for XSS/injection prevention
- ⏳ Need rate limiting per message type

### Performance
- ✅ Validation happens early (before processing)
- ✅ JSON parsing cached in validation result
- ⏳ Consider validation caching for repeated patterns
- ⏳ Monitor validation performance impact

### User Experience
- ✅ Clear error messages
- ✅ Structured error format
- ⏳ Consider validation error codes/documentation
- ⏳ Consider client-side validation helpers

### Monitoring
- ✅ Validation failure counter
- ⏳ Need validation failure breakdown
- ⏳ Need validation performance metrics
- ⏳ Need alerting on high failure rates

---

## 🔗 RELATED TASKS

### Completed
- ✅ Task 1.2: Event Schema Validation
- ✅ Task 1.3: Rate Limiting
- ✅ Task 1.4: Graceful Shutdown

### In Progress
- 🔄 Task 1.5: Message Validation (Phase 1 Complete)

### Upcoming
- ⏳ Task 1.6: Connection Limits
- ⏳ Task 1.7: Production Logging
- ⏳ Task 1.8: Health Checks

---

## 📈 OVERALL PROGRESS: Task 1.5

**Status**: 35-40% Complete (Phase 1/3)

**Confidence**: High - solid foundation, clear path forward

**Blockers**: None

**ETA to Complete**: 2-2.5 days (15-20 hours)

---

Generated: October 29, 2025

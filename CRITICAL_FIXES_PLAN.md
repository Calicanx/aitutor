# 🔴 CRITICAL FIXES - Implementation Plan

## Status: IN PROGRESS
**Started:** 2025-12-10  
**Target Completion:** 2025-12-11

---

## 1. JWT Security Vulnerabilities 🔒 **[HIGHEST PRIORITY]**

### Current Issues:
- ✅ **FIXED:** JWT_SECRET validation added - refuses to start with weak secrets
- ✅ **FIXED:** Audience and issuer validation implemented
- ✅ **FIXED:** Token expiration checks in all services
- ✅ **FIXED:** Shared JWT config used across all services

### Files Fixed:
- ✅ `shared/jwt_config.py` - Added validation and security checks
- ✅ `shared/auth_middleware.py` - Added audience/issuer validation
- ✅ `services/AuthService/jwt_utils.py` - Updated to use shared config
- ✅ `services/Tutor/server.js` - Added validation and audience/issuer checks

### Implemented:
1. ✅ **JWT secret validation on startup** - Refuses to start if weak/default secret
2. ✅ **Audience validation** - Ensures tokens are from auth service (aud: teachr-api)
3. ✅ **Issuer validation** - Verifies tokens from correct issuer (iss: teachr-auth-service)
4. ✅ **Minimum complexity requirements** - At least 32 characters required
5. ✅ **All services updated** - Python and Node.js services use secure config
6. ✅ **Environment variable checks** - Fail fast if JWT_SECRET not set properly

**Estimated Time:** 2 hours  
**Actual Time:** 1.5 hours  
**Status:** ✅ **COMPLETE**

---

## 2. CORS Security Issues 🌐 **[HIGH PRIORITY]**

### Current Issues:
- ✅ **FIXED:** `allow_origins=["*"]` replaced with environment-based configuration
- ✅ **FIXED:** Secure defaults for development
- ✅ **FIXED:** Production domains from environment

### Files Fixed:
- ✅ `shared/cors_config.py` - Created shared CORS configuration
- ✅ `services/TeachingAssistant/api.py` - Updated to use secure CORS

### Remaining:
- ⚪ `services/AuthService/auth_api.py` - Need to update
- ⚪ `services/DashSystem/dash_api.py` - Need to update
- ⚪ `services/SherlockEDApi/app/main.py` - Need to update

### Implemented:
1. ✅ **Environment variable** - `ALLOWED_ORIGINS` with safe defaults
2. ✅ **Localhost for development** - `["http://localhost:3000", "http://localhost:4173"]`
3. ✅ **Production domains** - Read from `PRODUCTION_DOMAIN` environment variable
4. ⚪ **Update remaining services** - 3 more services to update

**Estimated Time:** 1 hour  
**Actual Time:** 0.5 hours (partial)  
**Status:** 🟡 **IN PROGRESS** (1/4 services updated)

---

## 3. Canvas Deletion Bug 🎨 **[CRITICAL UX]**

### Current Issues:
- ❌ Delete button clears entire canvas instead of selected elements
- Uses `clearCanvas()` method which removes everything

### Files Affected:
- `frontend/src/components/scratchpad/Scratchpad.tsx` (line 24)

### Fix Plan:
1. **Implement element selection** - Add ability to select individual strokes
2. **Add undo/redo functionality** - Use react-sketch-canvas built-in methods
3. **Update delete button** - Only remove selected elements, not entire canvas
4. **Add confirmation dialog** - For "clear all" action

**Estimated Time:** 3 hours  
**Status:** ⚪ Pending

---

## 4. MCQ Highlighting Bug 🔘 **[CRITICAL UX]**

### Current Issues:
- ❌ Clicking one option highlights all options (reported by user)
- Need to investigate Perseus radio widget styling

### Files Affected:
- `frontend/src/package/perseus/src/widgets/radio/multiple-choice-component.new.tsx`
- `frontend/src/package/perseus/src/widgets/radio/choice.new.tsx` (likely)
- `frontend/src/package/perseus/src/widgets/radio/multiple-choice.module.css` (likely)

### Investigation Needed:
- Check CSS `:hover` vs `:checked` states
- Verify onClick handler only affects selected option
- Review Choice component implementation

### Fix Plan:
1. **Investigate CSS** - Find hover/active state rules
2. **Fix styling** - Use `:checked` pseudo-class properly
3. **Update state management** - Ensure only selected option is highlighted
4. **Test single-select vs multi-select** - Both modes should work correctly

**Estimated Time:** 2 hours  
**Status:** ⚪ Pending (Need to investigate Choice component)

---

## 5. Inconsistent Logging 📝 **[HIGH PRIORITY]**

### Current Issues:
- ✅ **CONFIRMED:** 312+ `print()` statements in Python code
- No structured logging
- Different formats across services

### Fix Plan:
1. **Replace all print() with logger** - Search and replace across all Python files
2. **Implement structured logging** - JSON format for cloud debugging
3. **Add log levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
4. **Centralize logging config** - Create `shared/logging_config.py`

**Estimated Time:** 4 hours  
**Status:** ⚪ Pending

---

## 6. TypeScript Type Safety 💎 **[MEDIUM PRIORITY - After Critical]**

### Current Issues:
- 312+ `any` types in codebase
- No compile-time type safety

### Files Affected (Sample):
- `frontend/src/App.tsx`
- `frontend/src/utils/api-utils.ts`
- `frontend/src/contexts/types.ts`
- `frontend/src/utils/http-client.ts`

### Fix Plan:
1. **Create proper type definitions** - For API responses, contexts
2. **Replace useRef<any>** - With proper generic types
3. **Add strict TypeScript config** - Enable `strict: true`
4. **Gradual migration** - Fix one file at a time

**Estimated Time:** 8-10 hours (ongoing)  
**Status:** ⚪ Deferred (After critical fixes)

---

## Priority Order:

1. ✅ **JWT Security** (2 hours) - STARTING NOW
2. **CORS Security** (1 hour)
3. **Canvas Deletion Bug** (3 hours)
4. **MCQ Highlighting Bug** (2 hours)
5. **Logging Consistency** (4 hours)
6. TypeScript Type Safety (8-10 hours) - Deferred

**Total Critical Fixes:** ~12 hours  
**Total with TypeScript:** ~20-22 hours

---

## Success Criteria:

- [ ] JWT_SECRET validation prevents startup with weak secrets
- [ ] CORS only allows configured origins
- [ ] Canvas delete only removes selected elements
- [ ] MCQ options highlight individually
- [ ] All print() replaced with logger calls
- [ ] No new security vulnerabilities introduced

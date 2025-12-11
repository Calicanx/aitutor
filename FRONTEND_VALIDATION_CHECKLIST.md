# Frontend Validation Checklist

**Purpose:** Manually verify all claimed fixes from the Google Sheets feedback and Performance Roadmap document.

**Instructions:** Open the app at http://localhost:3000 and test each item. Mark with [x] when verified working.

---

## HIGH PRIORITY - Spreadsheet Feedback Items

### 1. MCQ Selection Bug (Row 2) - CRITICAL
**Claim:** Fixed - All answers no longer highlight when selecting one
**How to Test:**
- [ ] Navigate to a multiple choice question
- [ ] Click on ONE answer option (e.g., option B)
- [ ] Verify ONLY that option is highlighted/selected
- [ ] Verify other options remain unselected
- [ ] Click a different option and verify selection changes properly

**Files Changed:** `frontend/src/package/perseus/src/widgets/radio/util.ts` (added unique ID generation)

---

### 2. Mobile UI - Icon Positioning (Row 1)
**Claim:** CSS fix for "parent" icon positioning
**How to Test:**
- [ ] Open Chrome DevTools (F12) → Toggle Device Toolbar (Ctrl+Shift+M)
- [ ] Select a mobile device (iPhone 12 Pro)
- [ ] Check if icons have proper spacing from edges
- [ ] Verify no elements are cut off or too close to screen edges

---

### 3. Login & Profiling Expansion (Row 3)
**Claim:** Multi-step onboarding with grade, subjects, interests
**How to Test:**
- [ ] Log out and go to signup page
- [ ] Check if onboarding asks for: Name, Age, Grade level, Subjects, Learning interests
- [ ] Verify form validation works (required fields)

**Status:** ⚠️ May be partially implemented - check SignupForm.tsx

---

### 4. UI/UX Design - Dashboard Sidebar (Row 4)
**Claim:** Simplified aesthetics, dashboard sidebar with progress tracking
**How to Test:**
- [ ] Check if sidebar shows learning progress
- [ ] Verify UI is not overly animated/flashy
- [ ] Look for progress indicators (% complete, skills mastered)

---

### 5. Learning Structure/Path Visibility (Row 5)
**Claim:** Learning path tracking implemented
**How to Test:**
- [ ] Look for a "Learning Path" or "Progress" section
- [ ] Check if topics/skills are displayed with difficulty levels
- [ ] Verify progression is visible

**Endpoint:** `/api/learning-path`

---

### 6. Learning History (Row 6)
**Claim:** Activity logging with timestamps
**How to Test:**
- [ ] Answer a few questions
- [ ] Look for a "History" or "Activity" section
- [ ] Check if completed questions are logged with dates/times

---

### 7. Icon & Layout Problems (Row 7-8)
**Claim:** Fixed click handlers, proper event delegation
**How to Test:**
- [ ] Click on all icons in the UI
- [ ] Verify each icon performs its intended action
- [ ] Check no icons are non-functional

---

### 8. Performance Issues (Row 9)
**Claim:** React Query caching, lazy loading, optimizations
**How to Test:**
- [ ] Open DevTools Network tab
- [ ] Navigate between pages
- [ ] Check if API calls are cached (304 responses, no duplicate calls)
- [ ] Verify page loads feel fast (< 3 seconds)
- [ ] Check console for "API_LATENCY" logs showing < 500ms

**Verification Command:** Look for timing in network tab or console logs

---

### 9. MCQ Interaction & Submission (Row 10)
**Claim:** Working Review and Restart buttons
**How to Test:**
- [ ] Answer some questions
- [ ] Look for "Review" button - click it
- [ ] Verify it shows your answers
- [ ] Look for "Restart" button - click it
- [ ] Verify it resets the session

---

### 10. AI Chat - Text Input & Tooltips (Row 11)
**Claim:** Added text input field, tooltips explaining tools
**How to Test:**
- [ ] Open the AI chat/tutor interface
- [ ] Verify there's a text input field (not just voice)
- [ ] Hover over tools/buttons
- [ ] Check if tooltips appear explaining what each does

---

### 11. Whiteboard - Full Toolset (Row 12)
**Claim:** Excalidraw integration with pen thickness, eraser, colors, undo/redo
**How to Test:**
- [ ] Open the scratchpad/whiteboard
- [ ] Check for pen thickness selector
- [ ] Check for eraser tool
- [ ] Check for color palette
- [ ] Test undo (Ctrl+Z) and redo (Ctrl+Shift+Z)
- [ ] Verify Excalidraw toolbar is visible

**File:** `frontend/src/components/scratchpad/Scratchpad.tsx`

---

## MEDIUM PRIORITY - Spreadsheet Items

### 12. Dark Mode Toggle
**How to Test:**
- [ ] Look for a theme/dark mode toggle in settings or header
- [ ] Click to switch themes
- [ ] Verify colors change appropriately

---

### 13. Keyboard Shortcuts
**How to Test:**
- [ ] Press `?` or look for shortcuts help
- [ ] Test common shortcuts (Esc to close, Enter to submit)

**Status:** ⚠️ May not be implemented

---

### 14. Demo Mode
**How to Test:**
- [ ] Look for "Try Demo" or "Guest Mode" option
- [ ] Verify it works without login

**Status:** ⚠️ May not be implemented

---

## PERFORMANCE ROADMAP ITEMS

### Phase 1: Observability (Should be 100% Complete)

#### Web Vitals (Frontend)
**How to Test:**
- [ ] Open browser DevTools Console
- [ ] Refresh the page
- [ ] Look for Web Vitals logs: LCP, CLS, INP values
- [ ] Verify values appear (e.g., `{name: "LCP", value: 1234}`)

**File:** `frontend/src/reportWebVitals.ts`

---

#### API Timing Middleware (Backend)
**How to Test:**
- [ ] Open DevTools Network tab
- [ ] Make any API call (navigate pages)
- [ ] Click on an API response
- [ ] Check Response Headers for `Server-Timing` header
- [ ] Look at console logs for `API_LATENCY` messages

**Files:** `shared/timing_middleware.py`, Applied to all 3 services

---

### Phase 2: Frontend Foundations

#### Lazy Loading
**How to Test:**
- [ ] Open Network tab
- [ ] Clear cache and reload
- [ ] Navigate to different routes
- [ ] Verify JS chunks load on-demand (not all at once)
- [ ] Look for files like `SidePanel-*.js`, `GradingSidebar-*.js` loading when needed

---

#### Performance Budgets (Lighthouse)
**How to Test (Terminal):**
```bash
cd frontend
npm run perf:lighthouse
```
- [ ] Run command and verify it completes
- [ ] Check if scores meet targets (Performance > 75%)

---

### Phase 7: Infrastructure

#### GZip Compression
**How to Test:**
- [ ] Open Network tab
- [ ] Check API responses
- [ ] Look for `Content-Encoding: gzip` header on responses > 1KB

---

## QUICK CONSOLE TESTS

Run these in browser DevTools Console:

```javascript
// Test 1: Check Web Vitals are reporting
// Look for these in console after page load

// Test 2: Check API response times
// Look for logs like: "API_LATENCY | GET /api/questions/2 | Status: 200 | Time: 337.22ms"

// Test 3: Verify React Query is caching
// Navigate away and back - API calls should not repeat
```

---

## SUMMARY TABLE

| # | Item | Priority | Status | Notes |
|---|------|----------|--------|-------|
| 1 | MCQ Selection Bug | HIGH | [ ] | Test radio buttons |
| 2 | Mobile Icon Position | HIGH | [ ] | Test in mobile view |
| 3 | Login/Profiling | HIGH | [ ] | Check signup flow |
| 4 | Dashboard Sidebar | HIGH | [ ] | Look for progress |
| 5 | Learning Path | HIGH | [ ] | Check visibility |
| 6 | Learning History | HIGH | [ ] | Check activity log |
| 7 | Icon Click Handlers | HIGH | [ ] | Click all icons |
| 8 | Performance | HIGH | [ ] | Check load times |
| 9 | Review/Restart | HIGH | [ ] | Test buttons |
| 10 | AI Chat Input | HIGH | [ ] | Check text field |
| 11 | Whiteboard Tools | HIGH | [ ] | Test Excalidraw |
| 12 | Dark Mode | MED | [ ] | Find toggle |
| 13 | Keyboard Shortcuts | MED | [ ] | Test shortcuts |
| 14 | Demo Mode | MED | [ ] | Find demo option |
| 15 | Web Vitals | PERF | [ ] | Check console |
| 16 | API Timing | PERF | [ ] | Check headers |
| 17 | Lazy Loading | PERF | [ ] | Check chunks |
| 18 | GZip | PERF | [ ] | Check encoding |

---

## KNOWN ISSUES / NOT IMPLEMENTED

Based on documentation review:

1. **Onboarding Tour** - Not implemented
2. **Demo Mode** - Not implemented
3. **Full Keyboard Shortcuts** - Not implemented
4. **Asset Optimization (WebP)** - Not implemented
5. **CDN Caching** - Not implemented (infrastructure)
6. **Phases 3-8 Performance** - Documented only, not implemented

---

## HOW TO REPORT ISSUES

If any item fails validation:

1. Note the item number and description
2. Take a screenshot
3. Copy any console errors
4. Note the steps to reproduce

---

**Last Updated:** December 11, 2025

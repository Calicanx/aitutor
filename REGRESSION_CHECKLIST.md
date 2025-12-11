# Regression Checklist: Critical & Outstanding Items

This checklist focuses on the items marked as "Needs explicit verification" or "Not implemented" in the recent review, along with critical functionality regression checks.

## 🔴 Needs Explicit Verification

### 1. MCQ Highlighting & Selection (Rows 3, 10, 17–20)
*   **Issue:** Radio selection state vs. hover state clarity.
*   **Verification Step:**
    *   Navigate to a question with multiple choice options.
    *   Hover over an option: Should show light gray background (`#f5f5f5`).
    *   **Click** an option: Should show distinct blue background (`#e6f7ff`) and border (`#1890ff`).
    *   **Expected:** Selected state must be visually distinct from hover state.
    *   *Status:* Fix applied in `index.css`. Please verify visually.

### 2. Performance & Optimization (Rows 9, 14, 20)
*   **Issue:** Verification of React Query, memoization, and lazy loading.
*   **Verification Steps:**
    *   **Network:** Open DevTools Network tab. Reload page. Verify `main` bundle is split from vendor chunks.
    *   **Lazy Loading:** Verify code splitting is working (check Network tab for new chunks loading when navigating to `/auth/setup` or clicking on the whiteboard).
    *   **Renders:** Use React DevTools "Highlight updates when components render" to verify `SidePanel` and `RendererComponent` are not re-rendering excessively on typing/hover.

## 🟠 Partially Implemented / Needs Polish

### 3. Profile Transparency (Rows 51–53)
*   **Issue:** Usage of profile data in UI.
*   **Verification Step:**
    *   Check header: Does it say "Test User" (or real name)?
    *   Check dashboard: Does "Current Grade" reflect the user's grade (e.g., Grade 10)?
    *   *Note:* A dedicated "Settings" page is currently **missing**.

## 🟡 Not Implemented / Future Work (Medium Priority)

The following items are confirmed as **Not Implemented** in the current scope. Do not fail regression based on these unless scope changed:

1.  **Onboarding Tour:** No guided tour after signup.
2.  **Demo Mode:** No persistent "Demo" button for non-logged-in users (replaced by dev bypass).
3.  **Keyboard Shortcuts:** No global shortcuts (e.g., `Cmd+Enter` to submit).
4.  **Mobile Responsiveness:** Layout is desktop-optimized; mobile view may be imperfect.
5.  **Dark Mode:** CSS variables exist, but no UI toggle is exposed in the current Header.

## ✅ Critical Functionality Regression (Must Pass)

### 1. Backend Connectivity
*   **Check:** "Journey" tab in sidebar loads data (not "Loading..." forever, no 404s).
*   **Check:** Questions load immediately upon starting.

### 2. Submission Flow
*   **Check:** Answering a question enables "Next".
*   **Check:** "End of Test" screen appears after sample usage.
*   **Check:** "Restart" button resets the test cleanly.
*   **Check:** "Review" button returns to Q1.

### 3. Whiteboard
*   **Check:** Excalidraw loads.
*   **Check:** Drawing works.

---

**Tester Note:** If "MCQ Highlighting" passes, the critical UX blocker is resolved. The "Not Implemented" items should be moved to the backlog or next sprint.

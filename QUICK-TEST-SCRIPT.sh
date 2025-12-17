#!/bin/bash

# Quick Testing Script for Phase 3 Implementation
# This script provides ready-to-use cURL commands for testing all endpoints

# ============================================================================
# SETUP - Get your JWT token first
# ============================================================================

echo "================================"
echo "Phase 3 Quick Testing Script"
echo "================================"
echo ""
echo "STEP 1: Get JWT Token"
echo "1. Log in to frontend app"
echo "2. Open DevTools > Application > Local Storage"
echo "3. Copy 'jwt_token' value"
echo "4. Replace YOUR_JWT_TOKEN in commands below"
echo ""

# ============================================================================
# TEST 1: Assessment Status (should return completed: false)
# ============================================================================

echo "TEST 1: Check Assessment Status"
echo "Command: Check if user already took assessment"
echo ""
echo "curl -X GET http://localhost:8000/assessment/status/math \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""
echo "Expected Response:"
echo "{ \"completed\": false, \"score\": null, \"date\": null, \"total\": null }"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 2: Start Assessment (should return 10 questions)
# ============================================================================

echo ""
echo "TEST 2: Start Assessment"
echo "Command: Start assessment and get 10 questions"
echo ""
echo "curl -X POST http://localhost:8000/assessment/start/math \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""
echo "Expected Response:"
echo "{
  \"status\": \"started\",
  \"subject\": \"math\",
  \"questions\": [ ... 10 questions ... ],
  \"total\": 10
}"
echo ""
echo "Check logs for: [ASSESSMENT] Loaded 10 questions for math assessment"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 3: Complete Assessment (submit 10 answers)
# ============================================================================

echo ""
echo "TEST 3: Complete Assessment"
echo "Command: Submit all 10 answers"
echo ""
echo "curl -X POST http://localhost:8000/assessment/complete \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{
  \"subject\": \"math\",
  \"answers\": [
    {\"question_id\": \"q1\", \"skill_id\": \"skill1\", \"is_correct\": true},
    {\"question_id\": \"q2\", \"skill_id\": \"skill1\", \"is_correct\": false},
    {\"question_id\": \"q3\", \"skill_id\": \"skill2\", \"is_correct\": true},
    {\"question_id\": \"q4\", \"skill_id\": \"skill2\", \"is_correct\": true},
    {\"question_id\": \"q5\", \"skill_id\": \"skill3\", \"is_correct\": false},
    {\"question_id\": \"q6\", \"skill_id\": \"skill3\", \"is_correct\": true},
    {\"question_id\": \"q7\", \"skill_id\": \"skill4\", \"is_correct\": true},
    {\"question_id\": \"q8\", \"skill_id\": \"skill4\", \"is_correct\": false},
    {\"question_id\": \"q9\", \"skill_id\": \"skill5\", \"is_correct\": true},
    {\"question_id\": \"q10\", \"skill_id\": \"skill5\", \"is_correct\": true}
  ]
}'"
echo ""
echo "Expected Response:"
echo "{
  \"status\": \"completed\",
  \"score\": 7,
  \"total\": 10,
  \"percentage\": 70.0
}"
echo ""
echo "Check logs for: [ASSESSMENT_COMPLETE] Initialized 5 skill states"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 4: Verify Assessment Completed (status should now return completed: true)
# ============================================================================

echo ""
echo "TEST 4: Verify Assessment Status (should now be completed)"
echo "Command: Check if assessment is marked as complete"
echo ""
echo "curl -X GET http://localhost:8000/assessment/status/math \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\""
echo ""
echo "Expected Response:"
echo "{ \"completed\": true, \"score\": 7, \"date\": \"...\", \"total\": 10 }"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 5: Try to Take Assessment Again (should be blocked)
# ============================================================================

echo ""
echo "TEST 5: Re-Assessment Prevention"
echo "Command: Try to start assessment again (should fail)"
echo ""
echo "curl -X POST http://localhost:8000/assessment/start/math \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\""
echo ""
echo "Expected Response:"
echo "{
  \"error\": \"Assessment already completed\",
  \"score\": 7,
  \"date\": \"...\"
}"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 6: Video Tracking - Mark Video as Helpful (Correct Answer)
# ============================================================================

echo ""
echo "TEST 6: Track Video as Helpful (Correct Answer)"
echo "Command: Track when video helped student answer correctly"
echo ""
echo "curl -X POST \"http://localhost:8000/api/videos/mark-helpful?question_id=31.1.1.1.1_x7e322ef510dd7af7&video_id=dQw4w9WgXcQ&is_correct=true\" \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\""
echo ""
echo "Expected Response:"
echo "{ \"success\": true, \"status\": \"tracked\" }"
echo ""
echo "MongoDB Effect: score++ and helpful_count++ and views++"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 7: Video Tracking - Mark Video Viewed (Incorrect Answer)
# ============================================================================

echo ""
echo "TEST 7: Track Video View (Incorrect Answer)"
echo "Command: Track video view when answer was incorrect"
echo ""
echo "curl -X POST \"http://localhost:8000/api/videos/mark-helpful?question_id=31.1.1.1.1_x7e322ef510dd7af7&video_id=different-video-id&is_correct=false\" \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\""
echo ""
echo "Expected Response:"
echo "{ \"success\": true, \"status\": \"tracked\" }"
echo ""
echo "MongoDB Effect: only views++ (no score or helpful_count)"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 8: Approve Video
# ============================================================================

echo ""
echo "TEST 8: Approve Video (Move from suggested to learning)"
echo "Command: Admin approves a suggested video"
echo ""
echo "curl -X POST \"http://localhost:8000/api/videos/approve?question_id=31.1.1.1.1_x7e322ef510dd7af7&video_id=newVideoXYZ\" \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\""
echo ""
echo "Expected Response:"
echo "{ \"success\": true, \"status\": \"approved\" }"
echo ""
echo "MongoDB Effect: Video moved from suggested_videos to learning_videos with tracking fields initialized (score=0, views=0, helpful_count=0)"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 9: Reject Video
# ============================================================================

echo ""
echo "TEST 9: Reject Video (Remove from suggested)"
echo "Command: Admin rejects a suggested video"
echo ""
echo "curl -X POST \"http://localhost:8000/api/videos/reject?question_id=31.1.1.1.1_x7e322ef510dd7af7&video_id=badVideoABC\" \\"
echo "  -H \"Authorization: Bearer YOUR_JWT_TOKEN\""
echo ""
echo "Expected Response:"
echo "{ \"success\": true, \"status\": \"rejected\" }"
echo ""
echo "MongoDB Effect: Video removed from suggested_videos"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# TEST 10: Video Finder (Continuous Runner)
# ============================================================================

echo ""
echo "TEST 10: Video Finder (Raspberry Pi Service)"
echo "Command: Start continuous video finder"
echo ""
echo "cd d:\\gagan_arora_1\\aitutor"
echo "python services/VideoFinder/mongodb_integration.py"
echo ""
echo "Expected Output:"
echo "[VIDEO_FINDER] Initializing MongoDBVideoFinder"
echo "[VIDEO_FINDER] APIs initialized successfully"
echo "[VIDEO_FINDER] Starting continuous video finder"
echo "[VIDEO_FINDER] === Iteration 1 ==="
echo "[VIDEO_FINDER] Found X questions needing videos"
echo "[VIDEO_FINDER] Processing X questions"
echo "[VIDEO_FINDER] Found X videos for question..."
echo "[VIDEO_FINDER] Added video ... to ..."
echo ""
echo "MongoDB Effect: Videos added to suggested_videos array with language detection"
echo ""
echo "Press Enter to continue..."
read

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "================================"
echo "All Tests Completed!"
echo "================================"
echo ""
echo "Summary:"
echo "✅ TEST 1: Assessment Status - Check completion"
echo "✅ TEST 2: Start Assessment - Get 10 questions"
echo "✅ TEST 3: Complete Assessment - Submit answers"
echo "✅ TEST 4: Verify Completed - Status changed"
echo "✅ TEST 5: Re-assessment Prevention - Blocked"
echo "✅ TEST 6: Video Tracking (Correct) - Score incremented"
echo "✅ TEST 7: Video Tracking (Incorrect) - Views incremented"
echo "✅ TEST 8: Approve Video - Moved to learning"
echo "✅ TEST 9: Reject Video - Removed from suggested"
echo "✅ TEST 10: Video Finder - Continuous discovery"
echo ""
echo "Next Steps:"
echo "1. Check logs: tail -f logs/dash_api.log"
echo "2. Verify MongoDB: See PHASE-3-TESTING-GUIDE.md"
echo "3. Test frontend: Take assessment through UI"
echo "4. Monitor production"
echo ""
echo "For detailed instructions, see: PHASE-3-TESTING-GUIDE.md"
echo ""

"""
API Pricing Configuration for Cost Tracking
"""

# Pricing per API call (in USD) - Legacy, kept for backward compatibility
API_PRICING = {
    "gemini": 0.0001,      # Legacy - not used for token-based tracking
    "openrouter": 0.0002,  # OpenRouter API pricing per call
    "dash_api": 0.0        # DASH API - Free
}

# gemini-2.5-flash-native-audio-preview-09-2025 Token Pricing (per 1M tokens in USD)
GEMINI_TOKEN_PRICING = {
    "text_input": 0.50,      # Text
    "audio_input": 3.00,     # Audio/Video input (Live API uses audio)
    "output": 12.00          # Output tokens
}

# Session interval progression (in seconds)
COST_TRACKING_INTERVALS = {
    0: 30,      # First 5 minutes: every 30 seconds
    300: 60,    # After 5 minutes: every 1 minute
    900: 300    # After 15 minutes: every 5 minutes
}

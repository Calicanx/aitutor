/**
 * API Key Fetcher for Gemini Live API
 * Fetches API key securely from AuthService backend
 */

import { apiUtils } from '../../lib/api-utils';

const AUTH_SERVICE_URL = import.meta.env.VITE_AUTH_SERVICE_URL || 'http://localhost:8003';

interface GeminiKeyResponse {
  api_key: string;
  model: string;
}

// Cache for API key with expiration
let cachedApiKey: string | null = null;
let cachedModel: string | null = null;
let cacheExpiry: number = 0;
const CACHE_DURATION = 60 * 60 * 1000; // 1 hour

/**
 * Fetch Gemini API key from AuthService
 * Uses JWT authentication to ensure only authenticated users can access
 */
export async function fetchGeminiApiKey(): Promise<{ apiKey: string; model: string }> {
  // Check cache first
  if (cachedApiKey && cachedModel && Date.now() < cacheExpiry) {
    return {
      apiKey: cachedApiKey,
      model: cachedModel,
    };
  }

  try {
    const response = await apiUtils.get(`${AUTH_SERVICE_URL}/auth/gemini-key`);

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication required. Please log in.');
      }
      throw new Error(`Failed to fetch API key: ${response.status} ${response.statusText}`);
    }

    const data: GeminiKeyResponse = await response.json();

    if (!data.api_key) {
      throw new Error('API key not found in response');
    }

    // Cache the result
    cachedApiKey = data.api_key;
    cachedModel = data.model || 'models/gemini-2.5-flash-native-audio-preview-09-2025';
    cacheExpiry = Date.now() + CACHE_DURATION;

    return {
      apiKey: cachedApiKey,
      model: cachedModel,
    };
  } catch (error) {
    console.error('Error fetching Gemini API key:', error);
    throw error;
  }
}

/**
 * Clear cached API key (useful for logout or errors)
 */
export function clearApiKeyCache(): void {
  cachedApiKey = null;
  cachedModel = null;
  cacheExpiry = 0;
}


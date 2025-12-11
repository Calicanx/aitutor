/**
 * Tutor Service - Direct Gemini Live API Integration
 * 
 * This service manages direct connection to Google Gemini Live API
 * from the frontend, eliminating the need for a backend proxy.
 * 
 * This is a separate service component that handles:
 * - Direct WebSocket connection to Gemini Live API
 * - System prompt loading and injection
 * - Message processing and forwarding
 * - Error handling and reconnection logic
 */

import { GoogleGenAI } from '@google/genai';
import { LiveConnectConfig, LiveServerMessage } from '@google/genai';
import { fetchGeminiApiKey, clearApiKeyCache } from './api-key-fetcher';

// System prompt cache
let systemPromptCache: string | null = null;
let systemPromptLoading: Promise<string> | null = null;

/**
 * Load system prompt from public directory
 */
async function loadSystemPrompt(): Promise<string> {
  // Return cached prompt if available
  if (systemPromptCache) {
    return systemPromptCache;
  }

  // If already loading, wait for it
  if (systemPromptLoading) {
    return systemPromptLoading;
  }

  // Start loading
  systemPromptLoading = (async () => {
    try {
      const response = await fetch('/ai_tutor_system_prompt.md');
      if (!response.ok) {
        console.warn('⚠️  Could not load system prompt file, using empty prompt');
        return '';
      }
      const prompt = await response.text();
      systemPromptCache = prompt;
      console.log(`📝 System prompt loaded (${prompt.length} characters)`);
      return prompt;
    } catch (error) {
      console.error('⚠️  Error loading system prompt:', error);
      return '';
    } finally {
      systemPromptLoading = null;
    }
  })();

  return systemPromptLoading;
}

/**
 * Tutor Service Class
 * Manages direct connection to Gemini Live API
 */
export class TutorService {
  private geminiClient: GoogleGenAI | null = null;
  private geminiSession: any = null;
  private apiKey: string | null = null;
  private model: string = 'models/gemini-2.5-flash-native-audio-preview-09-2025';
  private systemPrompt: string = '';

  /**
   * Initialize the service
   * Fetches API key and loads system prompt
   */
  async initialize(): Promise<void> {
    try {
      // Fetch API key from backend
      const { apiKey, model } = await fetchGeminiApiKey();
      this.apiKey = apiKey;
      this.model = model;

      // Load system prompt
      this.systemPrompt = await loadSystemPrompt();

      // Initialize Gemini client
      this.geminiClient = new GoogleGenAI({ apiKey: this.apiKey });
    } catch (error) {
      console.error('❌ Failed to initialize Tutor Service:', error);
      throw error;
    }
  }

  /**
   * Connect to Gemini Live API
   */
  async connect(
    config: LiveConnectConfig,
    callbacks: {
      onopen?: () => void;
      onmessage?: (message: LiveServerMessage) => void;
      onerror?: (error: Error) => void;
      onclose?: (event: { reason?: string }) => void;
    }
  ): Promise<void> {
    if (!this.geminiClient) {
      throw new Error('Tutor Service not initialized. Call initialize() first.');
    }

    // Inject system prompt into config
    const fullConfig: LiveConnectConfig = {
      ...config,
      systemInstruction: config.systemInstruction || this.systemPrompt,
    };

    console.log(`🔗 Connecting to Gemini model: ${this.model}`);
    console.log(`🎤 Voice: ${fullConfig.speechConfig?.voiceConfig?.prebuiltVoiceConfig?.voiceName || 'default'}`);

    try {
      this.geminiSession = await this.geminiClient.live.connect({
        model: this.model,
        config: fullConfig,
        callbacks: {
          onopen: () => {
            console.log('✅ Gemini Live API connected');
            callbacks.onopen?.();
          },
          onmessage: (message: LiveServerMessage) => {
            callbacks.onmessage?.(message);
          },
          onerror: (error: Error) => {
            console.error('❌ Gemini error:', error.message);
            callbacks.onerror?.(error);
          },
          onclose: (event: { reason?: string }) => {
            console.log(`🔌 Gemini connection closed: ${event.reason || 'Unknown reason'}`);
            callbacks.onclose?.(event);
          },
        },
      });

      console.log('✅ Gemini session established');
    } catch (error) {
      console.error('❌ Failed to connect to Gemini:', error);
      throw error;
    }
  }

  /**
   * Disconnect from Gemini Live API
   */
  disconnect(): void {
    if (this.geminiSession) {
      this.geminiSession.close();
      this.geminiSession = null;
      console.log('🔌 Gemini session closed');
    }
  }

  /**
   * Send realtime input (audio/video) to Gemini
   */
  sendRealtimeInput(media: { mimeType: string; data: string }): void {
    if (!this.geminiSession) {
      console.warn('⚠️  Cannot send realtime input: session not connected');
      return;
    }

    try {
      this.geminiSession.sendRealtimeInput({ media });
    } catch (error) {
      console.error('❌ Error sending realtime input:', error);
    }
  }

  /**
   * Send tool response to Gemini
   */
  sendToolResponse(toolResponse: any): void {
    if (!this.geminiSession) {
      console.warn('⚠️  Cannot send tool response: session not connected');
      return;
    }

    try {
      this.geminiSession.sendToolResponse(toolResponse);
    } catch (error) {
      console.error('❌ Error sending tool response:', error);
    }
  }

  /**
   * Send client content (text messages) to Gemini
   */
  sendClientContent(parts: any[], turnComplete: boolean = true): void {
    if (!this.geminiSession) {
      console.warn('⚠️  Cannot send client content: session not connected');
      return;
    }

    try {
      this.geminiSession.sendClientContent({
        turns: parts,
        turnComplete,
      });
    } catch (error) {
      console.error('❌ Error sending client content:', error);
    }
  }

  /**
   * Clear API key cache (useful for logout)
   */
  clearCache(): void {
    clearApiKeyCache();
    this.apiKey = null;
    this.geminiClient = null;
    this.geminiSession = null;
  }

  /**
   * Get current session status
   */
  isConnected(): boolean {
    return this.geminiSession !== null;
  }
}


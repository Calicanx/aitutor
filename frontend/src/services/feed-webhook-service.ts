/**
 * Feed Webhook Service
 * 
 * Centralized service to send feed (media, audio, transcript) to TeachingAssistant webhook
 * with batching and throttling to avoid browser overload.
 */

import { apiUtils } from '../lib/api-utils';
import { LiveServerContent } from '@google/genai';

const TEACHING_ASSISTANT_API_URL = import.meta.env.VITE_TEACHING_ASSISTANT_API_URL || 'http://localhost:8002';

/**
 * Extract transcript text from Gemini content event
 */
export function extractTranscriptFromContent(content: LiveServerContent): string | null {
  const parts = content.modelTurn?.parts || [];
  const textParts = parts
    .filter((p: any) => p.text && p.text.trim().length > 0)
    .map((p: any) => p.text.trim());
  return textParts.length > 0 ? textParts.join(' ') : null;
}

class FeedWebhookService {
  private audioBuffer: string[] = [];
  private lastAudioSend: number = 0;
  private readonly AUDIO_BATCH_INTERVAL = 2000; // 2 seconds
  private audioBatchIntervalId: number | null = null;

  constructor() {
    // Start audio batching interval
    this.startAudioBatching();
  }

  /**
   * Start the audio batching interval
   */
  private startAudioBatching(): void {
    if (this.audioBatchIntervalId !== null) {
      return; // Already started
    }

    this.audioBatchIntervalId = window.setInterval(() => {
      this.flushAudioBuffer();
    }, this.AUDIO_BATCH_INTERVAL);
  }

  /**
   * Stop the audio batching interval
   */
  private stopAudioBatching(): void {
    if (this.audioBatchIntervalId !== null) {
      clearInterval(this.audioBatchIntervalId);
      this.audioBatchIntervalId = null;
    }
    // Flush any remaining audio
    this.flushAudioBuffer();
  }

  /**
   * Flush audio buffer to webhook
   */
  private flushAudioBuffer(): void {
    if (this.audioBuffer.length === 0) {
      return;
    }

    // Combine all audio chunks (for now, just send count - can be enhanced later)
    const audioData = this.audioBuffer.join(''); // In practice, might want to combine differently
    this.audioBuffer = [];
    this.lastAudioSend = Date.now();

    // Send to webhook (fire-and-forget)
    this.sendToWebhook('audio', {
      audio: audioData,
    }).catch((error) => {
      console.error('Failed to send audio batch to webhook:', error);
    });
  }

  /**
   * Send data to webhook endpoint
   */
  private async sendToWebhook(
    type: 'media' | 'audio' | 'transcript' | 'combined',
    data: { media?: string; audio?: string; transcript?: string }
  ): Promise<void> {
    const payload = {
      type,
      timestamp: new Date().toISOString(),
      data,
    };

    await apiUtils.post(`${TEACHING_ASSISTANT_API_URL}/webhook/feed`, payload);
  }

  /**
   * Send media frame to webhook
   */
  async sendMedia(mediaBase64: string): Promise<void> {
    // Fire-and-forget: don't block on webhook call
    this.sendToWebhook('media', {
      media: mediaBase64,
    }).catch((error) => {
      console.error('Failed to send media to webhook:', error);
    });
  }

  /**
   * Send audio chunk to webhook (batched)
   */
  async sendAudio(audioBase64: string): Promise<void> {
    // Add to buffer instead of sending immediately
    this.audioBuffer.push(audioBase64);
  }

  /**
   * Send transcript to webhook immediately
   */
  async sendTranscript(transcript: string): Promise<void> {
    // Fire-and-forget: don't block on webhook call
    this.sendToWebhook('transcript', {
      transcript,
    }).catch((error) => {
      console.error('Failed to send transcript to webhook:', error);
    });
  }

  /**
   * Cleanup: stop intervals and flush buffers
   */
  cleanup(): void {
    this.stopAudioBatching();
  }
}

// Export singleton instance
export const feedWebhookService = new FeedWebhookService();


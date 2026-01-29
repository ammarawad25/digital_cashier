import { describe, it, expect, beforeEach, vi } from 'vitest';
import { formatCurrency, formatDate, truncate, parseApiResponse } from '../utils/formatters';

/**
 * Test Suite: Formatter Utilities
 */
describe('Formatter Utilities', () => {
  describe('formatCurrency', () => {
    it('should format positive numbers as SAR currency', () => {
      const result = formatCurrency(100);
      expect(result).toContain('100');
      expect(result).toContain('SAR');
    });

    it('should handle decimal values', () => {
      const result = formatCurrency(99.99);
      expect(result).toContain('99.99');
    });

    it('should handle zero value', () => {
      const result = formatCurrency(0);
      expect(result).toContain('0');
    });

    it('should handle large numbers', () => {
      const result = formatCurrency(1000000);
      expect(result).toContain('1,000,000');
    });

    it('should format small decimal values', () => {
      const result = formatCurrency(0.50);
      expect(result).toContain('0.50');
    });
  });

  describe('formatDate', () => {
    it('should format date object correctly', () => {
      const date = new Date('2024-01-27T10:30:00');
      const result = formatDate(date);
      expect(result).toContain('January');
      expect(result).toContain('27');
      expect(result).toContain('2024');
    });

    it('should format ISO string correctly', () => {
      const result = formatDate('2024-01-27T10:30:00');
      expect(result).toContain('January');
      expect(result).toContain('27');
      expect(result).toContain('2024');
    });

    it('should include time in formatted string', () => {
      const result = formatDate('2024-01-27T10:30:00');
      expect(result).toMatch(/\d{2}:\d{2}/);
    });
  });

  describe('truncate', () => {
    it('should truncate string longer than specified length', () => {
      const longString = 'This is a very long string that should be truncated';
      const result = truncate(longString, 20);
      expect(result.length).toBeLessThanOrEqual(23); // 20 + '...'
      expect(result).toContain('...');
    });

    it('should not truncate string shorter than specified length', () => {
      const shortString = 'Short';
      const result = truncate(shortString, 20);
      expect(result).toBe('Short');
    });

    it('should use default length of 50', () => {
      const string = 'a'.repeat(60);
      const result = truncate(string);
      expect(result.length).toBeLessThanOrEqual(53); // 50 + '...'
    });

    it('should handle empty string', () => {
      const result = truncate('', 10);
      expect(result).toBe('');
    });

    it('should handle string exactly at length limit', () => {
      const string = 'a'.repeat(20);
      const result = truncate(string, 20);
      expect(result).toBe(string);
    });
  });

  describe('parseApiResponse', () => {
    it('should extract response message', () => {
      const response = {
        response: 'Hello from agent',
        session_id: 'session-123',
        intent: 'greeting',
        confidence: 0.95,
        conversation_state: 'greeting',
      };
      const result = parseApiResponse(response);
      expect(result.message).toBe('Hello from agent');
    });

    it('should extract session ID', () => {
      const response = {
        response: 'Test',
        session_id: 'session-123',
        intent: 'greeting',
        confidence: 0.95,
        conversation_state: 'greeting',
      };
      const result = parseApiResponse(response);
      expect(result.sessionId).toBe('session-123');
    });

    it('should extract intent', () => {
      const response = {
        response: 'Test',
        session_id: 'session-123',
        intent: 'ordering',
        confidence: 0.95,
        conversation_state: 'building_order',
      };
      const result = parseApiResponse(response);
      expect(result.intent).toBe('ordering');
    });

    it('should extract confidence score', () => {
      const response = {
        response: 'Test',
        session_id: 'session-123',
        intent: 'greeting',
        confidence: 0.85,
        conversation_state: 'greeting',
      };
      const result = parseApiResponse(response);
      expect(result.confidence).toBe(0.85);
    });

    it('should extract conversation state', () => {
      const response = {
        response: 'Test',
        session_id: 'session-123',
        intent: 'ordering',
        confidence: 0.95,
        conversation_state: 'building_order',
      };
      const result = parseApiResponse(response);
      expect(result.conversationState).toBe('building_order');
    });

    it('should handle missing response field', () => {
      const response = {
        session_id: 'session-123',
        intent: 'greeting',
        confidence: 0.95,
        conversation_state: 'greeting',
      };
      const result = parseApiResponse(response);
      expect(result.message).toBe('');
    });

    it('should return all fields in parsed response', () => {
      const response = {
        response: 'Test message',
        session_id: 'session-123',
        intent: 'inquiry',
        confidence: 0.92,
        conversation_state: 'browsing_menu',
      };
      const result = parseApiResponse(response);
      expect(result).toEqual({
        message: 'Test message',
        sessionId: 'session-123',
        intent: 'inquiry',
        confidence: 0.92,
        conversationState: 'browsing_menu',
      });
    });
  });
});

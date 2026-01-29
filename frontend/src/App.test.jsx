import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import * as conversationAPI from '../api/conversationAPI';

/**
 * Integration Tests for App Component
 * Tests the complete conversation flow
 */
describe('App Integration Tests', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Clear all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should display phone input on initial load', () => {
    render(<App />);
    expect(screen.getByTestId('phone-input')).toBeTruthy();
    expect(screen.getByTestId('start-session-button')).toBeTruthy();
  });

  it('should start session with phone number', async () => {
    render(<App />);

    const phoneInput = screen.getByTestId('phone-input');
    const startButton = screen.getByTestId('start-session-button');

    fireEvent.change(phoneInput, { target: { value: '+966501234567' } });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeTruthy();
      expect(screen.getByTestId('voice-button')).toBeTruthy();
    });
  });

  it('should send message and display in chat', async () => {
    // Mock API response
    const mockResponse = {
      response: 'Hello! How can I help?',
      session_id: 'session-123',
      intent: 'greeting',
      confidence: 0.95,
      conversation_state: 'greeting',
    };

    vi.spyOn(conversationAPI, 'sendMessage').mockResolvedValueOnce(mockResponse);

    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    // Wait for chat to appear
    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeTruthy();
    });

    // Send message
    fireEvent.change(screen.getByTestId('message-input'), {
      target: { value: 'Hello' },
    });
    fireEvent.click(screen.getByTestId('send-button'));

    // Message should appear in chat
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeTruthy();
    });
  });

  it('should display error message on API failure', async () => {
    const errorMessage = 'Network error';
    vi.spyOn(conversationAPI, 'sendMessage').mockRejectedValueOnce(
      new Error(errorMessage)
    );

    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeTruthy();
    });

    // Send message
    fireEvent.change(screen.getByTestId('message-input'), {
      target: { value: 'Hello' },
    });
    fireEvent.click(screen.getByTestId('send-button'));

    // Error should be displayed
    await waitFor(() => {
      expect(screen.getByTestId('error-alert')).toBeTruthy();
    });
  });

  it('should end session and return to phone input', async () => {
    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeTruthy();
    });

    // End session
    fireEvent.click(screen.getByTestId('end-session-button'));

    // Should return to phone input
    await waitFor(() => {
      expect(screen.getByTestId('phone-input')).toBeTruthy();
    });
  });

  it('should persist session data in localStorage', async () => {
    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeTruthy();
    });

    // Check localStorage
    expect(localStorage.getItem('customerPhone')).toBe('+966501234567');
  });

  it('should display phone number in header after session starts', async () => {
    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    await waitFor(() => {
      expect(screen.getByText(/\+966501234567/)).toBeTruthy();
    });
  });

  it('should handle multiple messages in sequence', async () => {
    const mockResponse = {
      response: 'Response from agent',
      session_id: 'session-123',
      intent: 'greeting',
      confidence: 0.95,
      conversation_state: 'greeting',
    };

    vi.spyOn(conversationAPI, 'sendMessage').mockResolvedValue(mockResponse);

    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeTruthy();
    });

    // Send first message
    fireEvent.change(screen.getByTestId('message-input'), {
      target: { value: 'Hello' },
    });
    fireEvent.click(screen.getByTestId('send-button'));

    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeTruthy();
    });

    // Send second message
    fireEvent.change(screen.getByTestId('message-input'), {
      target: { value: 'Help me' },
    });
    fireEvent.click(screen.getByTestId('send-button'));

    await waitFor(() => {
      expect(screen.getByText('Help me')).toBeTruthy();
    });
  });

  it('should require phone number before allowing messages', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('phone-input')).toBeTruthy();
    });

    // Try to send message without starting session
    fireEvent.change(screen.getByTestId('message-input'), {
      target: { value: 'Hello' },
    });

    // Start button should still require phone number
    const phoneInput = screen.getByTestId('phone-input');
    expect(phoneInput).toHaveValue('');
  });

  it('should show empty chat state initially', () => {
    render(<App />);

    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' },
    });
    fireEvent.click(screen.getByTestId('start-session-button'));

    // Wait and check for empty state
    waitFor(() => {
      expect(screen.getByText(/No messages yet/)).toBeTruthy();
    });
  });
});

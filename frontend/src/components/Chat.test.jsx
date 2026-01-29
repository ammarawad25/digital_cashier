import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatMessage, ChatWindow, ChatInput, VoiceButton } from '../components/Chat';

/**
 * Test Suite: ChatMessage Component
 */
describe('ChatMessage', () => {
  it('should render user message with correct styling', () => {
    render(<ChatMessage message="Hello" isUser={true} />);
    const element = screen.getByTestId('chat-message-user');
    expect(element).toHaveClass('user');
    expect(element).toHaveTextContent('Hello');
  });

  it('should render agent message with correct styling', () => {
    render(<ChatMessage message="Hi there!" isUser={false} />);
    const element = screen.getByTestId('chat-message-agent');
    expect(element).toHaveClass('agent');
    expect(element).toHaveTextContent('Hi there!');
  });

  it('should display timestamp when provided', () => {
    const timestamp = new Date('2024-01-27T10:30:00').toISOString();
    render(<ChatMessage message="Test" isUser={true} timestamp={timestamp} />);
    expect(screen.getByText(/10:30/)).toBeTruthy();
  });

  it('should handle long messages with word breaking', () => {
    const longMessage = 'This is a very long message that should wrap properly without breaking the layout';
    render(<ChatMessage message={longMessage} isUser={true} />);
    expect(screen.getByText(longMessage)).toHaveClass('break-words');
  });
});

/**
 * Test Suite: ChatWindow Component
 */
describe('ChatWindow', () => {
  it('should render empty state when no messages', () => {
    render(<ChatWindow messages={[]} />);
    expect(screen.getByTestId('chat-window')).toHaveTextContent('No messages yet');
  });

  it('should render all messages when provided', () => {
    const messages = [
      { text: 'User message', isUser: true },
      { text: 'Agent response', isUser: false },
    ];
    render(<ChatWindow messages={messages} />);
    expect(screen.getByText('User message')).toBeTruthy();
    expect(screen.getByText('Agent response')).toBeTruthy();
  });

  it('should render messages in correct order', () => {
    const messages = [
      { text: 'First message', isUser: true },
      { text: 'Second message', isUser: false },
      { text: 'Third message', isUser: true },
    ];
    render(<ChatWindow messages={messages} />);
    const chatMessages = screen.getAllByText(/message/);
    expect(chatMessages.length).toBe(3);
  });

  it('should auto-scroll to bottom on new messages', async () => {
    const { rerender } = render(<ChatWindow messages={[]} />);
    const messages = [{ text: 'Message', isUser: true }];

    rerender(<ChatWindow messages={messages} />);

    await waitFor(() => {
      expect(screen.getByText('Message')).toBeTruthy();
    });
  });
});

/**
 * Test Suite: ChatInput Component
 */
describe('ChatInput', () => {
  it('should render input field and send button', () => {
    render(<ChatInput onSendMessage={() => {}} />);
    expect(screen.getByTestId('message-input')).toBeTruthy();
    expect(screen.getByTestId('send-button')).toBeTruthy();
  });

  it('should call onSendMessage when send button is clicked', async () => {
    const mockSend = vi.fn();
    render(<ChatInput onSendMessage={mockSend} />);

    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });

    const button = screen.getByTestId('send-button');
    fireEvent.click(button);

    expect(mockSend).toHaveBeenCalledWith('Test message');
  });

  it('should clear input after sending message', async () => {
    render(<ChatInput onSendMessage={() => {}} />);
    const input = screen.getByTestId('message-input');

    fireEvent.change(input, { target: { value: 'Test message' } });
    expect(input).toHaveValue('Test message');

    fireEvent.click(screen.getByTestId('send-button'));

    await waitFor(() => {
      expect(input).toHaveValue('');
    });
  });

  it('should send message on Enter key press', async () => {
    const mockSend = vi.fn();
    render(<ChatInput onSendMessage={mockSend} />);

    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

    expect(mockSend).toHaveBeenCalledWith('Test message');
  });

  it('should not send message on Shift+Enter', () => {
    const mockSend = vi.fn();
    render(<ChatInput onSendMessage={mockSend} />);

    const input = screen.getByTestId('message-input');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13, shiftKey: true });

    expect(mockSend).not.toHaveBeenCalled();
  });

  it('should disable send button when input is empty', () => {
    render(<ChatInput onSendMessage={() => {}} />);
    const button = screen.getByTestId('send-button');
    expect(button).toBeDisabled();
  });

  it('should disable input and button when disabled prop is true', () => {
    render(<ChatInput onSendMessage={() => {}} disabled={true} />);
    expect(screen.getByTestId('message-input')).toBeDisabled();
    expect(screen.getByTestId('send-button')).toBeDisabled();
  });

  it('should use custom placeholder', () => {
    const customPlaceholder = 'Custom placeholder text';
    render(<ChatInput onSendMessage={() => {}} placeholder={customPlaceholder} />);
    expect(screen.getByPlaceholderText(customPlaceholder)).toBeTruthy();
  });
});

/**
 * Test Suite: VoiceButton Component
 */
describe('VoiceButton', () => {
  it('should render recording button when not recording', () => {
    render(<VoiceButton onStartRecording={() => {}} onStopRecording={() => {}} isRecording={false} />);
    const button = screen.getByTestId('voice-button');
    expect(button).toHaveClass('idle');
    expect(button).toHaveTextContent('🎤');
  });

  it('should render stop button when recording', () => {
    render(<VoiceButton onStartRecording={() => {}} onStopRecording={() => {}} isRecording={true} />);
    const button = screen.getByTestId('voice-button');
    expect(button).toHaveClass('recording');
    expect(button).toHaveTextContent('⏹');
  });

  it('should call onStartRecording when clicked and not recording', () => {
    const mockStart = vi.fn();
    render(<VoiceButton onStartRecording={mockStart} onStopRecording={() => {}} isRecording={false} />);

    fireEvent.click(screen.getByTestId('voice-button'));
    expect(mockStart).toHaveBeenCalled();
  });

  it('should call onStopRecording when clicked and recording', () => {
    const mockStop = vi.fn();
    render(<VoiceButton onStartRecording={() => {}} onStopRecording={mockStop} isRecording={true} />);

    fireEvent.click(screen.getByTestId('voice-button'));
    expect(mockStop).toHaveBeenCalled();
  });

  it('should be disabled when isDisabled prop is true', () => {
    render(<VoiceButton onStartRecording={() => {}} onStopRecording={() => {}} isDisabled={true} />);
    expect(screen.getByTestId('voice-button')).toBeDisabled();
  });

  it('should show transcribing indicator when isTranscribing is true', () => {
    render(
      <VoiceButton
        onStartRecording={() => {}}
        onStopRecording={() => {}}
        isTranscribing={true}
        isRecording={false}
      />
    );
    const button = screen.getByTestId('voice-button');
    expect(button).toHaveTextContent('...');
    expect(button).toBeDisabled();
  });
});

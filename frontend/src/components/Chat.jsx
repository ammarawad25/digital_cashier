import React, { useState, useRef, useEffect } from 'react';
import { formatCurrency } from '../utils/formatters';

/**
 * ReceiptTable Component
 * Displays a formatted receipt table for order confirmations
 */
export const ReceiptTable = ({ receiptData }) => {
  if (!receiptData) return null;

  const { order_number, items = [], subtotal = 0, tax = 0, delivery_fee = 0, total = 0, fulfillment_type = 'delivery' } = receiptData;

  return (
    <div className="receipt-table bg-white border-2 border-gray-300 rounded-lg p-6 my-4 shadow-2xl max-w-md mx-auto" style={{ fontFamily: 'monospace' }}>
      {/* Header */}
      <div className="text-center border-b-2 border-dashed border-gray-800 pb-4 mb-4">
        <h3 className="font-bold text-xl text-black uppercase tracking-tighter">🍔 BURGER RESTAURANT 🍔</h3>
        <p className="text-sm text-gray-800 mt-2 font-black tracking-tighter">ORDER RECEIPT</p>
        <div className="flex justify-center gap-4 mt-3">
          <span className="text-2xl">🍔</span>
          <span className="text-2xl">🍔</span>
        </div>
        <p className="text-xs font-black text-black mt-4 uppercase tracking-widest border border-black inline-block px-2 py-1">#{order_number}</p>
        <p className="text-[10px] text-gray-900 mt-2 font-bold">{new Date().toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}</p>
        <p className="text-[10px] text-gray-900 mt-1 font-black uppercase tracking-widest">{fulfillment_type === 'delivery' ? '🚚 Delivery' : '🚗 Drive-Thru Pickup'}</p>
      </div>

      {/* Items */}
      <div className="border-b-2 border-dashed border-gray-800 pb-4 mb-4">
        <table className="w-full text-[11px] text-black border-collapse">
          <thead>
            <tr className="border-b-2 border-gray-800 font-black">
              <th className="text-left py-2 uppercase tracking-tighter">Item Description</th>
              <th className="text-center py-2 px-2">QTY</th>
              <th className="text-right py-2 px-2">PRICE</th>
              <th className="text-right py-2">TOTAL</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index} className="border-b border-gray-300">
                <td className="text-left py-3 pr-2">
                  <div className="font-black text-xs uppercase leading-tight">{item.arabic_name || item.name}</div>
                </td>
                <td className="text-center py-3 px-2 font-bold">x{item.quantity}</td>
                <td className="text-right py-3 px-2 font-mono">{formatCurrency(item.price)}</td>
                <td className="text-right py-3 font-black font-mono">{formatCurrency(item.price * item.quantity)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Totals */}
      <div className="space-y-2 text-xs text-black font-bold">
        <div className="flex justify-between">
          <span className="uppercase tracking-tighter">Gross Subtotal:</span>
          <span className="font-mono">{formatCurrency(subtotal)}</span>
        </div>
        {tax > 0 && (
          <div className="flex justify-between text-gray-800">
            <span className="uppercase tracking-tighter">VAT (15%):</span>
            <span className="font-mono">{formatCurrency(tax)}</span>
          </div>
        )}
        {delivery_fee > 0 && (
          <div className="flex justify-between text-gray-800">
            <span className="uppercase tracking-tighter">{fulfillment_type === 'delivery' ? 'Delivery Charge:' : 'Service Fee:'}:</span>
            <span className="font-mono">{formatCurrency(delivery_fee)}</span>
          </div>
        )}
        <div className="flex justify-between border-t-2 border-gray-800 pt-3 mt-3 font-black text-lg bg-gray-100 p-2">
          <span className="tracking-tighter uppercase">Net Total:</span>
          <span className="font-mono">{formatCurrency(total)}</span>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center border-t-2 border-dashed border-gray-800 pt-4 mt-4">
        <div className="bg-green-100 text-green-900 text-[10px] font-black py-1 px-3 rounded-full inline-block uppercase tracking-widest mb-2">
          Verified & Confirmed
        </div>
        <p className="text-[10px] text-gray-900 font-bold uppercase tracking-widest">Ready in ~15 minutes</p>
        <p className="text-xs font-black text-black mt-3 uppercase tracking-[0.2em]">Thank You for choosing us! 🙏</p>
      </div>
    </div>
  );
};

/**
 * ChatMessage Component
 * Displays individual chat messages from user or agent
 */
export const ChatMessage = ({ message, isUser = false, timestamp = null, receiptData = null }) => {
  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-6 group`}
      data-testid={`chat-message-${isUser ? 'user' : 'agent'}`}
    >
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-[#282F37] flex items-center justify-center text-[10px] font-bold text-[#8492A3] border border-[#2C353E]">
            A
          </div>
        ) : (
          <img src="/assets/agent-sanad.png" alt="S" className="w-8 h-8 rounded-full bg-[#2C353E] border border-[#2C353E]" />
        )}
      </div>
      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-bold text-[#8492A3] uppercase tracking-wider">
            {isUser ? 'Ahmed' : 'Sanad'}
          </span>
          {formattedTime && (
            <span className="text-[9px] text-[#526070] font-medium uppercase tracking-tighter">
              {formattedTime}
            </span>
          )}
        </div>
        <div className={`rounded-xl p-3 text-sm leading-relaxed ${
          isUser 
            ? 'bg-[#282F37] text-[#F1F3F5] rounded-tr-none border border-[#2C353E]' 
            : 'bg-[#1A1C1E] text-[#B9C8DA] rounded-tl-none border border-[#2C353E]'
        }`}>
          {message}
          {receiptData && <div className="mt-4"><ReceiptTable receiptData={receiptData} /></div>}
        </div>
      </div>
    </div>
  );
};

/**
 * ChatWindow Component
 * Displays the conversation history with fixed height and scrolling
 */
export const ChatWindow = ({ messages = [], className = '' }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div
      className="chat-window"
      data-testid="chat-window"
    >
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-500">
          <div className="text-center max-w-xs">
            <p className="text-lg font-bold text-white mb-2">How can I help you?</p>
            <p className="text-sm text-[#8492A3]">I can help you browse the menu, place an order, or answer questions.</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col">
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              message={msg.text}
              isUser={msg.isUser}
              timestamp={msg.timestamp}
              receiptData={msg.receiptData}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};

/**
 * ChatInput Component
 * Input field for sending text messages
 */
export const ChatInput = ({ onSendMessage, disabled = false, placeholder = 'Ask me anything...' }) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef(null);

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-3 w-full" data-testid="chat-input">
      <input
        ref={inputRef}
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={disabled}
        placeholder={placeholder}
        className="edix-input flex-1"
        data-testid="message-input"
        aria-label="Message input"
      />
    </div>
  );
};

/**
 * VoiceButton Component
 * Button to start/stop voice recording
 */
export const VoiceButton = ({
  onStartRecording,
  onStopRecording,
  isRecording = false,
  isDisabled = false,
  isTranscribing = false,
}) => {
  const handleClick = () => {
    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={handleClick}
        disabled={isDisabled || isTranscribing}
        className={`voice-button ${isRecording ? 'recording' : 'idle'} ${
          isDisabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
        data-testid="voice-button"
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        title={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {isTranscribing ? (
          <span className="text-sm">...</span>
        ) : isRecording ? (
          <span className="text-2xl">⏹</span>
        ) : (
          <span className="text-2xl">🎤</span>
        )}
      </button>
    </div>
  );
};

/**
 * EscalateButton Component
 * Button to escalate to human agent
 */
export const EscalateButton = ({ onEscalate, isDisabled = false }) => {
  return (
    <button
      onClick={onEscalate}
      disabled={isDisabled}
      className={`btn btn-secondary text-sm ${
        isDisabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      data-testid="escalate-button"
      aria-label="Talk to human agent"
      title="Talk to a human representative"
    >
      Talk to Human
    </button>
  );
};

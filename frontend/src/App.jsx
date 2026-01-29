import React, { useState, useCallback, useEffect } from 'react';
import { ChatWindow, ChatInput, VoiceButton, EscalateButton } from './components/Chat';
import { OrderReceipt } from './components/OrderReceipt';
import { CustomerOrders } from './components/CustomerOrders';
import { conversationAPI } from './api/conversationAPI';
import { VoiceRecorder, VoicePlayer } from './services/voiceService';
import { parseApiResponse } from './utils/formatters';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [customerPhone, setCustomerPhone] = useState(() => {
    const saved = localStorage.getItem('customerPhone');
    return saved || `+966${Date.now().toString().slice(-9)}`;
  });
  const [orderData, setOrderData] = useState({
    items: [], subtotal: 0, tax: 0, deliveryFee: 0, total: 0,
    orderId: null, orderNumber: null, status: 'draft', fulfillmentType: 'pickup',
  });

  const recorderRef = React.useRef(new VoiceRecorder());
  const playerRef = React.useRef(new VoicePlayer());

  useEffect(() => {
    localStorage.removeItem('conversationSession');
    const savedPhone = localStorage.getItem('customerPhone');
    if (savedPhone) setCustomerPhone(savedPhone);
  }, []);

  const handleSendMessage = useCallback(async (message) => {
    if (!message?.trim()) return;
    setIsLoading(true);
    try {
      const userMessage = { text: message, isUser: true, timestamp: new Date().toISOString() };
      setMessages((prev) => [...prev, userMessage]);
      const response = await conversationAPI.sendMessage(message, customerPhone, sessionId);
      const parsed = parseApiResponse(response);
      if (parsed.sessionId) setSessionId(parsed.sessionId);
      const agentMessage = {
        text: parsed.message, isUser: false, timestamp: new Date().toISOString(),
        receiptData: response.receipt_data || null,
      };
      setMessages((prev) => [...prev, agentMessage]);
      updateOrderData(response);
    } catch (err) { console.error(err); } finally { setIsLoading(false); }
  }, [customerPhone, sessionId]);

  const handleStartRecording = useCallback(async () => {
    try { await recorderRef.current.start(); setIsRecording(true); } catch (err) { console.error(err); }
  }, []);

  const handleStopRecording = useCallback(async () => {
    setIsRecording(false); setIsLoading(true);
    try {
      const audioBlob = await recorderRef.current.stop();
      if (!audioBlob) return;
      const response = await conversationAPI.sendVoiceMessage(audioBlob, customerPhone, sessionId, 'ar');
      setMessages((prev) => [...prev, 
        { text: response.transcription, isUser: true, timestamp: new Date().toISOString() },
        { text: response.response, isUser: false, timestamp: new Date().toISOString(), receiptData: response.receipt_data || null }
      ]);
      if (response.session_id) setSessionId(response.session_id);
      updateOrderData(response);
    } catch (err) { console.error(err); } finally { setIsLoading(false); }
  }, [customerPhone, sessionId]);

  const updateOrderData = (response) => {
    if (response.order_cleared) {
      setOrderData({ items: [], subtotal: 0, tax: 0, deliveryFee: 0, total: 0, orderId: null, orderNumber: null, status: 'draft', fulfillmentType: 'pickup' });
      return;
    }
    if (response.order_draft) {
      setOrderData((prev) => ({
        ...prev,
        items: response.order_draft.items || [],
        subtotal: response.order_draft.subtotal || 0,
        tax: response.order_draft.tax || 0,
        deliveryFee: response.order_draft.delivery_fee || 0,
        total: response.order_draft.total || 0,
        orderId: response.order_draft.order_number,
        orderNumber: response.order_draft.order_number,
      }));
    }
  };

  const handleConfirmOrder = useCallback(async () => {
    if (!customerPhone.trim() || isLoading) return;
    setIsLoading(true);
    try {
      const response = await conversationAPI.sendMessage('أكد الطلب', customerPhone, sessionId);
      const parsed = parseApiResponse(response);
      setMessages((prev) => [...prev, 
        { text: '📝 طلب تأكيد الطلب', isUser: true, timestamp: new Date().toISOString() },
        { text: parsed.message, isUser: false, timestamp: new Date().toISOString(), receiptData: response.receipt_data || null }
      ]);
      updateOrderData(response);
      // Refresh order history after confirmation
      if (refreshOrdersRef.current) {
        refreshOrdersRef.current();
      }
    } catch (err) { console.error(err); } finally { setIsLoading(false); }
  }, [customerPhone, sessionId, isLoading]);

  const refreshOrdersRef = React.useRef(null);

  const handleAskAboutOrder = useCallback((orderNumber) => {
    handleSendMessage(`ما هو وضع الطلب رقم ${orderNumber}؟`);
  }, [handleSendMessage]);

  const handleViewReceipt = useCallback((order) => {
    setMessages((prev) => [...prev, {
      text: `عرض إيصال الطلب #${order.order_number || (order.id && order.id.slice(0, 8)) || 'N/A'}`,
      isUser: false,
      timestamp: new Date().toISOString(),
      receiptData: order
    }]);
  }, []);

  const handleEndSession = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setCustomerPhone('');
    setOrderData({ items: [], subtotal: 0, tax: 0, deliveryFee: 0, total: 0, orderId: null, orderNumber: null, status: 'draft', fulfillmentType: 'pickup' });
    localStorage.removeItem('conversationSession');
    localStorage.removeItem('customerPhone');
  }, []);

  const handleEscalate = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await conversationAPI.sendMessage('Escalate to human', customerPhone, sessionId);
      const parsed = parseApiResponse(response);
      setMessages((prev) => [...prev, { text: parsed.message, isUser: false, timestamp: new Date().toISOString() }]);
    } catch (err) { console.error(err); } finally { setIsLoading(false); }
  }, [customerPhone, sessionId]);

  return (
    <div className="h-screen bg-[#121212] flex flex-col text-white overflow-hidden">
      {/* Header */}
      <header className="h-16 border-b border-[#2C353E] bg-[#1A1A1A] flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 bg-[#0046CC] rounded flex items-center justify-center">
             <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </div>
          <div className="h-8 w-[1px] bg-[#2C353E] mx-1"></div>
          <div className="flex items-center gap-3">
            <img src="/assets/agent-sanad.png" alt="Sanad" className="w-9 h-9 rounded-full border border-[#2C353E] object-cover" />
            <div className="flex flex-col">
              <span className="font-black text-sm tracking-tight leading-none uppercase">SANAD</span>
              <span className="text-[10px] font-bold text-[#8492A3] uppercase tracking-widest mt-1">Digital Cashier</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
           <div className="text-right">
             <p className="text-[10px] text-[#526070] uppercase font-bold tracking-widest">Active User</p>
             <p className="text-xs font-bold text-[#F1F3F5]">{customerPhone}</p>
           </div>
           <button onClick={handleEndSession} className="px-4 py-2 border border-[#2C353E] rounded text-[10px] font-bold uppercase tracking-widest text-[#8492A3] hover:text-white hover:bg-[#2C353E] transition-all">Sign Out</button>
        </div>
      </header>

      {/* Grid Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left: Content Area (Vertical stacking widgets) */}
        <div className="flex-1 overflow-hidden p-6 flex flex-col gap-6 bg-[#121212]">
          <div className="flex-1 bg-[#1A1A1A] rounded-xl border border-[#2C353E] p-6 flex flex-col shadow-2xl min-h-0">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#8492A3]">Live Order</h3>
              <div className="flex gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto min-h-0">
              <OrderReceipt 
                {...orderData} 
                onConfirmOrder={handleConfirmOrder} 
                isLoading={isLoading} 
              />
            </div>
          </div>
          <div className="flex-1 bg-[#1A1A1A] rounded-xl border border-[#2C353E] p-6 flex flex-col shadow-2xl min-h-0">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-[#8492A3]">Order History</h3>
              <div className="flex gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)] animate-pulse"></span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto min-h-0">
              <CustomerOrders 
                customerPhone={customerPhone} 
                refreshOrdersRef={refreshOrdersRef}
                onAskAboutOrder={handleAskAboutOrder}
                onViewReceipt={handleViewReceipt}
              />
            </div>
          </div>
        </div>

        {/* Right: Chat Sidebar */}
        <aside className="w-[500px] border-l border-[#2C353E] bg-[#1A1A1A] flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-[#2C353E] flex items-center justify-between">
            <h2 className="text-xs font-bold text-[#8492A3] uppercase tracking-widest">Chat Title</h2>
            <div className="flex gap-2">
              <button className="w-8 h-8 rounded bg-[#282F37] flex items-center justify-center text-xs border border-[#2C353E]">📝</button>
              <button className="w-8 h-8 rounded bg-[#282F37] flex items-center justify-center text-xs border border-[#2C353E]">🔲</button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <ChatWindow messages={messages} />
          </div>

          <div className="p-6 bg-[#1A1A1A]">
            <div className="bg-[#121212] rounded-xl border border-[#2C353E] p-4">
              <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} placeholder="Ask anything about your inventory" />
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#2C353E]">
                <div className="flex items-center gap-4">
                  {/* Left icons removed as requested */}
                </div>
                <div className="flex items-center gap-3">
                  <VoiceButton onStartRecording={handleStartRecording} onStopRecording={handleStopRecording} isRecording={isRecording} isDisabled={isLoading} />
                  <button 
                    onClick={() => handleSendMessage(document.querySelector('input[data-testid="message-input"]')?.value)} 
                    disabled={isLoading}
                    className="w-10 h-10 bg-[#0046CC] hover:bg-[#0037A3] text-white rounded-lg flex items-center justify-center transition-all disabled:opacity-50 shadow-lg border border-white/10"
                    aria-label="Send message"
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13"></line>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

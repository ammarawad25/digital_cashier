/**
 * Test Data Generation Utilities
 * Generates mock data for testing
 */

export const generateMockConversation = () => {
  return {
    messages: [
      {
        text: 'مرحبا، السلام عليكم',
        isUser: true,
        timestamp: new Date(Date.now() - 60000).toISOString(),
      },
      {
        text: 'مرحباً! كيف يمكنني مساعدتك اليوم؟',
        isUser: false,
        timestamp: new Date(Date.now() - 55000).toISOString(),
      },
      {
        text: 'أريد طلب برجر وبطاطس',
        isUser: true,
        timestamp: new Date(Date.now() - 40000).toISOString(),
      },
      {
        text: 'تمام، أضفت برجر وبطاطس إلى طلبك. هل تريد شيء آخر؟',
        isUser: false,
        timestamp: new Date(Date.now() - 35000).toISOString(),
      },
    ],
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
  };
};

export const generateMockOrder = () => {
  return {
    items: [
      {
        name: 'Classic Burger',
        price: 35,
        quantity: 2,
      },
      {
        name: 'French Fries',
        price: 15,
        quantity: 2,
      },
      {
        name: 'Iced Coffee',
        price: 12,
        quantity: 1,
      },
    ],
    subtotal: 112,
    tax: 16.8,
    deliveryFee: 10,
    total: 138.8,
    orderId: '550e8400-e29b-41d4-a716-446655440001',
    status: 'building_order',
    fulfillmentType: 'drive-thru',
  };
};

export const generateMockConversationResponse = () => {
  return {
    response: 'تمام، أضفت الطلب. الإجمالي 138.80 ريال.',
    session_id: '550e8400-e29b-41d4-a716-446655440000',
    intent: 'ordering',
    confidence: 0.95,
    conversation_state: 'building_order',
    order_draft: generateMockOrder(),
  };
};

export const generateMockVoiceTranscription = () => {
  return {
    transcription: 'أريد طلب برجر وبطاطس',
    language: 'ar',
    response: generateMockConversationResponse(),
  };
};

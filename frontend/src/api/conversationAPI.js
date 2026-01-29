import axios from 'axios';

// Use the full API URL including /api prefix
const API_BASE = 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Retry a request with exponential backoff
 * @param {Function} requestFn - Function that returns a promise
 * @param {number} maxRetries - Maximum number of retries (default: 3)
 * @returns {Promise} - The request promise
 */
const retryRequest = async (requestFn, maxRetries = 3) => {
  let lastError;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on client errors (4xx)
      if (error.response && error.response.status >= 400 && error.response.status < 500) {
        throw error;
      }
      
      // If this is the last attempt, throw the error
      if (attempt === maxRetries - 1) {
        break;
      }
      
      // Wait before retrying with exponential backoff
      const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
      console.log(`Request failed, retrying in ${delay}ms... (attempt ${attempt + 1}/${maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

export const conversationAPI = {
  /**
   * Send a text message to the conversation API
   * @param {string} message - The message to send
   * @param {string} customerPhone - Customer phone number
   * @param {string} sessionId - Optional session ID
   * @returns {Promise<Object>} Conversation response
   */
  sendMessage: async (message, customerPhone, sessionId = null) => {
    try {
      return await retryRequest(async () => {
        const response = await client.post('/conversation/message', {
          message,
          customer_phone: customerPhone,
          session_id: sessionId,
        });
        return response.data;
      });
    } catch (error) {
      throw new Error(`Failed to send message: ${error.message}`);
    }
  },

  /**
   * Send a voice message to the conversation API
   * @param {Blob} audioBlob - Audio blob from recorder
   * @param {string} customerPhone - Customer phone number
   * @param {string} sessionId - Optional session ID
   * @param {string} language - Language code (default: 'ar')
   * @returns {Promise<Object>} Voice response with transcription and conversation
   */
  sendVoiceMessage: async (audioBlob, customerPhone, sessionId = null, language = 'ar') => {
    try {
      // Log request details for debugging
      console.log('Sending voice message:', {
        blobSize: audioBlob.size,
        blobType: audioBlob.type,
        customerPhone,
        sessionId,
        language
      });

      return await retryRequest(async () => {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.webm');
        formData.append('customer_phone', customerPhone);
        if (sessionId) {
          formData.append('session_id', sessionId);
        }
        formData.append('language', language);

        const response = await client.post('/conversation/voice', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        console.log('Voice message response:', response.data);
        return response.data;
      });
    } catch (error) {
      console.error('Voice message error:', error.response?.data || error.message);
      throw new Error(`Failed to send voice message: ${error.message}`);
    }
  },

  /**
   * Health check endpoint
   * @returns {Promise<Object>} Health status
   */
  healthCheck: async () => {
    try {
      const response = await client.get('/conversation/health');
      return response.data;
    } catch (error) {
      throw new Error('API health check failed');
    }
  },
};

export default client;

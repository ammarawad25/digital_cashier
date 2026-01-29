/**
 * Utility functions for formatting data
 */

/**
 * Format number as currency (SAR)
 * @param {number} amount
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount) + ' ﷼';
};

/**
 * Format date to readable string
 * @param {Date|string} date
 * @returns {string}
 */
export const formatDate = (date) => {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Truncate string to specified length
 * @param {string} str
 * @param {number} length
 * @returns {string}
 */
export const truncate = (str, length = 50) => {
  return str.length > length ? `${str.substring(0, length)}...` : str;
};

/**
 * Parse API response and extract relevant data
 * @param {Object} response
 * @returns {Object} Parsed response data
 */
export const parseApiResponse = (response) => {
  return {
    message: response.response || '',
    sessionId: response.session_id,
    intent: response.intent,
    confidence: response.confidence,
    conversationState: response.conversation_state,
  };
};

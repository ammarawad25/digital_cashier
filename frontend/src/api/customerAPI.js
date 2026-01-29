/**
 * Get customer orders by phone number
 */
export const getCustomerOrders = async (customerPhone) => {
  if (!customerPhone) {
    throw new Error('Customer phone is required');
  }

  try {
    const response = await fetch(`/api/customer/orders?phone=${encodeURIComponent(customerPhone)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || errorData?.message || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('Get customer orders error:', error);
    throw error;
  }
};

/**
 * Report an issue with an order
 */
export const reportOrderIssue = async (orderNumber, issueDescription, customerPhone) => {
  if (!orderNumber || !issueDescription || !customerPhone) {
    throw new Error('Order number, issue description, and customer phone are required');
  }

  try {
    const response = await fetch('http://localhost:8001/api/conversation/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `لدي مشكلة في الطلب ${orderNumber}: ${issueDescription}`,
        customer_phone: customerPhone,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail || errorData?.message || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error('Report order issue error:', error);
    throw error;
  }
};
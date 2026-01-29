import React, { useState, useEffect } from 'react';
import { getCustomerOrders, reportOrderIssue } from '../api/customerAPI';

/**
 * CustomerOrders Component
 * Displays customer's order history with actions
 * PROTECTED: Prevents accidental data loss
 */
export const CustomerOrders = ({ customerPhone, onAskAboutOrder, onViewReceipt, refreshOrdersRef }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [complainingOrder, setComplainingOrder] = useState(null);
  const [complaintText, setComplaintText] = useState('');

  // Fetch customer orders
  const fetchOrders = async () => {
    if (!customerPhone) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getCustomerOrders(customerPhone);
      // API returns array directly, not wrapped in 'orders' property
      setOrders(Array.isArray(response) ? response : []);
    } catch (err) {
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [customerPhone]);

  // Expose fetchOrders via ref so parent can trigger refresh
  useEffect(() => {
    if (refreshOrdersRef) {
      refreshOrdersRef.current = fetchOrders;
    }
  }, [refreshOrdersRef, customerPhone]);

  // Handle complaint submission
  const handleComplaintSubmit = async (orderNumber) => {
    if (!complaintText.trim()) return;
    
    try {
      await reportOrderIssue(orderNumber, complaintText, customerPhone);
      setComplainingOrder(null);
      setComplaintText('');
      // Refresh orders to get updated status
      await fetchOrders();
    } catch (err) {
      console.error('Failed to submit complaint:', err);
      setError('Failed to submit complaint');
    }
  };

  // Status color mapping
  const getStatusColor = (status) => {
    const colors = {
      'PENDING': 'bg-yellow-100 text-yellow-800',
      'CONFIRMED': 'bg-blue-100 text-blue-800', 
      'PREPARING': 'bg-orange-100 text-orange-800',
      'READY': 'bg-green-100 text-green-800',
      'OUT_FOR_DELIVERY': 'bg-purple-100 text-purple-800',
      'DELIVERED': 'bg-emerald-100 text-emerald-800',
      'CANCELLED': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Status display text
  const getStatusText = (status) => {
    const texts = {
      'PENDING': '⏳ قيد الانتظار',
      'CONFIRMED': '✅ تم التأكيد',
      'PREPARING': '👨‍🍳 يتم التحضير',
      'READY': '🍕 جاهز للاستلام',
      'OUT_FOR_DELIVERY': '🚚 في الطريق',
      'DELIVERED': '✅ تم التسليم',
      'CANCELLED': '❌ ملغي'
    };
    return texts[status] || status;
  };

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
        <p className="text-sm text-gray-600 mt-2">Loading orders...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-600 text-sm">{error}</p>
        <button 
          onClick={fetchOrders}
          className="mt-2 text-blue-600 text-sm underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <p className="text-sm">Your orders will be displayed here once available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-2">
      <div className="flex items-start justify-between mb-3 px-1">
        <h3 className="font-bold text-[#8492A3] text-[10px] uppercase tracking-widest">Your Orders</h3>
      </div>
      
      {orders.map((order) => (
        <div key={order.id} className="border border-[#2C353E] rounded-lg p-4 bg-[#121212] hover:border-[#0046CC] transition-all">
          {/* Order Header */}
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="font-bold text-white text-sm">{order.order_number ? `Order #${order.order_number}` : `Order #${order.id.slice(0, 8)}`}</p>
              <p className="text-[10px] font-bold text-[#526070] uppercase tracking-wider mt-1">
                {new Date(order.created_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
            <div className="text-right">
              <span className={`px-2 py-1 rounded-full text-[9px] font-black uppercase tracking-widest bg-[#2C353E] text-[#8492A3]`}>
                {getStatusText(order.status)}
              </span>
              <p className="text-sm font-black text-white mt-2">${order.total.toFixed(2)}</p>
            </div>
          </div>

          {/* Order Actions */}
          <div className="grid grid-cols-3 gap-2 mt-4">
            <button
              onClick={() => onViewReceipt && onViewReceipt(order)}
              className="px-2 py-2 bg-[#1A1A1A] border border-[#2C353E] text-[#8492A3] rounded text-[10px] font-bold uppercase tracking-widest hover:text-white hover:border-[#8492A3] transition-all"
            >
              Receipt
            </button>
            
            <button
              onClick={() => setComplainingOrder(order.id)}
              className="px-2 py-2 bg-[#1A1A1A] border border-[#2C353E] text-[#8492A3] rounded text-[10px] font-bold uppercase tracking-widest hover:text-white hover:border-[#8492A3] transition-all"
            >
              Issue
            </button>
            
            <button
              onClick={() => onAskAboutOrder && onAskAboutOrder(order.order_number || order.id)}
              className="px-2 py-2 bg-[#1A1A1A] border border-[#2C353E] text-[#8492A3] rounded text-[10px] font-bold uppercase tracking-widest hover:text-white hover:border-[#8492A3] transition-all"
            >
              Ask
            </button>
          </div>

          {/* Complaint Form */}
          {complainingOrder === order.id && (
            <div className="mt-3 p-3 bg-gray-50 rounded border">
              <p className="text-xs font-medium text-gray-700 mb-2">What's the issue?</p>
              <textarea
                value={complaintText}
                onChange={(e) => setComplaintText(e.target.value)}
                placeholder="Describe the problem with your order..."
                className="w-full p-2 border border-gray-300 rounded text-xs resize-none"
                rows={3}
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleComplaintSubmit(order.order_number || order.id)}
                  disabled={!complaintText.trim()}
                  className="px-3 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700 disabled:opacity-50"
                >
                  Submit
                </button>
                <button
                  onClick={() => {
                    setComplainingOrder(null);
                    setComplaintText('');
                  }}
                  className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-xs font-medium hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
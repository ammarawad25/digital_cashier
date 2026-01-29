import React from 'react';
import { formatCurrency } from '../utils/formatters';

/**
 * OrderReceipt Component
 * Displays the current order being built and its receipt
 * PROTECTED: Shows lock status when order is confirmed
 */
export const OrderReceipt = ({
  items = [],
  subtotal = 0,
  tax = 0,
  deliveryFee = 0,
  total = 0,
  orderId = null,
  status = 'draft',
  fulfillmentType = 'delivery',
  isEmpty = true,
  onConfirmOrder = null,
  isLoading = false,
  isLocked = false,
}) => {
  if (isEmpty && items.length === 0) {
    return (
      <div
        className="card h-full flex items-center justify-center text-gray-400"
        data-testid="order-receipt-empty"
      >
        <div className="text-center">
          <p className="text-lg font-semibold mb-2">Order Receipt</p>
          <p className="text-sm">Order details will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="summary-container" data-testid="order-receipt">       
      <h2 className="summary-title flex-shrink-0">Order Summary</h2>

      <div className="summary-scroll-area" data-testid="receipt-items">
        {items.length > 0 ? (
          <div className="space-y-4">
            {items.map((item, index) => (
              <div key={index} className="summary-item border-b border-[#2C353E] pb-3" data-testid={`receipt-item-${index}`}>
                <div className="flex-1">
                  <p className="font-bold text-white text-xs">{item.arabic_name || item.name}</p>
                  <p className="text-[9px] text-[#8492A3] font-bold uppercase tracking-widest">Qty {item.quantity}</p>
                </div>
                <div className="text-right ml-4">
                  <p className="font-bold text-white text-xs">
                    {formatCurrency(item.price * item.quantity)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center text-[#526070] py-10">
            <div className="text-4xl mb-4">🛒</div>
            <p className="text-sm font-bold text-white">Your cart is empty</p>
            <p className="text-[10px]">Speak your order to SANAD</p>
          </div>
        )}

        <div className="mt-8 space-y-3 border-t border-[#2C353E] pt-6">
          <div className="flex justify-between text-[10px] font-bold text-[#8492A3] uppercase tracking-widest">
            <span>Subtotal</span>
            <span className="text-white">{formatCurrency(subtotal)}</span>
          </div>
          <div className="flex justify-between text-[10px] font-bold text-[#8492A3] uppercase tracking-widest">
            <span>Service Fee</span>
            <span className="text-white">{formatCurrency(deliveryFee)}</span>
          </div>
          <div className="flex justify-between text-[10px] font-bold text-[#8492A3] uppercase tracking-widest">
            <span>Tax</span>
            <span className="text-white">{formatCurrency(tax)}</span>
          </div>
        </div>
      </div>

      <div className="summary-total flex-shrink-0 pt-4 border-t border-[#2C353E]">
        <span className="summary-total-label text-[10px]">Total</span>
        <span className="summary-total-value text-xl">{formatCurrency(total)}</span>
      </div>

      {status === 'draft' && items.length > 0 && onConfirmOrder && (
        <button
          onClick={onConfirmOrder}
          disabled={isLoading}
          className="btn-edix-primary w-full mt-4 h-12 flex-shrink-0 shadow-[0_8px_16px_-4px_rgba(0,70,204,0.4)] uppercase text-xs tracking-widest font-black"
          data-testid="confirm-order-button"
        >
          {isLoading ? 'Processing...' : 'PLACE ORDER'}
        </button>
      )}
    </div>
  );
};

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OrderReceipt } from '../components/OrderReceipt';

/**
 * Test Suite: OrderReceipt Component
 */
describe('OrderReceipt', () => {
  it('should render empty state when no items', () => {
    render(<OrderReceipt isEmpty={true} items={[]} />);
    expect(screen.getByTestId('order-receipt-empty')).toBeTruthy();
    expect(screen.getByText(/Order details will appear here/)).toBeTruthy();
  });

  it('should render order receipt with items', () => {
    const items = [
      { name: 'Burger', price: 25, quantity: 2 },
      { name: 'Fries', price: 10, quantity: 1 },
    ];
    render(
      <OrderReceipt
        items={items}
        subtotal={60}
        tax={9}
        deliveryFee={5}
        total={74}
        isEmpty={false}
      />
    );

    expect(screen.getByTestId('order-receipt')).toBeTruthy();
    expect(screen.getByText('Burger')).toBeTruthy();
    expect(screen.getByText('Fries')).toBeTruthy();
  });

  it('should display all items correctly', () => {
    const items = [
      { name: 'Item 1', price: 10, quantity: 2 },
      { name: 'Item 2', price: 20, quantity: 1 },
      { name: 'Item 3', price: 15, quantity: 3 },
    ];
    render(
      <OrderReceipt
        items={items}
        subtotal={100}
        tax={15}
        isEmpty={false}
      />
    );

    const receiptItems = screen.getAllByTestId(/receipt-item-/);
    expect(receiptItems.length).toBe(3);
  });

  it('should display subtotal correctly', () => {
    render(
      <OrderReceipt
        items={[{ name: 'Item', price: 50, quantity: 2 }]}
        subtotal={100}
        tax={0}
        isEmpty={false}
      />
    );

    const subtotalElement = screen.getByTestId('receipt-subtotal');
    expect(subtotalElement).toHaveTextContent('SAR');
  });

  it('should display tax when greater than 0', () => {
    render(
      <OrderReceipt
        items={[]}
        subtotal={100}
        tax={15}
        isEmpty={false}
      />
    );

    expect(screen.getByTestId('receipt-tax')).toBeTruthy();
  });

  it('should not display tax when 0', () => {
    render(
      <OrderReceipt
        items={[]}
        subtotal={100}
        tax={0}
        isEmpty={false}
      />
    );

    expect(screen.queryByTestId('receipt-tax')).toBeNull();
  });

  it('should display delivery fee when greater than 0', () => {
    render(
      <OrderReceipt
        items={[]}
        subtotal={100}
        deliveryFee={5}
        isEmpty={false}
      />
    );

    expect(screen.getByTestId('receipt-delivery')).toBeTruthy();
  });

  it('should not display delivery fee when 0', () => {
    render(
      <OrderReceipt
        items={[]}
        subtotal={100}
        deliveryFee={0}
        isEmpty={false}
      />
    );

    expect(screen.queryByTestId('receipt-delivery')).toBeNull();
  });

  it('should display total correctly', () => {
    render(
      <OrderReceipt
        items={[]}
        subtotal={100}
        tax={15}
        deliveryFee={5}
        total={120}
        isEmpty={false}
      />
    );

    const totalElement = screen.getByTestId('receipt-total');
    expect(totalElement).toHaveTextContent('120');
  });

  it('should display order ID when provided', () => {
    render(
      <OrderReceipt
        items={[]}
        orderId="550e8400-e29b-41d4-a716-446655440000"
        isEmpty={false}
      />
    );

    expect(screen.getByText(/#550e8400/)).toBeTruthy();
  });

  it('should display fulfillment type', () => {
    const { rerender } = render(
      <OrderReceipt items={[]} fulfillmentType="delivery" isEmpty={false} />
    );
    expect(screen.getByText('🚗 Delivery')).toBeTruthy();

    rerender(<OrderReceipt items={[]} fulfillmentType="pickup" isEmpty={false} />);
    expect(screen.getByText('🏪 Pickup')).toBeTruthy();
  });

  it('should display status when not draft', () => {
    render(
      <OrderReceipt items={[]} status="confirmed" isEmpty={false} />
    );
    expect(screen.getByText(/CONFIRMED/)).toBeTruthy();
  });

  it('should calculate and display item subtotal correctly', () => {
    const items = [
      { name: 'Burger', price: 25, quantity: 2 },
    ];
    render(
      <OrderReceipt
        items={items}
        subtotal={50}
        isEmpty={false}
      />
    );

    // Burger at 25 x 2 = 50
    const itemElement = screen.getByTestId('receipt-item-0');
    expect(itemElement).toHaveTextContent('50');
    expect(itemElement).toHaveTextContent('Qty: 2');
  });

  it('should handle multiple items with different quantities', () => {
    const items = [
      { name: 'Item A', price: 10, quantity: 1 },
      { name: 'Item B', price: 20, quantity: 2 },
      { name: 'Item C', price: 15, quantity: 3 },
    ];
    render(
      <OrderReceipt
        items={items}
        subtotal={100}
        isEmpty={false}
      />
    );

    const item0 = screen.getByTestId('receipt-item-0');
    expect(item0).toHaveTextContent('Qty: 1');

    const item1 = screen.getByTestId('receipt-item-1');
    expect(item1).toHaveTextContent('Qty: 2');

    const item2 = screen.getByTestId('receipt-item-2');
    expect(item2).toHaveTextContent('Qty: 3');
  });

  it('should format currency values', () => {
    render(
      <OrderReceipt
        items={[{ name: 'Item', price: 25.5, quantity: 2 }]}
        subtotal={51}
        tax={7.65}
        deliveryFee={5}
        total={63.65}
        isEmpty={false}
      />
    );

    // Check that SAR currency is displayed
    const receipt = screen.getByTestId('order-receipt');
    expect(receipt.textContent).toContain('SAR');
  });
});

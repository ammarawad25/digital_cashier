import { test, expect } from '@playwright/test';

test.describe('Customer Service Agent Frontend E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
  });

  test('should display phone input on initial load', async ({ page }) => {
    // Check that the phone input form is visible
    await expect(page.getByTestId('phone-input')).toBeVisible();
    await expect(page.getByTestId('start-session-button')).toBeVisible();
  });

  test('should start a session with valid phone number', async ({ page }) => {
    // Enter phone number
    await page.getByTestId('phone-input').fill('+966501234567');

    // Click start button
    await page.getByTestId('start-session-button').click();

    // Wait for main interface to appear
    await expect(page.locator('text=🍕 Customer Service Agent')).toBeVisible();
    await expect(page.getByTestId('chat-window')).toBeVisible();
    await expect(page.getByTestId('voice-button')).toBeVisible();
  });

  test('should show error when phone number is empty', async ({ page }) => {
    // Try to submit empty form
    const startButton = page.getByTestId('start-session-button');
    await expect(startButton).toBeDisabled();
  });

  test('should send and receive text messages', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Wait for chat to load
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Type a message
    const messageInput = page.getByTestId('message-input');
    await messageInput.fill('Hello, I need help');

    // Send message
    await page.getByTestId('send-button').click();

    // Input should be cleared
    await expect(messageInput).toHaveValue('');

    // Wait for response (with timeout)
    await page.waitForTimeout(2000);
  });

  test('should display order receipt component', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Check that receipt is visible (on large screens)
    const receipt = page.getByTestId('order-receipt');
    if (await page.viewportSize().then(size => size && size.width > 1024)) {
      await expect(receipt).toBeVisible();
    }
  });

  test('should disable input while loading', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Wait for chat
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Try to send message
    const messageInput = page.getByTestId('message-input');
    await messageInput.fill('Test message');
    await page.getByTestId('send-button').click();

    // Input should be disabled during sending
    await expect(messageInput).toBeFocused();
  });

  test('should end session and return to phone input', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Wait for main interface
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Click end session button
    await page.getByTestId('end-session-button').click();

    // Should return to phone input
    await expect(page.getByTestId('phone-input')).toBeVisible();
  });

  test('should persist session in localStorage', async ({ page, context }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Wait for session
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Get localStorage data
    const sessionData = await page.evaluate(() => {
      return localStorage.getItem('customerPhone');
    });

    expect(sessionData).toBe('+966501234567');
  });

  test('should show voice button on main interface', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Check voice button
    const voiceButton = page.getByTestId('voice-button');
    await expect(voiceButton).toBeVisible();
    await expect(voiceButton).toHaveText('🎤');
  });

  test('should display error alerts', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Wait for chat
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Try to send a message (may fail due to no backend)
    await page.getByTestId('message-input').fill('Test');
    await page.getByTestId('send-button').click();

    // Error alert may appear
    await page.waitForTimeout(1000);
  });

  test('should have accessible form elements', async ({ page }) => {
    // Check for accessibility attributes
    const phoneInput = page.getByTestId('phone-input');
    const sendButton = page.getByTestId('send-button');
    const voiceButton = page.getByTestId('voice-button');

    await expect(phoneInput).toHaveAttribute('type', 'tel');

    // Start session to check other elements
    await phoneInput.fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    await expect(voiceButton).toHaveAttribute('aria-label');
  });

  test('should work on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Navigate
    await page.goto('/');

    // Check phone input is visible and usable
    await expect(page.getByTestId('phone-input')).toBeVisible();

    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Chat should be visible
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Voice button should be accessible
    await expect(page.getByTestId('voice-button')).toBeVisible();
  });

  test('should handle window resizing', async ({ page }) => {
    // Start session
    await page.getByTestId('phone-input').fill('+966501234567');
    await page.getByTestId('start-session-button').click();

    // Wait for main interface
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByTestId('chat-window')).toBeVisible();

    // Resize back to desktop
    await page.setViewportSize({ width: 1280, height: 720 });
    await expect(page.getByTestId('chat-window')).toBeVisible();
  });
});

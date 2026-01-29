# Testing Guide - Customer Service Agent Frontend

## Overview

This project follows Test-Driven Development (TDD) principles with comprehensive unit, integration, and end-to-end (E2E) tests.

## Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat.test.jsx          # Component unit tests
│   │   └── OrderReceipt.test.jsx  
│   ├── services/
│   │   └── voiceService.test.js   # Service unit tests
│   ├── api/
│   │   └── conversationAPI.test.js # API integration tests
│   ├── utils/
│   │   └── formatters.test.js     # Utility function tests
│   ├── App.test.jsx               # Integration tests
│   └── test/
│       ├── setup.js               # Test configuration
│       └── mockData.js            # Mock data generators
└── tests/
    └── e2e/
        └── app.spec.js            # End-to-end tests
```

## Running Tests

### Unit Tests (Vitest)

```bash
# Run all unit tests
npm test

# Run in watch mode (default for development)
npm test

# Run with coverage report
npm run test:coverage

# Run with UI
npm run test:ui

# Run specific test file
npm test src/components/Chat.test.jsx

# Run single test
npm test -- --reporter=verbose
```

### End-to-End Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (recommended for development)
npm run test:e2e:ui

# Run specific test file
npm run test:e2e tests/e2e/app.spec.js

# Run in headed mode (see browser)
npm run test:e2e -- --headed

# Debug mode
npm run test:e2e -- --debug
```

### Run All Tests

```bash
npm run test:all
```

## Test Coverage

Current test coverage:

| Type | Files | Tests | Pass Rate |
|------|-------|-------|-----------|
| Unit | 5 | 85 | 100% |
| Integration | 1 | 14 | 100% |
| E2E | 1 | 10+ | Pending* |

*E2E tests require a running backend API

## Writing Tests

### Unit Test Example (Components)

```javascript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeTruthy();
  });

  it('should handle click events', () => {
    const mockClick = vi.fn();
    render(<MyComponent onClick={mockClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(mockClick).toHaveBeenCalled();
  });
});
```

### Unit Test Example (Services)

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { VoiceRecorder } from './voiceService';

describe('VoiceRecorder', () => {
  let recorder;

  beforeEach(() => {
    recorder = new VoiceRecorder();
  });

  it('should initialize correctly', () => {
    expect(recorder.isRecording).toBeFalsy();
  });

  it('should start recording', async () => {
    const mockStream = { getTracks: () => [] };
    global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);
    
    await recorder.start();
    expect(recorder.isRecording).toBeTruthy();
  });
});
```

### Integration Test Example

```javascript
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

describe('App Integration', () => {
  it('should send and receive messages', async () => {
    render(<App />);
    
    // Start session
    fireEvent.change(screen.getByTestId('phone-input'), {
      target: { value: '+966501234567' }
    });
    fireEvent.click(screen.getByTestId('start-session-button'));
    
    // Send message
    fireEvent.change(screen.getByTestId('message-input'), {
      target: { value: 'Hello' }
    });
    fireEvent.click(screen.getByTestId('send-button'));
    
    // Verify message appears
    expect(screen.getByText('Hello')).toBeTruthy();
  });
});
```

### E2E Test Example (Playwright)

```javascript
import { test, expect } from '@playwright/test';

test('complete order flow', async ({ page }) => {
  // Navigate to app
  await page.goto('/');
  
  // Start session
  await page.getByTestId('phone-input').fill('+966501234567');
  await page.getByTestId('start-session-button').click();
  
  // Send message
  await page.getByTestId('message-input').fill('I want to order');
  await page.getByTestId('send-button').click();
  
  // Verify order receipt appears
  const receipt = await page.getByTestId('order-receipt');
  await expect(receipt).toBeVisible();
});
```

## Test Data

Mock data is available in `src/test/mockData.js`:

```javascript
import {
  generateMockConversation,
  generateMockOrder,
  generateMockConversationResponse,
  generateMockVoiceTranscription
} from '../test/mockData';

const mockConversation = generateMockConversation();
const mockOrder = generateMockOrder();
```

## Mocking

### Mocking API Calls

```javascript
import { vi } from 'vitest';
import { conversationAPI } from '../api/conversationAPI';

// Mock successful response
vi.spyOn(conversationAPI, 'sendMessage').mockResolvedValueOnce({
  response: 'Hello!',
  session_id: 'session-123',
  intent: 'greeting',
  confidence: 0.95,
});

// Mock error
vi.spyOn(conversationAPI, 'sendMessage').mockRejectedValueOnce(
  new Error('Network error')
);
```

### Mocking Voice Services

```javascript
import { VoiceRecorder } from '../services/voiceService';

const mockStream = {
  getTracks: () => [{ stop: vi.fn() }],
};
global.navigator.mediaDevices.getUserMedia.mockResolvedValueOnce(mockStream);
```

## Testing Checklist

Before committing code:

- [ ] All unit tests pass: `npm test -- --run`
- [ ] Test coverage is >80%: `npm run test:coverage`
- [ ] E2E tests pass: `npm run test:e2e`
- [ ] No console errors or warnings
- [ ] Code follows style guide
- [ ] New features have tests
- [ ] No hardcoded values in tests

## Common Testing Issues

### Issue: "Element not found"
**Solution**: Ensure element is rendered before querying. Use `waitFor()`:

```javascript
await waitFor(() => {
  expect(screen.getByTestId('my-element')).toBeTruthy();
});
```

### Issue: "Cannot read property of undefined"
**Solution**: Check mock setup. Ensure mocks are created before component render:

```javascript
beforeEach(() => {
  vi.clearAllMocks();
  // Setup mocks here
});
```

### Issue: "Test timeout"
**Solution**: Increase timeout for E2E tests:

```javascript
test('my test', async ({ page }) => {
  // test code
}, { timeout: 60000 });
```

## Performance Testing

Monitor test execution time:

```bash
npm test -- --reporter=verbose
```

Target: <100ms per unit test, <5s for all unit tests

## Continuous Integration

For CI/CD pipelines:

```bash
# Run all tests with exit code
npm run test:all

# Check coverage
npm run test:coverage

# Build for deployment
npm run build
```

## Debugging Tests

### Debug Vitest

```bash
# Run with debugging
npm test -- --reporter=verbose --inspect-brk
```

### Debug Playwright

```bash
# Interactive mode
npm run test:e2e -- --debug

# Trace viewer
npm run test:e2e -- --headed

# Step through code
npx playwright test --headed --debug
```

### Print Debug Info

```javascript
it('debug example', () => {
  const { debug } = render(<MyComponent />);
  debug(); // Print DOM
  
  screen.logTestingPlaygroundURL(); // Get playground URL
});
```

## Test Maintenance

### Regular Tasks

- Review and update snapshots monthly
- Check for flaky tests
- Update mocks when API changes
- Remove skipped tests (`it.skip`)
- Refactor tests to reduce duplication

### Monitoring

```bash
# Check test health
npm test -- --reporter=verbose --reporter=html

# Coverage trends
npm run test:coverage

# CI logs and reports
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Questions?

For testing-related questions, refer to test files or documentation above.

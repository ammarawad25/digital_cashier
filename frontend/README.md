# Customer Service Agent Frontend

A modern React-based frontend for the Customer Service Agent digital worker system. This interface allows customers to interact with an AI-powered customer service agent through voice and text chat, with real-time order tracking.

## ✨ Features

- **Voice & Text Chat**: Switch between voice recording and text input seamlessly
- **Real-time Transcription**: Arabic and English language support
- **Order Receipt Tracking**: Real-time display of order details and pricing
- **Responsive Design**: Beautiful, modern UI with Tailwind CSS
- **Session Management**: Persistent conversation sessions with local storage
- **Accessibility**: ARIA labels and semantic HTML for better accessibility

## 🛠 Tech Stack

- **Frontend Framework**: React 18
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3
- **Testing**: Vitest + React Testing Library
- **HTTP Client**: Axios
- **Voice Services**: Web Audio API

## 📋 Requirements

- Node.js 16+ and npm 8+
- Backend API running on `http://localhost:8000`

## 🚀 Quick Start

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

The dev server automatically proxies `/api` requests to `http://localhost:8000`

### Building for Production

```bash
npm run build
npm run preview  # Preview the production build
```

## 🧪 Testing

### Run All Tests

```bash
npm test
```

### Run Tests with Coverage

```bash
npm run test:coverage
```

### Run Tests with UI

```bash
npm run test:ui
```

## 📚 Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Chat.jsx        # Chat interface components
│   │   ├── OrderReceipt.jsx # Order receipt display
│   │   ├── Chat.test.jsx    # Component tests
│   │   └── OrderReceipt.test.jsx
│   ├── services/           # Business logic services
│   │   ├── voiceService.js # Voice recording/playback
│   │   └── voiceService.test.js
│   ├── api/               # API integration
│   │   ├── conversationAPI.js
│   │   └── conversationAPI.test.js
│   ├── utils/             # Utility functions
│   │   ├── formatters.js
│   │   └── formatters.test.js
│   ├── styles/           # Global styles
│   │   └── index.css
│   ├── test/             # Test utilities and mock data
│   │   ├── setup.js
│   │   └── mockData.js
│   ├── App.jsx           # Main application component
│   └── main.jsx          # Entry point
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
├── vitest.config.js      # Vitest configuration
├── tailwind.config.js    # Tailwind configuration
└── postcss.config.js     # PostCSS configuration
```

## 🎯 Features Breakdown

### Chat Interface
- Send and receive messages in real-time
- Auto-scrolling conversation history
- User and agent message differentiation
- Timestamps for each message
- Character-by-character message display

### Voice Recording
- One-click voice recording via microphone
- Real-time audio transcription
- Automatic language detection (Arabic/English)
- Echo cancellation and noise suppression
- Visual feedback during recording

### Order Receipt
- Real-time order updates
- Item list with quantities and prices
- Automatic calculation of totals
- Tax and delivery fee display
- Order status tracking
- Currency formatting (SAR)

### Session Management
- Persistent session storage in localStorage
- Phone number validation
- Session ID generation
- Automatic session cleanup

## 🔧 Environment Variables

Create a `.env` file if needed for API configuration:

```
VITE_API_URL=http://localhost:8000
```

## 🐛 Troubleshooting

### Voice Recording Not Working
- Check browser permissions for microphone access
- Ensure you're using HTTPS in production (or localhost for development)
- Verify your system audio is not muted

### Slow Transcription
- Check network connectivity
- Verify backend API is running
- Clear browser cache if issues persist

### Style Issues
- Ensure Tailwind CSS is properly built: `npm install`
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

## 📖 API Integration

The frontend communicates with the backend through the `/api/conversation` endpoint:

### POST `/api/conversation/message`
Send a text message and get a response

```javascript
{
  message: "I want to order a burger",
  customer_phone: "+966501234567",
  session_id: "uuid-here" // optional
}
```

### POST `/api/conversation/voice`
Send voice message with automatic transcription

```javascript
FormData {
  audio: Blob,
  customer_phone: "+966501234567",
  language: "ar", // or "en"
  session_id: "uuid-here" // optional
}
```

## 🚀 Deployment

### Docker Deployment (Optional)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Build & Deploy

```bash
npm run build
# Deploy the dist/ folder to your hosting service
```

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🧑‍💻 Development Guidelines

### Code Style
- Use ES6+ syntax
- Follow React hooks best practices
- Use functional components
- Maintain component re-usability

### Testing
- Write tests alongside components
- Aim for >80% code coverage
- Test user interactions, not implementation details
- Use meaningful test descriptions

### Performance
- Lazy load components when needed
- Optimize bundle size
- Use React.memo for expensive components
- Monitor lighthouse scores

## 📄 License

This project is part of the Customer Service Agent system.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `npm test`
4. Commit with meaningful messages
5. Push and create a pull request

## 📞 Support

For issues and questions, please reach out to the development team.

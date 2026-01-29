# Voice-Only Customer Service Agent

Multi-agent digital worker system for food service customer support with resilient agentic flow.

## 🚀 Performance Optimizations (Latest)

**✅ Optimized for Speed & Efficiency** (January 28, 2026)
- ⚡ **30-40% faster response times**
- 🎯 **80-90% faster perceived latency** (streaming enabled)
- 💰 **20% cost reduction** (fewer tokens)
- 🧠 **40% memory reduction**
- 📈 **200% more concurrent users**

**Documentation:**
- [📊 Optimization Summary](OPTIMIZATION_SUMMARY.md) - Complete overview
- [⚡ Quick Reference](docs/OPTIMIZATION_QUICK_REF.md) - Configuration guide
- [📈 Visual Guide](docs/OPTIMIZATION_VISUAL_GUIDE.md) - Performance diagrams
- [📋 Comparison Table](docs/OPTIMIZATION_COMPARISON_TABLE.md) - Before/after metrics

## Features

- **Policy-First Resolution**: 80% of issues handled without LLM
- **Graduated Confidence**: Smart decision-making with confidence thresholds
- **Multi-Agent Architecture**: Specialized agents for Menu, Orders, and Issues
- **Session Persistence**: Stateful conversations with history
- **FAQ Fast Path**: Instant responses for common questions
- **Recommendation Engine**: Smart upsell suggestions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Update `OPENAI_API_KEY` with your squad key.

**Optional: Enable LangSmith Tracing**

To trace agent communication, add to `.env`:
```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT=customer-service-agent
```

### 3. Initialize Database

```bash
python -m src.data.seed_data
```

### 4. Run Tests

```bash
pytest tests/ -v
```

### 5. Start API Server

```bash
uvicorn src.main:app --reload --port 8000
```

## API Endpoints

### POST /api/conversation/message

Process a customer message:

```bash
curl -X POST http://localhost:8000/api/conversation/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to order a burger",
    "customer_phone": "+15555555555"
  }'
```

### GET /api/conversation/health

Health check:

```bash
curl http://localhost:8000/api/conversation/health
```

## Architecture

### Core Agents

1. **Conversation Orchestrator**: Routes requests to specialized agents
2. **Menu Agent**: Handles menu inquiries (FAQ-first approach)
3. **Order Processing Agent**: Builds and validates orders
4. **Issue Resolution Agent**: Resolves complaints (policy-first)

### Services

- **Context Manager**: Session lifecycle and history
- **Policy Engine**: Rule-based issue resolution
- **Intent Detection**: LLM-powered intent classification
- **FAQ Search**: Keyword-based fast responses
- **Recommendation Engine**: Complementary item suggestions
- **Audit Logger**: Comprehensive logging

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_policy_engine.py -v
```

## Database Models

- **Customer**: User profiles
- **MenuItem**: Menu with categories and dietary tags
- **Order**: Order tracking with status
- **OrderItem**: Items in each order
- **Issue**: Complaint tracking
- **Session**: Conversation state
- **FAQ**: Knowledge base
- **AuditLog**: Audit trail

## Confidence Thresholds

| Confidence | Action |
|------------|--------|
| ≥0.85 | Auto-execute |
| 0.60-0.85 | Confirm first |
| <0.60 | Clarify/escalate |

## Policy Rules

- **Missing Item**: Auto-refund if ≤$50
- **Late Delivery**: 20% credit if >30min delay (max $25)
- **Wrong Order**: Refund/replacement if ≤$75
- **Quality Issue**: 50% refund if ≤$30

## Development

Project structure:
```
customer_service_agent/
├── src/
│   ├── models/          # Database models & schemas
│   ├── services/        # Business logic & agents
│   ├── api/             # FastAPI endpoints
│   ├── data/            # Seed data generator
│   └── utils/           # LLM helpers
├── tests/               # Unit & integration tests
└── data/                # SQLite database
```

## Future Enhancements

- Real STT/TTS integration
- Advanced analytics dashboard
- Multi-channel support
- Production authentication
- Real payment processing

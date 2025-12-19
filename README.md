# MarqetFi API

A high-performance trading platform API built with FastAPI, providing secure wallet management, order execution, and real-time market data services.

## Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd marqetfi-api
make setup

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start services (PostgreSQL, Redis, RabbitMQ)
make docker-up

# 4. Run migrations
make migrate

# 5. Start application (FastAPI + Celery worker + Celery beat)
make run
```

API available at `http://localhost:8000` | Docs: `http://localhost:8000/docs`

## Architecture

![High Level Design](./assets/hld.svg)

<details>
<summary>View Mermaid Diagram</summary>

```mermaid
graph TB
    subgraph Client["Client Layer"]
        WebApp["Web Application<br/>React/Next.js"]
        MobileApp["Mobile App<br/>React Native"]
    end

    subgraph Gateway["API Gateway Layer"]
        APIGateway["API Gateway FastAPI<br/>Rate Limiting & Auth"]
    end

    subgraph Auth["Authentication & Identity"]
        AuthService["Auth Service<br/>Web2: Email/Google/Apple<br/>Web3: Wallet Connection"]
        OAuthService["OAuth Service<br/>Google & Apple OAuth"]
        WalletAuthService["Wallet Auth Service<br/>Web3 Signature Verification"]
        WalletProviderFactory["Wallet Provider Factory<br/>Privy.io / Dynamic.xyz"]
        MPCWalletService["MPC Wallet Service<br/>Wallet Creation & Management"]
    end

    subgraph Core["Core Services - Python"]
        WalletService["Wallet Service<br/>Balance & Key Management"]
        TradingService["Trading Service<br/>Order & Position Management"]
        SettlementService["Settlement Service<br/>Trade Execution"]
        PriceFeedService["Price Feed Service<br/>Real-time Market Data"]
        ProviderRouter["Provider Router<br/>Multi-Provider Routing"]
        ProviderFactory["Provider Factory<br/>Ostium / Lighter"]
    end

    subgraph Background["Background Processing"]
        CeleryWorker["Celery Worker<br/>Async Task Processing"]
        CeleryBeat["Celery Beat<br/>Scheduled Tasks"]
        TaskQueue["Task Queue<br/>RabbitMQ"]
    end

    subgraph Admin["Admin Services"]
        AdminService["Admin Service<br/>Configuration Management"]
        OstiumAdminService["Ostium Admin Service<br/>Settings & Fees Management"]
    end

    subgraph External["External Infrastructure"]
        PostgreSQL["PostgreSQL<br/>User, Trade, Wallet Data"]
        RabbitMQ["Message Queue<br/>RabbitMQ/Celery"]
        Redis["Redis Cache<br/>& Sessions"]
        Ostium["Ostium Protocol<br/>Liquidity Provider"]
        Lighter["Lighter Protocol<br/>Liquidity Provider"]
        Arbitrum["Arbitrum Network<br/>USDC Settlement"]
        PrivyAPI["Privy.io API<br/>MPC Wallet Provider"]
        DynamicAPI["Dynamic.xyz API<br/>MPC Wallet Provider"]
    end

    subgraph Support["Support Services"]
        RiskMgmt["Risk Management<br/>Limits & Margin"]
        Analytics["Analytics<br/>P&L & Reporting"]
        Monitoring["Monitoring & Logging<br/>Observability"]
    end

    WebApp --> APIGateway
    MobileApp --> APIGateway
    APIGateway --> AuthService
    APIGateway --> TradingService
    APIGateway --> AdminService

    AuthService --> OAuthService
    AuthService --> WalletAuthService
    AuthService --> MPCWalletService
    WalletAuthService --> WalletProviderFactory
    MPCWalletService --> WalletProviderFactory
    WalletProviderFactory --> PrivyAPI
    WalletProviderFactory --> DynamicAPI

    OAuthService --> PostgreSQL
    WalletAuthService --> PostgreSQL
    MPCWalletService --> PostgreSQL

    TradingService --> SettlementService
    TradingService --> PriceFeedService
    TradingService --> ProviderRouter
    TradingService --> RiskMgmt

    SettlementService --> ProviderFactory
    SettlementService --> ProviderRouter
    PriceFeedService --> ProviderFactory
    PriceFeedService --> ProviderRouter

    ProviderFactory --> Ostium
    ProviderFactory --> Lighter
    ProviderRouter --> ProviderFactory

    SettlementService --> Arbitrum
    SettlementService --> TaskQueue

    AdminService --> OstiumAdminService
    OstiumAdminService --> PostgreSQL

    WalletService --> PostgreSQL
    WalletService --> WalletProviderFactory
    WalletService --> TaskQueue

    TradingService --> PostgreSQL
    TradingService --> TaskQueue
    PriceFeedService --> Redis

    CeleryWorker --> TaskQueue
    CeleryBeat --> TaskQueue
    CeleryWorker --> PostgreSQL
    CeleryWorker --> Redis
    CeleryWorker --> ProviderFactory
    CeleryWorker --> WalletProviderFactory

    Analytics --> PostgreSQL
    Analytics --> RiskMgmt
    Analytics --> Redis

    Monitoring --> PostgreSQL
    Monitoring --> Redis
    Monitoring --> RabbitMQ

    classDef client fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef gateway fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef auth fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef core fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef background fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef admin fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef support fill:#fff9c4,stroke:#f57f17,stroke-width:2px

    class WebApp,MobileApp client
    class APIGateway gateway
    class AuthService,OAuthService,WalletAuthService,WalletProviderFactory,MPCWalletService auth
    class WalletService,TradingService,SettlementService,PriceFeedService,ProviderRouter,ProviderFactory core
    class CeleryWorker,CeleryBeat,TaskQueue background
    class AdminService,OstiumAdminService admin
    class PostgreSQL,RabbitMQ,Redis,Ostium,Lighter,Arbitrum,PrivyAPI,DynamicAPI external
    class RiskMgmt,Analytics,Monitoring support
```

</details>

## Features

- 🔐 **Secure Authentication**: Email, Google, and Apple OAuth support
- 💼 **MPC Wallet Management**: Secure multi-party computation wallet creation and management
- 📊 **Trading Services**: Order management, position tracking, and trade execution
- 💱 **Real-time Market Data**: Live price feeds with Redis caching
- ⚡ **Asynchronous Processing**: RabbitMQ/Celery for background tasks
- 🛡️ **Risk Management**: Limits, margin controls, and position monitoring
- 📈 **Analytics**: P&L calculations and comprehensive reporting
- 🔗 **Blockchain Integration**: Arbitrum Network for USDC settlement
- 💧 **Liquidity**: Ostium Protocol integration for trading liquidity

## Development

### Prerequisites

- Python 3.11+
- PostgreSQL 14+, Redis 6+, RabbitMQ 3.9+
- Docker & Docker Compose (for infrastructure)

### Common Commands

```bash
make setup          # Install dependencies and setup pre-commit hooks
make run            # Start FastAPI + Celery worker + Celery beat
make test           # Run tests with coverage
make lint           # Run all linters
make format         # Format code with black and isort
make pre-commit     # Run pre-commit hooks on all files
make docker-up      # Start infrastructure services
make docker-down    # Stop infrastructure services
make migrate        # Run database migrations
make clean          # Clean cache and build files
```

### Running Services Individually

```bash
python run.py --server-only    # FastAPI only
python run.py --worker-only    # Celery worker only
python run.py --beat-only      # Celery beat only
python run.py --no-beat        # Server + worker (no beat)
```

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit. Setup is included in `make setup`.

Hooks run:
- Code formatting (Black, Ruff)
- Import sorting (isort)
- Linting (Ruff)
- Type checking (mypy)
- File checks (trailing whitespace, large files, etc.)

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Deployment

### Docker

```bash
docker build -t marqetfi-api .
docker run -p 8000:8000 --env-file .env marqetfi-api
```

### Production Checklist

- Set `DEBUG=false`
- Use strong `SECRET_KEY`
- Configure CORS origins
- Enable database connection pooling
- Enable Redis persistence
- Configure RabbitMQ clustering
- Set up monitoring and logging
- Use HTTPS/TLS
- Implement rate limiting
- Set up backup strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make test` and `make lint`
5. Commit (pre-commit hooks will run automatically)
6. Push and open a Pull Request

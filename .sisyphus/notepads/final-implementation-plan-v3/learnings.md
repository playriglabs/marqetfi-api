# Learnings - Final Implementation Plan v3

## 2026-01-24 - Phase 0: Infrastructure Setup

### Circular FK Dependency Resolution

**Issue**: Alembic autogenerate created migration with circular foreign key dependency between `users.mpc_wallet_id` → `wallets.id` and `wallets.user_id` → `users.id`.

**Error**: `relation "wallets" does not exist` when trying to create `users` table with FK constraint to wallets.

**Solution**: Manually edited migration file to:
1. Remove `sa.ForeignKeyConstraint()` from users table creation (lines 102-105)
2. Create both tables first without circular FK
3. Add FK constraint AFTER both tables exist using `op.create_foreign_key()` (added at line 661-667)
4. Update downgrade function to drop FK constraint before dropping tables

**Pattern Discovered**: When models have circular FK dependencies, defer FK constraint creation until after all tables exist.

**Files Modified**:
- `alembic/versions/95ab60098bd3_initial_schema_with_webhooks_and_.py`

### RabbitMQ Setup

**Convention**: Use secure credentials (not default `guest:guest`)
- Username: `marqetfi`
- Password: `mqf_dev_2026_secure`

**Ports**:
- 5672: AMQP protocol
- 15672: Management UI

### Celery Broker Migration

**Pattern**: Keep Redis as result backend, use RabbitMQ as broker
- Broker: RabbitMQ (production-grade message durability)
- Backend: Redis (fast result storage)

**Configuration**:
- Change `broker=settings.REDIS_URL` → `broker=settings.CELERY_BROKER_URL`
- Keep `backend=settings.REDIS_URL` unchanged

### Migration Strategy

**Approach**: Complete regeneration from current models
- Backup old migrations to `.sisyphus/backups/alembic-old/`
- Delete all migration files except `__init__.py`
- Run `alembic revision --autogenerate` to create fresh migration
- Review generated migration for circular dependencies

### Database Schema Verification

**All tables created successfully** (21 total):
- ✅ `webhook_configurations` - ARRAY type for event_types
- ✅ `webhook_deliveries` - delivery tracking
- ✅ `orders` - with stop_price, trailing_offset, linked_order_id, is_trailing_active
- ✅ All existing tables (users, wallets, trades, positions, etc.)

**Key Findings**:
- PostgreSQL ARRAY type works correctly for webhook event_types
- Advanced order fields are nullable (except is_trailing_active which defaults to False)
- Foreign keys properly set up with CASCADE/SET NULL as designed

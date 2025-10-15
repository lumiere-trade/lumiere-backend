-- ============================================================
-- PERFORMANCE OPTIMIZATION: Composite Index for Transaction History
-- ============================================================
-- Purpose: Optimize queries for user transaction history with date sorting
-- Component: Pourtier
-- Database: pourtier_db
-- ============================================================

-- Composite index for escrow transaction queries by user with date sorting
-- This is the most common query pattern for transaction history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_escrow_tx_user_created
    ON escrow_transactions(user_id, created_at DESC);

-- Analyze table after index creation
ANALYZE escrow_transactions;

-- Verify index created
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'escrow_transactions'
  AND indexname = 'idx_escrow_tx_user_created';

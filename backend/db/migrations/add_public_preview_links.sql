-- Migration: Add public_preview_links table
-- Purpose: Store public preview links for stocks (for blog/marketing purposes)
-- Date: 2025-11-21

-- Create public_preview_links table
CREATE TABLE IF NOT EXISTS public_preview_links (
    link_id VARCHAR(255) PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL
);

-- Create index for stock_code lookup
CREATE INDEX IF NOT EXISTS idx_public_preview_stock_code
ON public_preview_links(stock_code);

-- Create index for created_by lookup
CREATE INDEX IF NOT EXISTS idx_public_preview_created_by
ON public_preview_links(created_by);

-- Verification query
-- SELECT link_id, stock_code, created_by, created_at, expires_at
-- FROM public_preview_links
-- ORDER BY created_at DESC;

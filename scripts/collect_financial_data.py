#!/usr/bin/env python3
"""
수동으로 재무 데이터 수집 (테스트용)

Usage:
    python scripts/collect_financial_data.py --type product_info
    python scripts/collect_financial_data.py --type financial_ratios
    python scripts/collect_financial_data.py --type all
"""
import argparse
import asyncio
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.crawlers.kis_product_info_collector import collect_product_info_for_all_stocks
from backend.crawlers.kis_financial_collector import collect_financial_ratios_for_all_stocks


async def main():
    parser = argparse.ArgumentParser(description='Collect financial data from KIS API')
    parser.add_argument(
        '--type',
        choices=['product_info', 'financial_ratios', 'all'],
        required=True,
        help='Type of data to collect'
    )

    args = parser.parse_args()

    if args.type in ['product_info', 'all']:
        print("📊 Collecting product info...")
        await collect_product_info_for_all_stocks()

    if args.type in ['financial_ratios', 'all']:
        print("📊 Collecting financial ratios...")
        await collect_financial_ratios_for_all_stocks()

    print("✅ Data collection completed!")


if __name__ == '__main__':
    asyncio.run(main())

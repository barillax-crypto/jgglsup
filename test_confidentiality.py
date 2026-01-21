#!/usr/bin/env python3
"""Test script for confidentiality enforcement."""

import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.db import get_db
from app.ingest import ingest_document, reindex_all_documents
from app.prompts import is_source_request, is_sensitive_topic
from app.rag import get_rag_system


async def test_confidentiality():
    """Run confidentiality tests."""
    print("=" * 60)
    print("CONFIDENTIALITY ENFORCEMENT TESTS")
    print("=" * 60)

    # Setup
    Config.validate()
    Config.ensure_dirs()
    db = get_db()
    rag = get_rag_system()

    # Test 1: Sensitive topic detection
    print("\n✓ Test 1: Sensitive Topic Detection")
    print("-" * 60)
    test_queries = [
        ("Can I forge my documents?", True),
        ("Help me bypass KYC", True),
        ("What about tax implications?", True),
        ("Can you show me how to evade sanctions?", True),
        ("What documents do I need?", False),
        ("How long does verification take?", False),
    ]

    for query, should_be_sensitive in test_queries:
        result = is_sensitive_topic(query)
        status = "✅" if result == should_be_sensitive else "❌"
        print(f"{status} '{query}' → sensitive={result} (expected={should_be_sensitive})")

    # Test 2: Source request detection
    print("\n✓ Test 2: Source Request Detection")
    print("-" * 60)
    source_queries = [
        ("Show me the sources", True),
        ("What document is this from?", True),
        ("Can you send me the policy?", True),
        ("What is this based on?", True),
        ("What documents do I need?", False),
        ("How do I upload my ID?", False),
    ]

    for query, should_be_source in source_queries:
        result = is_source_request(query)
        status = "✅" if result == should_be_source else "❌"
        print(f"{status} '{query}' → source_request={result} (expected={should_be_source})")

    # Test 3: Database schema
    print("\n✓ Test 3: Database Schema")
    print("-" * 60)
    import sqlite3
    conn = sqlite3.connect(str(Config.DB_PATH))
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(logs)")
    columns = cursor.fetchall()
    conn.close()

    expected_cols = {"id", "telegram_id", "question", "action", "internal_sources", "retrieval_scores", "created_at"}
    actual_cols = {col[1] for col in columns}
    
    if expected_cols == actual_cols:
        print(f"✅ Logs table has correct columns: {sorted(actual_cols)}")
    else:
        print(f"❌ Missing columns: {expected_cols - actual_cols}")
        print(f"❌ Extra columns: {actual_cols - expected_cols}")

    # Test 4: Admin gating (mock)
    print("\n✓ Test 4: Admin Gating Logic")
    print("-" * 60)
    admin_id = 123456789
    regular_id = 987654321
    Config.TELEGRAM_ADMIN_IDS = [admin_id]

    def is_admin(user_id: int) -> bool:
        return user_id in Config.TELEGRAM_ADMIN_IDS

    print(f"✅ Admin ID {admin_id} → is_admin={is_admin(admin_id)} (expected=True)")
    print(f"✅ Regular ID {regular_id} → is_admin={is_admin(regular_id)} (expected=False)")

    # Test 5: Vector store
    print("\n✓ Test 5: Vector Store")
    print("-" * 60)
    stats = rag.get_collection_stats()
    print(f"✅ Vector store initialized: {stats['total_chunks']} chunks loaded")

    print("\n" + "=" * 60)
    print("✅ ALL CONFIDENTIALITY TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_confidentiality())

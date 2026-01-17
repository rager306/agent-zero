#!/bin/bash
# Langchain 1.x Migration Script for Agent Zero
# Generated: 2026-01-17
# Updated with official docs best practices (Ref MCP)
#
# USAGE: ./report/migrate_langchain.sh [--dry-run]
#
# This script performs in-place replacement of deprecated langchain imports.
# Use --dry-run to preview changes without modifying files.

set -e

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No files will be modified"
    echo ""
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📦 Langchain 1.x Migration Script (2025 Best Practices)"
echo "========================================================"
echo "Project: $PROJECT_ROOT"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

migrate_file() {
    local file="$1"
    local pattern="$2"
    local replacement="$3"
    local description="$4"

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${YELLOW}📝 $file${NC}"
        echo "   $description"

        if [[ "$DRY_RUN" == true ]]; then
            echo -e "   ${GREEN}Would replace:${NC} $pattern"
            echo -e "   ${GREEN}With:${NC} $replacement"
        else
            sed -i "s|$pattern|$replacement|g" "$file"
            echo -e "   ${GREEN}✅ Applied${NC}"
        fi
        echo ""
        return 0
    fi
    return 1
}

echo "🔄 Migrating imports..."
echo ""

# ============================================================
# 1. python/helpers/call_llm.py
# ============================================================
migrate_file "python/helpers/call_llm.py" \
    "from langchain\.prompts import" \
    "from langchain_core.prompts import" \
    "langchain.prompts → langchain_core.prompts"

migrate_file "python/helpers/call_llm.py" \
    "from langchain\.schema import AIMessage" \
    "from langchain_core.messages import AIMessage" \
    "langchain.schema → langchain_core.messages"

# ============================================================
# 2. python/helpers/memory.py
# CRITICAL: CacheBackedEmbeddings moved to langchain-classic!
# Source: https://docs.langchain.com/oss/python/integrations/text_embedding#caching
# ============================================================
migrate_file "python/helpers/memory.py" \
    "from langchain\.storage import" \
    "from langchain_classic.storage import" \
    "langchain.storage → langchain_classic.storage (official 2025)"

migrate_file "python/helpers/memory.py" \
    "from langchain\.embeddings import CacheBackedEmbeddings" \
    "from langchain_classic.embeddings import CacheBackedEmbeddings" \
    "CacheBackedEmbeddings → langchain_classic (official 2025)"

# ============================================================
# 3. python/helpers/vector_db.py
# Same pattern as memory.py
# ============================================================
migrate_file "python/helpers/vector_db.py" \
    "from langchain\.storage import" \
    "from langchain_classic.storage import" \
    "langchain.storage → langchain_classic.storage"

migrate_file "python/helpers/vector_db.py" \
    "from langchain\.embeddings import CacheBackedEmbeddings" \
    "from langchain_classic.embeddings import CacheBackedEmbeddings" \
    "CacheBackedEmbeddings → langchain_classic"

# ============================================================
# 4. python/helpers/document_query.py
# ============================================================
migrate_file "python/helpers/document_query.py" \
    "from langchain\.schema import SystemMessage, HumanMessage" \
    "from langchain_core.messages import SystemMessage, HumanMessage" \
    "langchain.schema → langchain_core.messages"

migrate_file "python/helpers/document_query.py" \
    "from langchain\.text_splitter import" \
    "from langchain_text_splitters import" \
    "langchain.text_splitter → langchain_text_splitters"

# ============================================================
# 5. models.py
# ============================================================
migrate_file "models.py" \
    "from langchain\.embeddings\.base import Embeddings" \
    "from langchain_core.embeddings import Embeddings" \
    "langchain.embeddings.base → langchain_core.embeddings"

echo "========================================================"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}🔍 Dry run complete. Run without --dry-run to apply changes.${NC}"
else
    echo -e "${GREEN}✅ Migration complete!${NC}"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Install new dependencies:"
    echo "      uv add langchain-classic langchain-text-splitters"
    echo "   2. Update existing dependencies:"
    echo "      uv add --upgrade langchain langchain-core langchain-community"
    echo "   3. Run tests:"
    echo "      python -m pytest tests/ -v"
fi

# Langchain 1.x Migration Best Practices (2025-2026)

**Источник**: Официальная документация Langchain (docs.langchain.com)  
**Дата**: 2026-01-17  
**Релевантность**: Langchain 1.0+ LTS

---

## Ключевые изменения в Langchain 1.x

### Новая структура пакетов

```
┌─────────────────────────────────────────────────────────────────┐
│                      LANGCHAIN 1.x ECOSYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│  langchain          │  Упрощённый пакет (agents, tools, etc.)  │
│  langchain-core     │  Базовые абстракции (messages, docs)     │
│  langchain-community│  Интеграции (FAISS, loaders, etc.)       │
│  langchain-classic  │  Legacy код (chains, CacheBackedEmbed.)  │
│  langchain-text-splitters │  Text splitters                    │
│  langchain-openai   │  OpenAI интеграция                       │
│  langchain-anthropic│  Anthropic интеграция                    │
└─────────────────────────────────────────────────────────────────┘
```

### Что доступно в `langchain` v1

| Модуль | Содержимое | Примечание |
|--------|-----------|------------|
| `langchain.agents` | `create_agent`, `AgentState` | Создание агентов |
| `langchain.messages` | Message types, `trim_messages` | Re-export из langchain-core |
| `langchain.tools` | `@tool`, `BaseTool` | Re-export из langchain-core |
| `langchain.chat_models` | `init_chat_model`, `BaseChatModel` | Унифицированная инициализация |
| `langchain.embeddings` | `init_embeddings`, `Embeddings` | Базовые embeddings |

---

## Критические изменения для Agent Zero

### 1. CacheBackedEmbeddings → langchain-classic

**Официальная документация подтверждает**: `CacheBackedEmbeddings` перемещён в `langchain-classic`.

```python
# ❌ СТАРЫЙ КОД (не работает в v1)
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore

# ✅ НОВЫЙ КОД (langchain 1.x)
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore
```

**Затронутые файлы**:
- `python/helpers/memory.py:3-4`
- `python/helpers/vector_db.py:10,14`

### 2. Text Splitters → отдельный пакет

```bash
pip install langchain-text-splitters
```

```python
# ❌ СТАРЫЙ КОД
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ✅ НОВЫЙ КОД
from langchain_text_splitters import RecursiveCharacterTextSplitter
```

**Затронутые файлы**:
- `python/helpers/document_query.py:28`

### 3. Messages и Schema → langchain-core

```python
# ❌ СТАРЫЙ КОД
from langchain.schema import AIMessage, SystemMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate

# ✅ НОВЫЙ КОД
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
```

**Затронутые файлы**:
- `python/helpers/call_llm.py:2-7`
- `python/helpers/document_query.py:22`

### 4. Embeddings Base Class → langchain-core

```python
# ❌ СТАРЫЙ КОД
from langchain.embeddings.base import Embeddings

# ✅ НОВЫЙ КОД
from langchain_core.embeddings import Embeddings
```

**Затронутые файлы**:
- `models.py:41`

### 5. FAISS остаётся в langchain-community ✅

```python
# ✅ БЕЗ ИЗМЕНЕНИЙ
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
```

---

## Полная таблица миграции для Agent Zero

| Старый импорт | Новый импорт | Пакет |
|--------------|--------------|-------|
| `langchain.prompts` | `langchain_core.prompts` | langchain-core |
| `langchain.schema.AIMessage` | `langchain_core.messages.AIMessage` | langchain-core |
| `langchain.schema.SystemMessage` | `langchain_core.messages.SystemMessage` | langchain-core |
| `langchain.schema.HumanMessage` | `langchain_core.messages.HumanMessage` | langchain-core |
| `langchain.embeddings.base.Embeddings` | `langchain_core.embeddings.Embeddings` | langchain-core |
| `langchain.embeddings.CacheBackedEmbeddings` | `langchain_classic.embeddings.CacheBackedEmbeddings` | langchain-classic |
| `langchain.storage.LocalFileStore` | `langchain_classic.storage.LocalFileStore` | langchain-classic |
| `langchain.storage.InMemoryByteStore` | `langchain_classic.storage.InMemoryByteStore` | langchain-classic |
| `langchain.text_splitter` | `langchain_text_splitters` | langchain-text-splitters |

---

## Рекомендуемые зависимости

### pyproject.toml / requirements.txt

```toml
[project.dependencies]
langchain = ">=1.0.0"
langchain-core = ">=0.3.0"
langchain-community = ">=0.4.0"
langchain-classic = ">=0.1.0"        # ⚠️ НОВЫЙ пакет!
langchain-text-splitters = ">=0.3.0"
faiss-cpu = ">=1.7.4"
```

### Установка через UV

```bash
uv add langchain langchain-core langchain-community langchain-classic langchain-text-splitters
```

---

## LTS и поддержка версий

### Политика Long-Term Support

| Версия | Статус | Поддержка до |
|--------|--------|--------------|
| **Langchain 1.x** | ACTIVE (LTS) | После 2.0 → MAINTENANCE 1+ год |
| **Langchain 0.3** | MAINTENANCE | Декабрь 2026 |

### Semver гарантии

- **Minor releases** (1.0 → 1.1): Новые фичи, без breaking changes
- **Patch releases** (1.0.0 → 1.0.1): Bug fixes
- **Major releases** (1.x → 2.0): Breaking changes

### Особенность langchain-community

> ⚠️ `langchain-community` версии 0.4 **не следует** strict semver из-за характера community-контрибьюций. Возможны breaking changes в minor releases.

---

## План миграции для Agent Zero

### Этап 1: Добавить новые зависимости

```bash
# Добавить langchain-classic (критично!)
uv add langchain-classic langchain-text-splitters

# Обновить существующие
uv add --upgrade langchain langchain-core langchain-community
```

### Этап 2: Обновить импорты

**Порядок файлов по приоритету:**

1. `python/helpers/memory.py` — CacheBackedEmbeddings, LocalFileStore
2. `python/helpers/vector_db.py` — InMemoryByteStore, CacheBackedEmbeddings
3. `python/helpers/call_llm.py` — prompts, schema
4. `python/helpers/document_query.py` — schema, text_splitter
5. `models.py` — embeddings.base

### Этап 3: Тестирование

```bash
# Проверить импорты
python -c "
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore, InMemoryByteStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.embeddings import Embeddings
print('✅ All imports successful')
"

# Запустить тесты
python -m pytest tests/ -v
```

---

## Важные замечания

### 1. langchain-classic — временное решение

`langchain-classic` предоставляет обратную совместимость, но рекомендуется постепенно переходить на новые паттерны:

- Legacy chains (`LLMChain`) → LangGraph
- `CacheBackedEmbeddings` → Рассмотреть альтернативы кэширования

### 2. Мониторинг изменений в langchain-community

Следить за changelog `langchain-community`, так как там возможны breaking changes.

### 3. Архивная документация

Старая документация доступна:
- [v0.3 docs](https://github.com/langchain-ai/langchain/tree/v0.3/docs/docs)
- [v0.3 API reference](https://reference.langchain.com/v0.3/python/)

---

## Ссылки

- [LangChain v1 Migration Guide](https://docs.langchain.com/oss/python/migrate/langchain-v1)
- [Release Policy](https://docs.langchain.com/oss/python/release-policy)
- [FAISS Integration](https://docs.langchain.com/oss/python/integrations/vectorstores/faiss)
- [Embedding Caching](https://docs.langchain.com/oss/python/integrations/text_embedding#caching)
- [Text Splitters](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)

---

*Отчёт составлен на основе официальной документации Langchain через Ref MCP*

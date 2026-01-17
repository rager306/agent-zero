# Langchain Usage Analysis Report

**Дата анализа**: 2026-01-17  
**Проект**: Agent Zero  
**Ветка**: `experiment/uv-python313`  
**Текущая версия langchain**: 0.3.x (требуется миграция на 1.x)

---

## Содержание

1. [Обзор](#обзор)
2. [Затронутые файлы](#затронутые-файлы)
3. [Детальный анализ по файлам](#детальный-анализ-по-файлам)
4. [Таблица несовместимостей](#таблица-несовместимостей)
5. [Приоритеты миграции](#приоритеты-миграции)
6. [Рекомендации](#рекомендации)

---

## Обзор

В проекте Agent Zero используются следующие пакеты экосистемы Langchain:

| Пакет | Статус | Использование |
|-------|--------|---------------|
| `langchain` | ⚠️ Deprecated imports | Основные импорты (prompts, schema, storage) |
| `langchain_core` | ✅ Актуально | Messages, Documents, Language Models |
| `langchain_community` | ✅ Актуально | FAISS, Document Loaders, Transformers |
| `langchain_unstructured` | ✅ Актуально | UnstructuredLoader |

**Найдено проблем несовместимости**: 12 импортов требуют изменения  
**Затронуто файлов**: 6

---

## Затронутые файлы

### Файлы с устаревшими импортами (требуют исправления)

| # | Файл | Строки | Проблемные импорты | Приоритет |
|---|------|--------|-------------------|-----------|
| 1 | `python/helpers/call_llm.py` | 2-7 | `langchain.prompts`, `langchain.schema` | 🔴 Высокий |
| 2 | `python/helpers/memory.py` | 3-4 | `langchain.storage`, `langchain.embeddings` | 🔴 Высокий |
| 3 | `python/helpers/vector_db.py` | 10-14 | `langchain.storage`, `langchain.embeddings` | 🔴 Высокий |
| 4 | `python/helpers/document_query.py` | 22, 28 | `langchain.schema`, `langchain.text_splitter` | 🟡 Средний |
| 5 | `models.py` | 41 | `langchain.embeddings.base` | 🟡 Средний |

### Файлы с актуальными импортами (без изменений)

| # | Файл | Импорты |
|---|------|---------|
| 1 | `agent.py` | `langchain_core.prompts`, `langchain_core.messages` |
| 2 | `python/helpers/history.py` | `langchain_core.messages` |
| 3 | `python/helpers/memory_consolidation.py` | `langchain_core.documents` |
| 4 | `python/api/memory_dashboard.py` | `langchain_core.documents` |
| 5 | `python/helpers/knowledge_import.py` | `langchain_community.document_loaders` |

---

## Детальный анализ по файлам

### 1. python/helpers/call_llm.py

**Расположение**: `python/helpers/call_llm.py:2-11`

```python
# ТЕКУЩИЙ КОД (проблемный)
from langchain.prompts import (          # Строка 2 ❌
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)

from langchain.schema import AIMessage   # Строка 7 ❌
from langchain_core.messages import HumanMessage, SystemMessage  # Строка 8 ✅
```

**Проблема**: Модуль `langchain.prompts` перемещён в `langchain_core.prompts` в версии 1.x

**Исправление**:
```python
from langchain_core.prompts import (     # ✅ Исправлено
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # ✅ Объединено
```

---

### 2. python/helpers/memory.py

**Расположение**: `python/helpers/memory.py:3-4`

```python
# ТЕКУЩИЙ КОД (проблемный)
from langchain.storage import InMemoryByteStore, LocalFileStore  # ❌
from langchain.embeddings import CacheBackedEmbeddings            # ❌
```

**Проблема**: 
- `langchain.storage` перемещён в `langchain_community.storage`
- `langchain.embeddings.CacheBackedEmbeddings` перемещён в `langchain.embeddings.CacheBackedEmbeddings` (остаётся) или `langchain_community.embeddings`

**Исправление**:
```python
from langchain_community.storage import InMemoryByteStore, LocalFileStore  # ✅
from langchain.embeddings import CacheBackedEmbeddings  # ✅ (проверить совместимость)
```

**Примечание**: `CacheBackedEmbeddings` может потребовать дополнительной проверки в langchain 1.x

---

### 3. python/helpers/vector_db.py

**Расположение**: `python/helpers/vector_db.py:10-14`

```python
# ТЕКУЩИЙ КОД (проблемный)
from langchain.storage import InMemoryByteStore           # Строка 10 ❌
from langchain.embeddings import CacheBackedEmbeddings    # Строка 14 ❌
```

**Исправление**:
```python
from langchain_community.storage import InMemoryByteStore           # ✅
from langchain.embeddings import CacheBackedEmbeddings              # ✅ (требует проверки)
```

---

### 4. python/helpers/document_query.py

**Расположение**: `python/helpers/document_query.py:22, 28`

```python
# ТЕКУЩИЙ КОД (проблемный)
from langchain.schema import SystemMessage, HumanMessage  # Строка 22 ❌
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Строка 28 ❌
```

**Проблема**:
- `langchain.schema` перемещён в `langchain_core.messages`
- `langchain.text_splitter` выделен в отдельный пакет `langchain_text_splitters`

**Исправление**:
```python
from langchain_core.messages import SystemMessage, HumanMessage  # ✅
from langchain_text_splitters import RecursiveCharacterTextSplitter  # ✅
```

**Зависимость**: Требуется добавить `langchain-text-splitters` в requirements.txt

---

### 5. models.py

**Расположение**: `models.py:41`

```python
# ТЕКУЩИЙ КОД (проблемный)
from langchain.embeddings.base import Embeddings  # Строка 41 ❌
```

**Исправление**:
```python
from langchain_core.embeddings import Embeddings  # ✅
```

---

## Таблица несовместимостей

| Устаревший импорт | Новый импорт (Langchain 1.x) | Пакет для установки |
|-------------------|------------------------------|---------------------|
| `langchain.prompts` | `langchain_core.prompts` | langchain-core |
| `langchain.schema` | `langchain_core.messages` | langchain-core |
| `langchain.schema.Document` | `langchain_core.documents.Document` | langchain-core |
| `langchain.storage` | `langchain_community.storage` | langchain-community |
| `langchain.embeddings.base` | `langchain_core.embeddings` | langchain-core |
| `langchain.text_splitter` | `langchain_text_splitters` | langchain-text-splitters |
| `langchain.chat_models` | `langchain_community.chat_models` | langchain-community |

---

## Приоритеты миграции

### 🔴 Высокий приоритет (критические файлы)

1. **python/helpers/memory.py** - Ключевой модуль для работы с памятью агента
2. **python/helpers/vector_db.py** - Ядро векторной базы данных
3. **python/helpers/call_llm.py** - Основной модуль вызова LLM

### 🟡 Средний приоритет

4. **python/helpers/document_query.py** - Загрузка и обработка документов
5. **models.py** - Конфигурация моделей

### 🟢 Низкий приоритет

- Файлы с актуальными импортами не требуют изменений

---

## Рекомендации

### 1. Последовательность миграции

```
1. Обновить requirements.txt / pyproject.toml
   ├── langchain>=1.0.0
   ├── langchain-core>=0.3.0
   ├── langchain-community>=0.3.0
   └── langchain-text-splitters>=0.3.0

2. Исправить импорты в порядке приоритета:
   ├── python/helpers/call_llm.py
   ├── python/helpers/memory.py
   ├── python/helpers/vector_db.py
   ├── python/helpers/document_query.py
   └── models.py

3. Запустить тесты:
   └── python -m pytest tests/
```

### 2. Скрипт автоматической миграции

```bash
# Поиск и замена устаревших импортов
find python/ -name "*.py" -exec sed -i \
  -e 's/from langchain\.prompts/from langchain_core.prompts/g' \
  -e 's/from langchain\.schema import/from langchain_core.messages import/g' \
  -e 's/from langchain\.storage/from langchain_community.storage/g' \
  -e 's/from langchain\.embeddings\.base/from langchain_core.embeddings/g' \
  -e 's/from langchain\.text_splitter/from langchain_text_splitters/g' \
  {} \;
```

### 3. Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Несовместимость API FAISS | Средняя | Проверить методы `add_documents`, `similarity_search` |
| Изменения в CacheBackedEmbeddings | Высокая | Протестировать кэширование embeddings |
| Breaking changes в Document loaders | Низкая | langchain-community сохраняет совместимость |

### 4. Тестирование после миграции

```bash
# Проверить импорты
python -c "from python.helpers.memory import Memory; print('✅ memory.py')"
python -c "from python.helpers.vector_db import VectorDB; print('✅ vector_db.py')"
python -c "from python.helpers.call_llm import call_llm; print('✅ call_llm.py')"
python -c "from python.helpers.document_query import DocumentQueryStore; print('✅ document_query.py')"
python -c "from models import get_model; print('✅ models.py')"

# Запустить полные тесты
python -m pytest tests/ -v
```

---

## Ссылки

- [Langchain 1.0 Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [Langchain Core Documentation](https://api.python.langchain.com/en/latest/langchain_core.html)
- [Langchain Community Documentation](https://api.python.langchain.com/en/latest/langchain_community.html)

---

*Отчёт сгенерирован автоматически с использованием Serena MCP*

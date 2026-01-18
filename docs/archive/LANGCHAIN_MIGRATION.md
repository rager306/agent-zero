# Langchain 1.x Migration Issues

**Дата**: 2026-01-17
**Ветка**: `experiment/uv-python313`
**Версия langchain**: 0.3.x → 1.2.x

## Проблема

При обновлении до Python 3.13 потребовалось обновить langchain до версии 1.x.
В langchain 1.x изменилась структура модулей, что привело к broken imports.

## Затронутые файлы

### python/helpers/call_llm.py
```python
# Строка 2-5: Не найден модуль
from langchain.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
```
**Решение**: 
```python
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
```

### python/helpers/knowledge.py (предположительно)
```python
# Не найдены модули:
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from langchain.schema import Document
```
**Решение**:
```python
from langchain.embeddings import CacheBackedEmbeddings  # остаётся
from langchain_community.storage import LocalFileStore
from langchain_core.documents import Document
```

## Изменения API в Langchain 1.x

| Старый путь | Новый путь |
|-------------|------------|
| `langchain.prompts` | `langchain_core.prompts` |
| `langchain.schema.Document` | `langchain_core.documents.Document` |
| `langchain.storage` | `langchain_community.storage` |
| `langchain.embeddings` | `langchain_community.embeddings` |
| `langchain.chat_models` | `langchain_community.chat_models` |
| `langchain.llms` | `langchain_community.llms` |

## Новые зависимости

Langchain 1.x автоматически добавил:
- `langgraph` - граф-based оркестрация агентов
- `langgraph-checkpoint` - сохранение состояния
- `langgraph-prebuilt` - готовые компоненты
- `langgraph-sdk` - SDK
- `langchain-classic` - совместимость со старым API

## Команды для поиска всех проблемных импортов

```bash
# Найти все langchain импорты
grep -rn "from langchain\." python/ --include="*.py"

# Найти конкретные проблемные модули
grep -rn "from langchain.prompts" python/
grep -rn "from langchain.schema" python/
grep -rn "from langchain.storage" python/
grep -rn "from langchain.embeddings" python/
```

## Рекомендации

1. Проверить каждый файл с langchain импортами
2. Обновить импорты согласно таблице выше
3. Протестировать функциональность knowledge base и RAG
4. Проверить совместимость с langchain-unstructured 1.0.1

## Ссылки

- [Langchain Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [Langchain 1.0 Release Notes](https://blog.langchain.dev/langchain-v01/)

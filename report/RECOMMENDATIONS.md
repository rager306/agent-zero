# Рекомендации по миграции Langchain 1.x

## Краткие выводы

### Текущее состояние
- **5 файлов** требуют исправления импортов
- **12 устаревших импортов** обнаружено
- **5 файлов** уже используют актуальные импорты (без изменений)

### Оценка сложности: 🟡 Средняя

Миграция затрагивает только импорты — API классов и функций остаётся совместимым.

---

## Рекомендованный план действий

### Этап 1: Подготовка (5 мин)

```bash
# Создать ветку для миграции
git checkout -b feature/langchain-1x-migration

# Обновить зависимости в pyproject.toml
uv add langchain-text-splitters
```

### Этап 2: Автоматическая миграция (2 мин)

```bash
# Предпросмотр изменений
./report/migrate_langchain.sh --dry-run

# Применить изменения
./report/migrate_langchain.sh
```

### Этап 3: Ручная проверка (10 мин)

Проверить файлы с особым вниманием:

1. **python/helpers/memory.py** — критичный модуль
   - Проверить `CacheBackedEmbeddings` совместимость
   - Проверить `LocalFileStore` поведение

2. **python/helpers/vector_db.py** — векторная БД
   - Проверить FAISS интеграцию
   - Проверить `InMemoryDocstore`

### Этап 4: Тестирование (15 мин)

```bash
# Проверить импорты
python -c "
from python.helpers.memory import Memory
from python.helpers.vector_db import VectorDB
from python.helpers.call_llm import call_llm
from python.helpers.document_query import DocumentQueryStore
print('✅ All imports successful')
"

# Запустить тесты
python -m pytest tests/ -v

# Запустить приложение
python run_ui.py
```

### Этап 5: Коммит и PR

```bash
git add -A
git commit -m "Migrate to langchain 1.x module structure"
git push origin feature/langchain-1x-migration
```

---

## Потенциальные проблемы

### 1. CacheBackedEmbeddings

**Риск**: Изменение API в langchain 1.x

**Проверка**:
```python
from langchain.embeddings import CacheBackedEmbeddings
# Если ImportError → использовать:
from langchain_community.embeddings import CacheBackedEmbeddings
```

### 2. Text Splitters

**Риск**: Новый пакет не установлен

**Решение**:
```bash
uv add langchain-text-splitters
# или
pip install langchain-text-splitters
```

### 3. FAISS совместимость

**Риск**: Изменения в `langchain_community.vectorstores.FAISS`

**Проверка**: Методы `add_documents`, `similarity_search`, `delete` должны работать идентично.

---

## Альтернативные подходы

### Вариант A: Постепенная миграция (рекомендуется)
- Исправлять файлы по одному
- Тестировать после каждого изменения
- Минимальный риск регрессий

### Вариант B: Полная миграция за раз
- Использовать скрипт `migrate_langchain.sh`
- Быстрее, но требует тщательного тестирования
- Подходит если есть хорошее тестовое покрытие

### Вариант C: Использование langchain-classic
- `pip install langchain-classic`
- Обеспечивает обратную совместимость
- Временное решение, не рекомендуется для продакшена

---

## Полезные команды

```bash
# Найти все оставшиеся устаревшие импорты
grep -rn "from langchain\." python/ --include="*.py" | grep -v "langchain_"

# Проверить установленные версии
pip show langchain langchain-core langchain-community langchain-text-splitters

# Запустить только тесты связанные с памятью
python -m pytest tests/ -k "memory" -v
```

---

## Контакты и ресурсы

- [Langchain Migration Guide](https://python.langchain.com/docs/versions/migrating_chains/)
- [Langchain 1.0 Changelog](https://github.com/langchain-ai/langchain/releases)
- [Agent Zero Issues](https://github.com/frdel/agent-zero/issues)

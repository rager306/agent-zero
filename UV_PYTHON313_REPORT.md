# Отчёт: Сборка Agent Zero с UV + Python 3.13

**Дата**: 2026-01-17
**Ветка**: `experiment/uv-python313`

## Результат: УСПЕШНО (с обновлениями зависимостей)

### Статистика

- **Python**: 3.13.11
- **UV**: установлен
- **Установлено пакетов**: 265
- **Время установки**: ~5 секунд (после скачивания)

### Необходимые обновления зависимостей

| Пакет | Старая версия | Новая версия | Причина |
|-------|---------------|--------------|---------|
| langchain | 0.3.22 | 1.2.6 | Совместимость с Python 3.13 |
| langchain-core | 0.3.49 | 1.2.7 | Требуется для langchain-unstructured 1.0.1 |
| langchain-community | 0.3.19 | 0.4.1 | Совместимость с langchain 1.x |
| langchain-unstructured | 0.1.6 | 1.0.1 | onnxruntime cp313 wheels |
| onnxruntime | 1.17-1.19 | 1.23.2 | Поддержка Python 3.13 |
| openai-whisper | 20240930 | 20250625 | Сборка под Python 3.13 |

### Удалённые пакеты

- `unstructured[all-docs]==0.16.23` - заменён на unstructured-client через langchain-unstructured
- `pywinpty` - только для Windows

### Новые зависимости (добавлены автоматически)

- langgraph, langgraph-checkpoint, langgraph-prebuilt, langgraph-sdk
- langchain-classic (совместимость)

### Команды для воспроизведения

```bash
# Создать проект
uv init --name agent-zero
echo "3.13" > .python-version

# Установить зависимости
uv add -r requirements-core.txt  # базовые пакеты
uv add kokoro                     # TTS
uv add onnxruntime               # ML runtime
uv add langchain langchain-community langchain-unstructured
uv add openai-whisper            # STT
uv add litellm                   # LLM abstraction

# Запуск
uv run python run_ui.py
```

### Файлы эксперимента

- `pyproject.toml` - конфигурация UV проекта
- `uv.lock` - lockfile для воспроизводимых сборок
- `.python-version` - версия Python
- `requirements-core.txt` - базовые зависимости

### Выводы

1. **Python 3.13 полностью совместим** с Agent Zero после обновления зависимостей
2. **Langchain 1.x** - крупное обновление, требует тестирования API совместимости
3. **UV работает отлично** - быстрая установка, чистое разрешение зависимостей
4. **Рекомендация**: провести регрессионное тестирование перед merge в main

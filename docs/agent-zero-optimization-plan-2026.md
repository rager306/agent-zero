# План оптимизации Agent Zero на 2026 год

> Документ создан: 2026-01-16
> Исследование проведено с использованием 5 параллельных агентов

---

## Содержание

1. [Сводная таблица приоритетов](#сводная-таблица-приоритетов)
2. [LLM Кэширование](#1-llm-кэширование)
3. [Python 3.13 + UV Package Manager](#2-python-313--uv-package-manager)
4. [Bun вместо NodeJS](#3-bun-вместо-nodejs)
5. [SearXNG Оптимизация](#4-searxng-оптимизация)
6. [Контейнер Оптимизация](#5-контейнер-оптимизация)
7. [Чек-лист для внедрения](#чек-лист-для-внедрения)

---

## Сводная таблица приоритетов

| Направление | Приоритет | Сложность | Ожидаемый эффект |
|-------------|-----------|-----------|------------------|
| **LLM Кэширование** | 🔴 Высокий | Низкая | Снижение затрат 50-90% |
| **UV Package Manager** | 🔴 Высокий | Низкая | Ускорение установки 10-100x |
| **Python 3.13 + JIT** | 🟡 Средний | Средняя | Ускорение 5-30% |
| **SearXNG оптимизация** | 🟡 Средний | Низкая | Ускорение поиска 2-3x |
| **Bun вместо NodeJS** | 🟡 Средний | Средняя | Ускорение холодного старта 5-8x |
| **Контейнер оптимизация** | 🟢 Низкий | Высокая | Уменьшение образа 50% |
| **Python 3.13 Free-Threading** | 🟢 Низкий | Высокая | Параллельность 2-4x (эксперим.) |

---

## 1. LLM Кэширование

### 1.1 Обзор стратегий кэширования

LLM кэширование — **самый эффективный способ оптимизации** с точки зрения ROI. Включает три уровня:

1. **Provider Prompt Caching** — кэширование на стороне провайдера (Anthropic, OpenAI, etc.)
2. **Response Caching** — кэширование полных ответов (Redis, In-Memory)
3. **Semantic Caching** — кэширование по семантической близости запросов

### 1.2 LiteLLM Caching Options

LiteLLM (используется в Agent Zero) поддерживает множество бэкендов для кэширования:

| Тип кэша | Применение | Сложность настройки |
|----------|------------|---------------------|
| **In-Memory** | Single-process, разработка | Минимальная |
| **Redis** | Распределённый, production | Средняя |
| **Disk** | Персистентный локальный | Низкая |
| **S3/GCS/Azure Blob** | Cloud-native деплой | Средняя |
| **Redis Semantic** | Similarity-based кэширование | Высокая |
| **Qdrant Semantic** | Vector database кэширование | Высокая |

#### Конфигурация Redis (рекомендуется для Production)

```yaml
litellm_settings:
  cache: True
  cache_params:
    type: redis
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
    ttl: 600  # 10 минут
```

**Важно**: НЕ используйте `redis_url` в production — используйте отдельные host, port, password для лучшей производительности.

#### In-Memory + Redis Hybrid (LiteLLM v1.75.5+)

LiteLLM v1.75.5 ввёл in-memory кэширование для Redis запросов, снижая latency с ~100ms до sub-1ms на cache hits. Система сначала проверяет in-memory, затем Redis.

#### Семантическое кэширование с Redis

```python
import litellm
from litellm import Cache

litellm.cache = Cache(
    type="redis-semantic",
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    similarity_threshold=0.8,
    ttl=120,
    redis_semantic_cache_embedding_model="text-embedding-ada-002",
)
```

**Требования**: redis-py >= 4.2.0, модуль RedisSearch.

#### Контроль кэша на уровне запроса

```python
# Обойти кэш для этого запроса
response = completion(..., cache={"no-cache": True})

# Не сохранять ответ
response = completion(..., cache={"no-store": True})

# Кастомный TTL
response = completion(..., cache={"ttl": 300})
```

### 1.3 GPTCache — Семантическое кэширование

[GPTCache](https://github.com/zilliztech/GPTCache) — наиболее зрелая библиотека семантического кэширования:

- **Производительность**: 2-10x быстрее ответы, до 100x снижение latency
- **Cache Hit Rates**: 61.6-68.8% с 97%+ точностью положительных хитов
- **Адаптивные пороги**: Статический порог 0.8 работает плохо; рекомендуются VectorQ адаптивные пороги

#### Поддерживаемые бэкенды

| Категория | Опции |
|-----------|-------|
| **Vector Stores** | Milvus, Faiss, Chroma, Qdrant, Weaviate, PGVector |
| **Cache Storage** | SQLite, PostgreSQL, MySQL, Redis, DynamoDB |
| **Embeddings** | OpenAI, ONNX, Hugging Face, Cohere, SentenceTransformers |
| **Eviction** | LRU, FIFO, LFU, Random |

#### Быстрая интеграция

```python
from gptcache import cache
from gptcache.adapter import openai

cache.init()
cache.set_openai_key()
# Все последующие вызовы OpenAI автоматически кэшируются
```

### 1.4 Prompt Caching на уровне провайдера

| Провайдер | Экономия | Снижение Latency | Конфигурация |
|-----------|----------|------------------|--------------|
| **Anthropic** | До 90% | До 85% | Явный `cache_control` |
| **OpenAI** | ~50% | Автоматически | Автоматически (1024+ токенов) |
| **DeepSeek** | ~50% | Автоматически | Автоматически |
| **Gemini** | 75% reads | ~3-5 мин TTL | Implicit (auto) |

#### Конфигурация Anthropic

```json
{
  "messages": [
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "System instructions and large context...",
          "cache_control": { "type": "ephemeral", "ttl": "1h" }
        }
      ]
    }
  ]
}
```

- **5-minute TTL**: По умолчанию, обновляется при каждом использовании
- **1-hour TTL**: Для агентов, работающих дольше 5 минут между вызовами
- **Лимит**: Максимум 4 cache breakpoints на запрос

### 1.5 OpenRouter Caching

OpenRouter автоматически маршрутизирует к провайдерам с warm caches.

**Провайдеры с auto-caching**:
- Grok
- Moonshot AI
- Groq
- DeepSeek

**Отслеживание использования кэша**:
```json
{
  "usage": { "include": true }
}
```

Ответ включает поле `cache_discount` с показателем экономии.

### 1.6 Рекомендации для Agent Zero

#### Tier 1: Немедленное внедрение (низкие усилия, высокий эффект)

1. **Включить Provider Prompt Caching**
   - Добавить `cache_control` breakpoints для системных промптов
   - Использовать 1-hour TTL для длительных сессий
   - Разместить tool definitions и статический контекст в начале промптов

2. **Настроить LiteLLM Response Caching**
   ```yaml
   litellm_settings:
     cache: True
     cache_params:
       type: redis
       host: localhost
       port: 6379
       ttl: 600
   ```

3. **Использовать автоматическое кэширование OpenRouter**
   - При использовании OpenRouter кэширование автоматическое для большинства моделей
   - Добавить `usage: {include: true}` для отслеживания экономии

#### Tier 2: Среднесрочная оптимизация

4. **Внедрить Redis Semantic Caching**
   ```yaml
   litellm_settings:
     cache: True
     cache_params:
       type: redis-semantic
       similarity_threshold: 0.85
       ttl: 300
       redis_semantic_cache_embedding_model: "text-embedding-3-small"
   ```

#### Tier 3: Продвинутая оптимизация

5. **Интеграция GPTCache**
   - Для высоконагруженных деплоев где семантическое сходство может устранить избыточные API вызовы
   - Начать с Faiss + SQLite, масштабировать до Milvus + PostgreSQL

6. **Гибридная стратегия кэширования**
   ```
   Поток запроса:
   1. Проверить in-memory кэш (sub-1ms)
   2. Проверить Redis semantic cache (similarity match)
   3. Проверить Redis exact cache
   4. Сделать API вызов с prompt caching
   5. Сохранить ответ во все слои кэша
   ```

### 1.7 Ожидаемый эффект

| Стратегия | Снижение стоимости | Улучшение Latency |
|-----------|-------------------|-------------------|
| Provider Prompt Caching | 50-90% | 50-85% |
| Redis Response Caching | 30-60% | 90%+ на hits |
| Semantic Caching | 20-40% дополнительно | Variable |
| **Комбинированный подход** | **70-95%** | **80-95%** |

### 1.8 Источники по LLM кэшированию

- [LiteLLM Caching Documentation](https://docs.litellm.ai/docs/caching/all_caches)
- [LiteLLM Proxy Caching](https://docs.litellm.ai/docs/proxy/caching)
- [LiteLLM Prompt Caching](https://docs.litellm.ai/docs/completion/prompt_caching)
- [LiteLLM Production Best Practices](https://docs.litellm.ai/docs/proxy/prod)
- [LiteLLM v1.75.5 Redis Improvements](https://docs.litellm.ai/release_notes/v1-75-5)
- [GPTCache GitHub](https://github.com/zilliztech/GPTCache)
- [GPTCache Deep Dive (Medium)](https://medium.com/@raju.samantapudi/rethinking-llm-performance-a-deep-dive-into-gptcache-and-the-future-of-semantic-caching-6f338f1f2fd2)
- [OpenRouter Prompt Caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching)
- [OpenRouter Tool Caching Announcement](https://openrouter.ai/announcements/gif-prompts-omni-search-tool-caching-and-byok-flags)
- [Anthropic Prompt Caching](https://www.anthropic.com/news/prompt-caching)
- [Claude Prompt Caching Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching Guide 2025](https://promptbuilder.cc/blog/prompt-caching-token-economics-2025)
- [Redis LLM Gateway Scale Guide](https://redis.io/blog/scale-your-llm-gateway/)
- [Prompt Caching Infrastructure Guide](https://introl.com/blog/prompt-caching-infrastructure-llm-cost-latency-reduction-guide-2025)

---

## 2. Python 3.13 + UV Package Manager

### 2.1 Python 3.13 — Ключевые улучшения

#### JIT Compilation (PEP 744)

Python 3.13 вводит экспериментальный Just-In-Time компилятор:

- **Текущая производительность**: 5-15% быстрее чем Python 3.12, до 30% для compute-heavy задач
- **Лучший use case**: Большие датасеты и real-time обработка данных — идеально для LLM взаимодействий
- **Включение JIT**: Переменная окружения `PYTHON_JIT=1`
- **Требования к сборке**: `--enable-experimental-jit` flag

**Рекомендация**: Включить JIT для production деплоев с консистентными LLM inference нагрузками.

#### Free-Threading / No-GIL Mode (PEP 703)

Самое значительное архитектурное изменение для мульти-агентных систем:

| Характеристика | Стандартный Python | Free-Threaded Python 3.13 |
|----------------|-------------------|---------------------------|
| Настоящие параллельные потоки | Нет (GIL ограничивает) | Да |
| Использование multi-core | Ограничено | Полное |
| Single-thread overhead | Baseline | ~40% (падает до 5-10% в 3.14) |
| Multi-thread выигрыш | Псевдо-параллельность | 2-4x на 4+ ядрах |

**Преимущества для Agent Zero**:
- 4-агентная система на 4-core машине может достичь **2-4x прироста производительности**
- Суб-агенты могут работать действительно параллельно
- Real-time выполнение инструментов при сохранении коммуникации агентов
- Лучшая утилизация иерархической системы коммуникации агентов

**Включение Free-Threading**:
```bash
# Использовать free-threaded сборку Python
python3.13t  # 't' суффикс означает free-threaded сборку

# Или отключить GIL в runtime
PYTHON_GIL=0 python your_script.py
```

#### Улучшения памяти

- **7% меньший memory footprint** по сравнению с Python 3.12
- Модифицированный mimalloc allocator включён по умолчанию
- Stripped leading indentation из docstrings, уменьшение размера `.pyc` файлов

### 2.2 UV Package Manager

#### Сравнение производительности

| Операция | pip | UV | Ускорение |
|----------|-----|----|-----------|
| Cold install (JupyterLab) | 21.4 секунды | 2.6 секунды | ~8x |
| Общие операции с пакетами | Baseline | 10-100x быстрее | 10-100x |
| Разрешение зависимостей | Последовательное | Параллельное | Значительное |

#### Ключевые преимущества для Agent Zero

1. **Unified Tooling**: UV заменяет pip, virtualenv, pip-tools, pipx, pyenv в одном бинарнике
2. **Global Cache**: Пакеты скачиваются один раз, линкуются во все проекты — экономит гигабайты при множестве AI проектов
3. **Clean Dependency Management**: `uv remove` удаляет транзитивные зависимости, держит окружения чистыми
4. **Automatic Environment Sync**: `uv run` гарантирует консистентное, locked окружение
5. **Cross-Platform Lockfile**: `uv.lock` обеспечивает воспроизводимые сборки

#### UV vs pip — Прямое сравнение

| Аспект | pip | UV |
|--------|-----|-----|
| Скорость | Медленно (последовательно) | 10-100x быстрее (параллельно) |
| Управление окружением | Нужен отдельный инструмент | Встроено |
| Дисковое пространство | Дубликаты в каждом проекте | Глобальный кэш с линками |
| Lockfile | Требует pip-tools | Нативный `uv.lock` |
| Управление версиями Python | Требует pyenv | Встроено |

### 2.3 Руководство по миграции Agent Zero на UV

#### Шаг 1: Установка UV

```bash
# Через curl (рекомендуется)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Или через pip (bootstrap)
pip install uv
```

#### Шаг 2: Миграция с requirements.txt

```bash
# Перейти в директорию Agent Zero
cd /path/to/agent-zero

# Инициализировать UV проект (создаёт pyproject.toml)
uv init

# Импортировать существующие requirements
uv add -r requirements.txt

# Установить версию Python
echo "3.13" > .python-version
```

#### Шаг 3: Структура проекта после миграции

```
agent-zero/
├── .python-version      # Python 3.13 или 3.13t (free-threaded)
├── .venv/               # Управляемое виртуальное окружение
├── pyproject.toml       # Зависимости проекта
├── uv.lock              # Кросс-платформенный lockfile
└── python/
    └── tools/           # Инструменты Agent Zero
```

#### Шаг 4: Основные команды UV

```bash
# Создать/синхронизировать окружение
uv sync

# Добавить зависимость
uv add langchain openai

# Добавить dev зависимость
uv add --dev pytest ruff

# Запустить Agent Zero
uv run python main.py

# Обновить все зависимости
uv lock --upgrade
```

#### Шаг 5: Миграция CI/CD

Заменить pip команды в CI/CD пайплайнах:

```yaml
# До (pip)
- run: pip install -r requirements.txt

# После (UV)
- run: curl -LsSf https://astral.sh/uv/install.sh | sh
- run: uv sync
```

### 2.4 Best Practices для Python 3.13 в AI/LLM приложениях

#### Thread Safety для мульти-агентных систем

```python
import threading
from concurrent.futures import ThreadPoolExecutor

# Использовать explicit locks для shared state
agent_state_lock = threading.Lock()

def run_sub_agent(agent_id, task):
    # Thread-safe выполнение агента
    with agent_state_lock:
        result = agent.execute(task)
    return result

# Использовать free-threading для параллельных агентов
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(run_sub_agent, i, task) for i, task in enumerate(tasks)]
    results = [f.result() for f in futures]
```

#### Рекомендуемая конфигурация окружения

```bash
# .env файл для Agent Zero с оптимизациями Python 3.13
PYTHON_JIT=1                    # Включить JIT компиляцию
PYTHON_GIL=0                    # Отключить GIL (только free-threaded сборка)
UV_SYSTEM_PYTHON=false          # Использовать UV-managed Python
```

#### Шаблон pyproject.toml для Agent Zero

```toml
[project]
name = "agent-zero"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "langchain>=0.1.0",
    "openai>=1.0.0",
    "anthropic>=0.18.0",
    # ... другие зависимости
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.1.0",
]

[tool.uv]
python = "3.13"
```

### 2.5 Сводная таблица оптимизаций

| Оптимизация | Ожидаемый эффект | Усилия | Риск |
|-------------|------------------|--------|------|
| Миграция на UV | 10-100x быстрее package ops | Низкие | Низкий |
| Обновление до Python 3.13 | 5-15% скорость, 7% память | Средние | Средний |
| Включение JIT | До 30% для compute-heavy | Низкие | Низкий |
| Free-threading | 2-4x для multi-agent | Высокие | Высокий |

### 2.6 Источники по Python 3.13 и UV

#### Python 3.13 Performance
- [What's New In Python 3.13 - Official Documentation](https://docs.python.org/3/whatsnew/3.13.html)
- [Python 3.13: Free Threading and a JIT Compiler - Real Python](https://realpython.com/python313-free-threading-jit/)
- [State of Python 3.13 Performance: Free-Threading - CodSpeed](https://codspeed.io/blog/state-of-python-3-13-performance-free-threading)
- [Python 3.13: Blazing New Trails in Performance and Scale - The New Stack](https://thenewstack.io/python-3-13-blazing-new-trails-in-performance-and-scale/)
- [Why Python 3.13 Is a Game-Changer for AI Development - Aitude](https://www.aitude.com/python-3-13-the-new-era-of-ai-development-and-what-it-means-for-modern-businesses/)
- [Python 3.13 in 2025 Breakthroughs: No-GIL, JIT, and iOS Support Explained](https://www.ahmedbouchefra.com/news/python-313-2025-breakthroughs-no-gil-jit-ios-support-explained/)

#### UV Package Manager
- [Python UV: The Ultimate Guide - DataCamp](https://www.datacamp.com/tutorial/python-uv)
- [uv vs pip: Managing Python Packages - Real Python](https://realpython.com/uv-vs-pip/)
- [From pip to uv: A Modern Revolution - Medium](https://medium.com/womenintechnology/from-pip-to-uv-a-modern-revolution-in-python-package-management-62dd8ac91df2)
- [Switching from Pip to uv - AppSignal Blog](https://blog.appsignal.com/2025/09/24/switching-from-pip-to-uv-in-python-a-comprehensive-guide.html)
- [Official UV Documentation](https://docs.astral.sh/uv/)
- [From pip to a uv project - Official Migration Guide](https://docs.astral.sh/uv/guides/migration/pip-to-project/)

#### Multi-Agent AI Performance
- [Python 3.13 without the GIL: A Game-Changer for Concurrency - Medium](https://medium.com/@r_bilan/python-3-13-without-the-gil-a-game-changer-for-concurrency-5e035500f0da)
- [Unlocking True Concurrency in Python 3.13 - DEV Community](https://dev.to/avik12345678/unlocking-true-concurrency-in-python-313-mastering-free-threaded-mode-for-high-performance-4kca)
- [Free-Threaded Python (3.14+ Production Ready) - AI Native](https://ai-native.panaversity.org/docs/Python-Fundamentals/cpython-gil/free-threaded-python)
- [Python support for free threading - Official Documentation](https://docs.python.org/3/howto/free-threading-python.html)

---

## 3. Bun вместо NodeJS

### 3.1 Executive Summary

**Bun — сильный кандидат для замены NodeJS** в frontend/tools Agent Zero. Bun значительно развился:
- **Anthropic приобрела Bun в ноябре 2025**
- Версия 1.3 объявлена "production-ready" с 90%+ Node.js совместимостью
- Существенные преимущества производительности (3-4x HTTP throughput, 5x startup, 20x package installs)

### 3.2 Бенчмарки производительности (2025-2026)

#### HTTP Server Performance

| Runtime | Requests/Second | Примечания |
|---------|-----------------|------------|
| **Bun** | 52,000 - 180,000 | Express-style тесты |
| Node.js | 13,000 - 65,000 | Те же условия тестов |
| Deno | ~75,000 | Middle ground |

#### Время старта

- **Bun 1.3**: ~8ms cold start
- **Node.js 24**: ~42ms cold start
- **Результат**: 5-8x быстрее

#### Установка пакетов

- **bun install**: 2-3 секунды для средних проектов
- **npm install**: 20-60 секунд для тех же проектов
- **Улучшение**: 10-20x быстрее

#### CPU-Bound задачи

- **Bun**: 1,700ms (сортировка 100,000 чисел)
- **Node.js**: 3,400ms
- **Улучшение**: 2x быстрее

#### Выполнение тестов

- `bun test` работает 5-10x быстрее чем Jest на Node.js

### 3.3 Совместимость Bun с существующими NodeJS проектами

#### Текущий статус (Bun 1.2+)

- **90%+ Node.js API совместимость** начиная с Bun 1.2
- Спроектирован как **drop-in replacement** для Node.js
- Запускает тысячи тестов Node.js test suite перед каждым релизом
- Работает с популярными фреймворками: **Next.js, Express, Fastify, Hono**

#### Поддерживаемые возможности

- CommonJS и ES Modules (можно использовать `require()` и `import` в одном файле)
- TypeScript (нативно, без транспиляции)
- JSX/TSX
- Автоматическая конвертация `package-lock.json` в `bun.lock`

#### Известные ограничения

- **node:cluster** - Не реализован
- **node:inspector** - Не реализован
- **node:child_process** - Отсутствуют некоторые функции
- **node:crypto** - Отсутствуют некоторые функции
- **Native modules** (bcrypt, sharp, sqlite3) могут не работать - используйте pure JS альтернативы

### 3.4 Руководство по миграции с NodeJS на Bun

#### Шаг 1: Замена Package Manager

```bash
# Вместо:
npm install

# Используйте:
bun install
```

Bun автоматически конвертирует `package-lock.json` в `bun.lock`.

#### Шаг 2: Обновление TypeScript конфигурации

```bash
bun remove @types/node ts-node
bun add bun-types
```

#### Шаг 3: Обновление scripts в package.json

```json
{
  "scripts": {
    "start": "bun run index.ts",
    "test": "bun test",
    "build": "bun build ./src/index.ts --outdir ./dist"
  }
}
```

#### Шаг 4: Замена Native модулей

| Node Module | Bun Альтернатива |
|-------------|------------------|
| bcrypt | bcryptjs (pure JS) |
| sharp | @bun/image |
| sqlite3 | bun:sqlite (built-in) |

### 3.5 Возможности Bun для веб-приложений и инструментов

#### All-in-One Toolkit

Bun объединяет множество инструментов в один бинарник:

| Традиционный стек | Эквивалент Bun |
|-------------------|----------------|
| Node.js runtime | bun (runtime) |
| npm/yarn/pnpm | bun install |
| Webpack/Rollup | bun build |
| Jest/Vitest | bun test |
| ts-node/tsx | Native TypeScript |
| Babel | Не нужен |

#### Возможности Bun 1.3 (Октябрь 2025)

- **Full-stack dev server** в `Bun.serve()`
- **Hot reloading** для frontend разработки
- **Integrated routing** с параметризованными маршрутами
- **Встроенный Redis client**
- **Package security scanner**: `bun pm check` (интеграция Socket.dev)
- **Migration tooling**: `bun pm migrate` для yarn/pnpm lockfiles

#### Встроенная поддержка баз данных

- **PostgreSQL client** (Bun 1.2+)
- **S3 object support** (Bun 1.2+)
- **SQLite** (`bun:sqlite`)
- **Redis client** (Bun 1.3+)

### 3.6 Рекомендации для Agent Zero

#### Архитектура Agent Zero

Agent Zero состоит из:
- **Main Framework**: Python-based AI agent system
- **Web UI**: Frontend interface (`run_ui.py`)
- **a0-launcher**: JavaScript-based launcher application
- **Docker Container**: Primary deployment method

#### Рекомендация: Постепенная миграция

##### Phase 1: Миграция Package Manager (Низкий риск)

```bash
# Заменить npm на bun для a0-launcher
cd a0-launcher
bun install  # Drop-in замена для npm install
```

**Преимущества**:
- 10-20x быстрее установка
- Не требуются изменения кода
- Автоматическая конвертация lockfile

##### Phase 2: Development Tooling (Средний риск)

- Заменить Jest на `bun test`
- Заменить webpack/vite на `bun build`
- Использовать нативное выполнение TypeScript

**Преимущества**:
- 5-10x быстрее запуск тестов
- Упрощённый toolchain
- Нативная поддержка TypeScript

##### Phase 3: Миграция Runtime (Высокий риск)

- Заменить Node.js runtime на Bun
- Тщательно протестировать всю функциональность
- Мониторить проблемы совместимости

**Преимущества**:
- 3-4x улучшение HTTP throughput
- 5x быстрее cold starts (отлично для Docker контейнеров)
- Меньшее потребление памяти

### 3.7 Оценка рисков

| Риск | Митигация |
|------|-----------|
| Несовместимость native модулей | Использовать pure JS альтернативы (bcryptjs, etc.) |
| Отсутствующие Node.js APIs | Проверить Bun compatibility docs перед миграцией |
| Ограниченный enterprise track record | Покупка Anthropic обеспечивает backing; сохранить Node.js как fallback |
| Learning curve | Минимальный - спроектирован как drop-in replacement |

### 3.8 Приобретение Bun компанией Anthropic

**2 декабря 2025 года Anthropic приобрела Bun.** Это высоко релевантно для Agent Zero:

- Bun теперь питает **Claude Code** и **Claude Agent SDK**
- Приобретение валидирует production-readiness Bun
- Обеспечивает долгосрочную поддержку и развитие
- Claude Code достиг $1 billion run-rate revenue используя Bun

### 3.9 Сводная матрица решений

| Критерий | Bun | Node.js | Рекомендация |
|----------|-----|---------|--------------|
| HTTP Performance | Отлично (3-4x быстрее) | Хорошо | **Bun** |
| Время старта | Отлично (5x быстрее) | Приемлемо | **Bun** |
| Установка пакетов | Отлично (20x быстрее) | Медленно | **Bun** |
| Зрелость экосистемы | Хорошо (90%+ compat) | Отлично | Node.js |
| Enterprise adoption | Растёт | Устоялась | Node.js |
| Долгосрочная поддержка | Anthropic-backed | Node.js Foundation | Ничья |
| Unified Tooling | Встроено | Требует настройки | **Bun** |

### 3.10 Источники по Bun

- [Strapi - Bun vs Node.js 2025 Performance Guide](https://strapi.io/blog/bun-vs-nodejs-performance-comparison-guide)
- [Better Stack - Node.js vs Deno vs Bun](https://betterstack.com/community/guides/scaling-nodejs/nodejs-vs-deno-vs-bun/)
- [DEV Community - Deno 2 vs Node.js vs Bun in 2026](https://dev.to/pockit_tools/deno-2-vs-nodejs-vs-bun-in-2026-the-complete-javascript-runtime-comparison-1elm)
- [Bun Official Documentation - Node.js Compatibility](https://bun.com/docs/runtime/nodejs-compat)
- [Socket.dev - Bun 1.2 Released](https://socket.dev/blog/bun-1-2-released-90-node-js-compatibility-built-in-s3-object-support)
- [heise online - Bun 1.3 Full-Stack Runtime](https://www.heise.de/en/news/Web-Development-Bun-1-3-Becomes-Full-Stack-JavaScript-Runtime-10759717.html)
- [InfoQ - Bun 1.2 Node Compat](https://www.infoq.com/news/2025/04/bun-12-node-compat-postgres/)
- [GitHub - oven-sh/bun](https://github.com/oven-sh/bun)
- [byteiota - Migrating from Node.js to Bun](https://byteiota.com/migrating-from-node-js-to-bun-1-1-production-guide/)
- [OpenReplay - How to: Migrating from Node to Bun](https://blog.openreplay.com/how-to--migrating-from-node-to-bun/)
- [LogRocket - Bun 1.3](https://blog.logrocket.com/bun-javascript-runtime-taking-node-js-deno/)
- [Medium - Why Choose Bun Over Node.js in Late 2026](https://lalatenduswain.medium.com/why-choose-bun-over-node-js-deno-and-other-javascript-runtimes-in-late-2026-121f25f208eb)

---

## 4. SearXNG Оптимизация

### 4.1 Обзор

SearXNG — privacy-respecting метапоисковик, интегрированный в Docker контейнер Agent Zero. Это исследование покрывает performance tuning, конфигурацию движков, Redis/Valkey кэширование и rate limiting оптимизации специально для AI agent workloads.

### 4.2 Performance Tuning

#### Рекомендации по железу

- **CPU**: 4 ядра рекомендуется для оптимальной производительности
- **RAM**: 4 GB выделено (каждый uWSGI worker использует ~256MB)
- **Storage**: ~20 GB для локального деплоя

#### uWSGI Конфигурация (Критично для производительности)

Настройки uWSGI по умолчанию **не подходят для production**. Настройте `/etc/uwsgi/apps-available/searxng.ini`:

```ini
[uwsgi]
master = true
vacuum = true
need-app = true
lazy-apps = true
die-on-term = true

# Workers & Threads
workers = %k                    # Авто-определение количества CPU (или задать вручную)
threads = 4                     # 4 потока на worker
enable-threads = true           # Требуется для Python threading

# Оптимизации производительности
thunder-lock = true             # Уменьшает thundering herd problem
offload-threads = 4             # Для обработки статических файлов (макс 4)
max-worker-lifetime = 3600      # Перезапуск workers каждый час (предотвращение memory leaks)
```

**Environment Variables для Docker**:
```bash
UWSGI_WORKERS=4
UWSGI_THREADS=4
```

#### Конфигурация Connection Pool

В `settings.yml` под `outgoing:`:

```yaml
outgoing:
  request_timeout: 2.0           # Дефолтный per-engine timeout
  max_request_timeout: 10.0      # Максимальный разрешённый timeout
  pool_connections: 100          # Макс concurrent connections
  pool_maxsize: 20               # Keep-alive connections (увеличить с дефолтных 10)
  keepalive_expiry: 5.0          # Секунды для keep connections alive
  enable_http2: true             # Включить HTTP/2 для лучшей производительности
```

### 4.3 Лучшие поисковые движки для AI агентов

#### Рекомендуемый выбор движков

Для Agent Zero и AI workloads включите движки, дающие **разнообразные, качественные результаты** с хорошей надёжностью:

##### Высокий приоритет (Включить эти)

| Движок | Категория | Примечания |
|--------|-----------|------------|
| `google` | general | Лучшие общие результаты |
| `duckduckgo` | general | Privacy-focused, надёжный |
| `bing` | general | Сильная альтернатива Google |
| `brave` | general | Хороший баланс privacy + качество |
| `wikipedia` | general | Высокий throughput, нет rate limits |
| `stackoverflow` | it | Необходим для code queries |
| `github` | it | Code repositories |
| `arxiv` | science | Научные статьи |
| `semantic_scholar` | science | Исследовательские статьи |
| `reddit` | social media | Дискуссии сообщества |

##### Отключить для производительности

- Движки, которые постоянно медленные (проверить страницу `/stats`)
- Движки, которые часто timeout или возвращают ошибки
- Дублирующие движки категорий, которые не нужны

#### Минимальная конфигурация

Для работы **только с essential движками** (максимальная производительность):

```yaml
use_default_settings:
  engines:
    keep_only:
      - google
      - duckduckgo
      - bing
      - brave
      - wikipedia
      - stackoverflow
      - github
      - arxiv
```

#### Engine-Specific Timeout Tuning

```yaml
engines:
  - name: google
    timeout: 3.0
    disabled: false

  - name: wikipedia
    timeout: 2.0
    max_connections: 50      # Wikipedia выдерживает высокую нагрузку

  - name: stackoverflow
    timeout: 4.0
    disabled: false
```

### 4.4 Redis/Valkey Caching Configuration

#### Почему Redis/Valkey важен для Agent Zero

- **Rate Limiter**: Требуется для limiter plugin (заменяет filtron)
- **Token Storage**: Некоторые движки хранят authentication tokens
- **Future Caching**: Планируется для дополнительного performance caching

> **Примечание**: SearXNG мигрирует с Redis на **Valkey**. Новые установки должны использовать Valkey.

#### Конфигурация в `settings.yml`

```yaml
valkey:
  url: valkey://localhost:6379/0

# Или для Redis (legacy):
redis:
  url: redis://localhost:6379/0

# Альтернатива: Unix socket (быстрее для локального)
valkey:
  url: unix:///var/run/valkey/valkey.sock?db=0
```

#### Docker Compose Setup

```yaml
services:
  searxng:
    image: searxng/searxng:latest
    depends_on:
      - valkey
    environment:
      - SEARXNG_REDIS_URL=valkey://valkey:6379/0

  valkey:
    image: valkey/valkey:latest
    command: valkey-server --save 30 1 --loglevel warning
    volumes:
      - valkey-data:/data

volumes:
  valkey-data:
```

#### Команда Backup

```bash
docker exec searxng-valkey valkey-cli BGSAVE
```

### 4.5 Rate Limiting и Load Balancing

#### Limiter Configuration

Включить в `settings.yml`:

```yaml
server:
  limiter: true
  method: "POST"
  secret_key: "your-secret-key-here"
```

#### Limiter TOML Configuration

Создать `/etc/searxng/limiter.toml`:

```toml
[botdetection.ip_limit]
link_token = true

[botdetection.ip_limit.filter_link_local]
skip_ips = ["127.0.0.1", "::1"]

# IP prefix для rate limiting
ipv4_prefix = 32
ipv6_prefix = 48
```

#### Для специфичной настройки Agent Zero

Поскольку Agent Zero запускает SearXNG локально в том же контейнере, вы можете захотеть **отключить или ослабить rate limiting** для внутренних запросов:

```toml
[botdetection.ip_limit]
link_token = false

# Whitelist локальных container IPs
[botdetection.ip_limit.filter_link_local]
skip_ips = ["127.0.0.1", "172.17.0.0/16", "::1"]
```

#### Load Balancing с Reverse Proxy

Если деплоите несколько SearXNG instances:

```yaml
server:
  # Требуется для корректного определения IP за reverse proxy
  trusted_proxies:
    - "172.17.0.0/16"
    - "10.0.0.0/8"
```

Настроить proper headers в вашем reverse proxy:
- `X-Forwarded-For`
- `X-Real-IP`
- `X-Forwarded-Proto`

#### Engine-Level Rate Limiting

Для движков со строгими rate limits:

```yaml
engines:
  - name: google
    rate_limit: 10       # Макс запросов в секунду к этому движку

  - name: bing
    rate_limit: 20
```

### 4.6 Рекомендации специфичные для Agent Zero

#### Оптимизированный `settings.yml` для Agent Zero

```yaml
use_default_settings: true

general:
  instance_name: "Agent Zero Search"
  enable_metrics: true

server:
  port: 8888
  bind_address: "0.0.0.0"
  secret_key: "change-this-to-a-random-string"
  limiter: false              # Отключить для внутреннего использования AI агентом
  method: "POST"
  image_proxy: false          # Отключить если не нужно

search:
  safe_search: 0              # Отключить safe search для полноценных результатов
  default_lang: "en"
  autocomplete: ""            # Отключить для API использования
  formats:
    - json                    # Обеспечить JSON output для API
    - html

outgoing:
  request_timeout: 3.0
  max_request_timeout: 15.0
  pool_connections: 100
  pool_maxsize: 25
  enable_http2: true

valkey:
  url: valkey://valkey:6379/0

# Оптимизированный выбор движков для AI агентов
use_default_settings:
  engines:
    keep_only:
      - google
      - duckduckgo
      - bing
      - brave
      - wikipedia
      - stackoverflow
      - github
      - arxiv
      - semantic_scholar
      - reddit
```

#### API Usage для Agent Zero

SearXNG JSON API endpoint:
```
http://localhost:8888/search?q=your+query&format=json&categories=general
```

Параметры для AI агентов:
- `format=json` - Machine-readable output
- `categories=general,science,it` - Таргетировать специфичные категории
- `engines=google,duckduckgo` - Специфичные движки
- `language=en` - Языковой фильтр
- `time_range=year` - Time-based filtering

#### Performance Monitoring

Доступ к странице статистики на `/stats` для определения медленных движков и соответствующей корректировки конфигурации.

### 4.7 Сводка ключевых оптимизаций

| Область | Рекомендация |
|---------|--------------|
| **Движки** | Оставить только 10-15 надёжных движков, отключить медленные |
| **Workers** | Установить равным количеству CPU, 4 потока каждый |
| **Connections** | pool_connections=100, pool_maxsize=25 |
| **Timeout** | 2-3s default, 10-15s max |
| **Caching** | Использовать Valkey с Unix socket для минимальной latency |
| **Rate Limiting** | Отключить limiter для внутреннего использования Agent Zero |
| **HTTP** | Включить HTTP/2 |

### 4.8 Источники по SearXNG

- [SearXNG Official Documentation](https://docs.searxng.org/)
- [SearXNG Performance Discussion #1738](https://github.com/searxng/searxng/discussions/1738)
- [SearXNG Redis Settings](https://docs.searxng.org/admin/settings/settings_redis.html)
- [SearXNG Limiter Documentation](https://docs.searxng.org/admin/searx.limiter.html)
- [SearXNG Engines Configuration](https://docs.searxng.org/admin/settings/settings_engines.html)
- [SearXNG Outgoing Settings](https://docs.searxng.org/admin/settings/settings_outgoing.html)
- [SearXNG uWSGI Configuration](https://docs.searxng.org/admin/installation-uwsgi.html)
- [Agent Zero Architecture](https://www.agent-zero.ai/p/architecture/)
- [Agent Zero GitHub](https://github.com/agent0ai/agent-zero)
- [Run SearXNG Locally for AI Agents - Medium](https://medium.com/@gabrielrodewald/run-searxng-locally-to-keep-your-ai-data-private-free-create-custom-agentic-tools-e8f4b5592082)
- [SearXNG MCP Server for AI Assistants](https://mcp.aibase.com/server/1916343959745699842)
- [LiteLLM SearXNG Integration](https://docs.litellm.ai/docs/search/searxng)

---

## 5. Контейнер Оптимизация

### 5.1 Executive Summary

На основе актуальных 2025-2026 best practices и специфичной архитектуры Agent Zero, здесь представлены ключевые стратегии оптимизации для container deployment.

### 5.2 Multi-Stage Docker Builds Optimization

#### Ключевые преимущества для Agent Zero

- **Уменьшение размера образа**: Может сократить images с ~523MB до ~273MB (примерно 50% reduction)
- **Улучшение скорости сборки**: Multi-stage builds могут завершиться за 1.2 секунды vs 1+ минуты для single-stage
- **Улучшение безопасности**: Уменьшает attack surface исключая build tools из финального образа

#### Рекомендуемая структура Dockerfile для Agent Zero

```dockerfile
# Stage 1: Сборка зависимостей
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
COPY requirements.txt .

# Сборка wheels для более быстрых последующих установок
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /a0
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY . .

# Agent Zero specific оптимизации
EXPOSE 80
CMD ["/exe/initialize.sh"]
```

#### 2026 Улучшения

- **BuildKit**: Включить с `DOCKER_BUILDKIT=1` для более быстрых сборок и лучшего кэширования
- **DockerSlim 2026**: Может автоматически минимизировать images до 70% без потери функциональности
- Использовать **Python wheels** чтобы избежать перекомпиляции тяжёлых библиотек (pandas, numpy) при каждой сборке

### 5.3 Alpine vs Debian Slim для Python Containers

#### Рекомендация: Использовать Debian Slim (python:3.12-slim-bookworm)

| Аспект | Alpine | Debian Slim |
|--------|--------|-------------|
| **Base size** | ~5 MB | ~22 MB |
| **Python image size** | 52 MB (uncompressed) | 149 MB (uncompressed) |
| **C library** | musl | glibc |
| **Performance** | 15-35% медленнее для некоторых workloads | Стандартная производительность |
| **Compatibility** | Могут быть проблемы с compiled deps | Отличная совместимость |

#### Почему Debian Slim лучше для Agent Zero

1. **Performance**: Alpine's musl library может вызвать 15-35% деградацию производительности в Python apps
2. **Compatibility**: Agent Zero использует множество Python зависимостей которые могут иметь glibc-specific оптимизации
3. **Build reliability**: Нет проблем с compiled extensions (numpy, pandas, etc.)
4. **Latest Python bugfixes**: Официальные Docker Python images на базе Debian получают updates первыми

#### Когда Alpine может работать

- Простые скрипты с pure Python зависимостями
- Когда размер образа абсолютный приоритет над производительностью
- Static file serving или простые API endpoints

### 5.4 Podman Rootless Performance Tuning

#### 2025-2026 Бенчмарки производительности

- **Скорость старта**: Podman Rootless в 4x быстрее чем Docker (fork-exec vs IPC queues)
- **Использование памяти**: На 75% меньше (нет daemon RSS overhead)
- **Scaling**: 10k containers/user на 16GB RAM vs Docker's 500

#### Критичные оптимизации для Agent Zero

##### Storage Driver Configuration

```bash
# В ~/.config/containers/storage.conf
[storage]
driver = "overlay"
runroot = "/run/user/1000/containers"
graphroot = "/home/user/.local/share/containers/storage"

[storage.options.overlay]
mount_program = "/usr/bin/fuse-overlayfs"
```

**Performance tip**: Использовать XFS или BTRFS filesystem для reflink support с lazy pulling.

##### Networking Optimization

- **Использовать pasta вместо slirp4netns**: 2x быстрее, снижает latency с 4ms до 1.2ms
- **Socket activation**: Обходит network penalty для listening sockets

```bash
# Включить pasta networking
podman run --network=pasta:t agent-zero
```

##### OCI Runtime Selection

```bash
# Использовать crun для максимальной производительности
podman run --runtime=/usr/bin/crun agent-zero
```

##### cgroups v2 Configuration (Обязательно)

```bash
# Проверить cgroups v2
cat /sys/fs/cgroup/cgroup.controllers

# Включить CPU/memory delegation
mkdir -p /etc/systemd/system/user@.service.d/
cat > /etc/systemd/system/user@.service.d/delegate.conf << EOF
[Service]
Delegate=cpu cpuset io memory pids
EOF
systemctl daemon-reload
```

#### Podman Command для Agent Zero

```bash
podman run -d \
  --name agent-zero \
  --runtime=/usr/bin/crun \
  --network=pasta:t \
  --log-driver=none \
  -p 50080:80 \
  -v /path/to/data:/a0/usr:Z \
  --cpus=2 \
  --memory=4g \
  agent0ai/agent-zero
```

### 5.5 Container Resource Limits Best Practices

#### Рекомендуемые лимиты для Agent Zero

```yaml
# docker-compose.yml
services:
  agent-zero:
    image: agent0ai/agent-zero
    deploy:
      resources:
        limits:
          cpus: '2.0'          # Hard limit: 2 CPU cores
          memory: 4G           # Hard limit: 4GB RAM
        reservations:
          cpus: '0.5'          # Minimum guaranteed
          memory: 512M         # Minimum guaranteed
    ports:
      - "50080:80"
    volumes:
      - ./data:/a0/usr
```

#### Memory Configuration

```bash
# Hard memory limit без swap
docker run -d \
  --memory=4g \
  --memory-swap=4g \
  --name agent-zero \
  agent0ai/agent-zero
```

**Key settings:**
- `--memory=4g`: Hard limit 4GB
- `--memory-swap=4g`: То же что memory = нет использования swap
- `--memory-reservation=512m`: Soft limit для scheduling

#### CPU Configuration

```bash
# Лимит на 2 CPU с гарантированным минимумом
docker run -d \
  --cpus=2 \
  --cpu-shares=2048 \
  --name agent-zero \
  agent0ai/agent-zero
```

**Key settings:**
- `--cpus=2`: Лимит на 2 CPU cores
- `--cpu-shares=2048`: Приоритет (default 1024, выше = больше приоритет)
- `--cpuset-cpus=0,1`: Pin к конкретным cores (для latency-sensitive workloads)

#### Monitoring Commands

```bash
# Real-time stats
docker stats agent-zero

# One-time check
docker stats --no-stream agent-zero

# Обновить лимиты без рестарта
docker update --memory=8g --cpus=4 agent-zero
```

#### Production Recommendations

| Workload | Memory | CPU | Notes |
|----------|--------|-----|-------|
| Light (single user) | 2-4GB | 1-2 cores | Basic Q&A tasks |
| Medium (multiple users) | 4-8GB | 2-4 cores | Concurrent sessions |
| Heavy (local LLM) | 16GB+ | 4+ cores | Ollama integration |

### 5.6 Agent Zero Specific Recommendations

#### Оптимизированный Dockerfile для Agent Zero

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.12-slim-bookworm AS runtime

# Security: Создать non-root user
RUN useradd -m -u 1000 agent && \
    mkdir -p /a0/usr && \
    chown -R agent:agent /a0

WORKDIR /a0
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY --chown=agent:agent . .

USER agent
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["/exe/initialize.sh"]
```

#### Docker Compose Production Template

```yaml
version: '3.8'

services:
  agent-zero:
    image: agent0ai/agent-zero:latest
    container_name: agent-zero
    restart: unless-stopped
    ports:
      - "50080:80"
    volumes:
      - agent-data:/a0/usr
    environment:
      - TZ=UTC
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  agent-data:
    driver: local
```

#### Key Optimization Checklist

1. **Использовать `python:3.12-slim-bookworm`** - Лучший баланс размер/производительность
2. **Включить BuildKit** - `export DOCKER_BUILDKIT=1`
3. **Multi-stage builds** - Исключить build tools из runtime
4. **Установить resource limits** - Предотвратить runaway containers
5. **Volume mapping только на `/a0/usr`** - Избежать version conflicts
6. **Log rotation** - Предотвратить исчерпание диска
7. **Health checks** - Включить automatic recovery
8. **Non-root user** - Security best practice

### 5.7 Сводная таблица оптимизаций

| Область оптимизации | Рекомендация | Эффект |
|---------------------|--------------|--------|
| Base Image | `python:3.12-slim-bookworm` | Лучше совместимость, ~10% быстрее |
| Multi-stage Build | Да, с wheel caching | 50% меньше images |
| Resource Limits | 4GB RAM, 2 CPUs default | Предотвращает crashes хоста |
| Podman Networking | pasta mode | 2x быстрее чем slirp4netns |
| Storage Driver | overlay с fuse-overlayfs | Лучшая rootless производительность |
| Runtime | crun | Самый быстрый OCI runtime |
| Logging | json-file с rotation | Предотвращает исчерпание диска |

### 5.8 Источники по контейнерной оптимизации

- [Docker Multi-Stage Builds Docs](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/)
- [Multi-stage builds #2: Python specifics](https://pythonspeed.com/articles/multi-stage-docker-python/)
- [Docker Multi-Stage Builds for Python Developers](https://collabnix.com/docker-multi-stage-builds-for-python-developers-a-complete-guide/)
- [Alpine Linux vs Debian Slim Comparison](https://alpinelinuxsupport.com/alpine-linux-vs-debian-slim-lightweight-docker-images-comparison/)
- [Best Docker base image for Python](https://pythonspeed.com/articles/base-image-python-docker-images/)
- [Benchmarking Debian vs Alpine](https://nickjanetakis.com/blog/benchmarking-debian-vs-alpine-as-a-base-docker-image)
- [Podman Performance Documentation](https://github.com/containers/podman/blob/main/docs/tutorials/performance.md)
- [Podman vs Docker 2025 Benchmarks](https://sanj.dev/post/container-runtime-showdown-2025)
- [Why Podman and containerd 2.0 are Replacing Docker in 2026](https://dev.to/dataformathub/deep-dive-why-podman-and-containerd-20-are-replacing-docker-in-2026-32ak)
- [Docker Resource Constraints Docs](https://docs.docker.com/engine/containers/resource_constraints/)
- [Complete Guide to Docker Resource Limits](https://eastondev.com/blog/en/posts/dev/20251218-docker-resource-limits-guide/)
- [Setting Memory and CPU Limits](https://www.baeldung.com/ops/docker-memory-limit)
- [Agent Zero Docker Image](https://hub.docker.com/r/agent0ai/agent-zero)
- [Agent Zero Installation Guide](https://github.com/agent0ai/agent-zero/blob/main/docs/installation.md)
- [Docker Setup DeepWiki](https://deepwiki.com/agent0ai/agent-zero/14.1-docker-setup)
- [GitHub - DockerSlim](https://github.com/docker-slim/docker-slim)
- [Distroless Docker Images Guide](https://bell-sw.com/blog/distroless-containers-for-security-and-size/)

---

## Чек-лист для внедрения

### Этап 1: Немедленно (1-2 дня)

- [ ] Включить prompt caching в настройках Agent Zero
- [ ] Добавить `cache_control` для MiniMax/OpenRouter вызовов
- [ ] Установить UV и мигрировать requirements
- [ ] Переключить a0-launcher на `bun install`

### Этап 2: На этой неделе

- [ ] Настроить Redis/Valkey кэширование для LiteLLM
- [ ] Оптимизировать SearXNG движки и настройки
- [ ] Настроить uWSGI workers и threads
- [ ] Добавить resource limits в docker-compose

### Этап 3: В течение месяца

- [ ] Обновить до Python 3.13, включить JIT
- [ ] Тестировать Bun runtime для a0-launcher
- [ ] Оптимизировать Dockerfile с multi-stage builds
- [ ] Внедрить Redis semantic caching

### Этап 4: Q2 2026

- [ ] Протестировать Python 3.14 free-threading
- [ ] Внедрить семантическое кэширование (GPTCache)
- [ ] Полная миграция на Bun
- [ ] Оптимизировать образ с DockerSlim

---

## Ключевые выводы

1. **Anthropic приобрела Bun** (ноябрь 2025) — это делает миграцию на Bun стратегически правильной для Agent Zero

2. **Python 3.14 free-threading** станет production-ready в 2026 с overhead всего 5-10% — ожидайте 2-4x ускорение для мульти-агентных систем

3. **LLM кэширование даёт самый быстрый ROI** — внедрение Redis + prompt caching может сократить расходы на 70-95% при минимальных усилиях

4. **UV Package Manager** — безрисковая миграция с немедленным эффектом (10-100x ускорение)

5. **Debian Slim > Alpine** для Python workloads — избегайте 15-35% деградации производительности

---

## Общие источники

### Agent Zero
- [Agent Zero AI Official Site](https://www.agent-zero.ai/)
- [Agent Zero GitHub Repository](https://github.com/agent0ai/agent-zero)
- [Agent Zero: The Most Flexible Python Agentic Framework - Medium](https://medium.com/@pankaj_pandey/agent-zero-the-most-flexible-python-agentic-framework-for-real-world-automation-d8ca24d3b83d)
- [Agent Zero DeepWiki](https://deepwiki.com/agent0ai/agent-zero)

---

> Документ подготовлен: Claude Code с использованием 5 параллельных исследовательских агентов
> Дата создания: 2026-01-16

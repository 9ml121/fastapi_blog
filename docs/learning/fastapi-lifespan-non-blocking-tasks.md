# FastAPI 应用启动时执行非阻塞后台任务的最佳实践

在开发 Web 应用时，我们经常需要在应用启动时执行一些初始化任务，例如：清理过期数据、预热缓存、建立连接池等。然而，如果这些任务是耗时的，它们可能会阻塞应用的启动，导致应用在很长一段时间内无法对外提供服务。

本文将详细解释如何在 FastAPI 中，使用 `lifespan` 事件管理器和 `asyncio` 库，优雅地实现一个**非阻塞 (Non-Blocking)** 的启动任务。

## 核心问题：异步框架中的同步阻塞

FastAPI 是一个异步 (Asynchronous) 框架，它的核心是一个事件循环 (Event Loop)。如果在这个主事件循环上运行一个缓慢的、同步的阻塞操作（例如一个耗时30秒的数据库查询），整个应用都会被“冻结”30秒，无法处理任何其他请求。这在生产环境中是灾难性的。

**我们的目标**：在应用启动时触发一个耗时任务，但不能让它拖慢应用的启动速度。应用应该能“发射任务”后，立刻完成启动并开始接受请求。

## 解决方案：Lifespan 与 Asyncio 的组合拳

我们将通过一个清理过期通知的实例，分步解析这个最佳实践。

### 1. `lifespan`：现代的事件管理器

FastAPI 推荐使用 `lifespan` 上下文管理器来处理启动和关闭事件。它结构清晰，将所有生命周期逻辑聚合一处。

一个基本的 `lifespan` 结构如下：

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 应用启动时执行的代码 ---
    print("应用正在启动...")
    
    yield  # <--- 分界线：应用在此处运行

    # --- 应用关闭时执行的代码 ---
    print("应用正在关闭...")

app = FastAPI(lifespan=lifespan)
```

### 2. 隔离同步代码

首先，我们将实际执行数据库操作的逻辑封装在一个独立的、**同步**的函数中。这有助于保持逻辑的清晰和分离。

```python
# crud/notification.py
def cleanup_old_notifications(session: Session) -> int:
    # ... 执行数据库删除操作 ...
    # 返回被删除的记录数量
    return deleted_count

# main.py
def _run_sync_cleanup() -> int:
    """真正的执行者：获取数据库会话并调用CRUD函数"""
    with SessionLocal() as session:
        return notification_crud.cleanup_old_notifications(session)
```

### 3. `asyncio.to_thread`：连接同步与异步的桥梁

为了不阻塞主事件循环，我们需要把上面那个同步的、可能耗时的 `_run_sync_cleanup` 函数扔到一个单独的线程 (Thread) 中去执行。`asyncio.to_thread` 就是为此而生的。

```python
import asyncio

async def _run_async_cleanup() -> None:
    """异步协调者：将同步任务扔到后台线程，并处理结果"""
    try:
        # await 等待后台线程完成任务并返回结果
        deleted_count = await asyncio.to_thread(_run_sync_cleanup)
        if deleted_count:
            logger.info("成功清理了 %d 条过期通知", deleted_count)
    except Exception:
        # 捕获任何异常，防止后台任务崩溃导致主应用受影响
        logger.exception("启动时清理过期通知失败")
```

### 4. `asyncio.create_task`：“发射后不管”的触发器

现在我们有了一个不会阻塞的异步清理函数 `_run_async_cleanup`。最后一步是在应用启动时触发它，并且**不等待它完成**。这就是 `asyncio.create_task` 的作用。

```python
async def _cleanup_notifications_on_startup() -> None:
    """任务的最终触发器"""
    # 将 _run_async_cleanup 任务提交给事件循环，然后立即返回
    asyncio.create_task(_run_async_cleanup())
```

### 5. 完整实现

最后，我们将所有部分组合到 `main.py` 的 `lifespan` 函数中。

```python
# main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

# (此处省略了 _run_sync_cleanup 和 _run_async_cleanup 的定义)

logger = logging.getLogger(__name__)

async def _cleanup_notifications_on_startup() -> None:
    """后台任务：应用启动后清理过期通知"""

    def _run_sync_cleanup() -> int:
        with SessionLocal() as session:
            return notification_crud.cleanup_old_notifications(session)

    async def _run_async_cleanup() -> None:
        try:
            deleted_count = await asyncio.to_thread(_run_sync_cleanup)
            if deleted_count:
                logger.info("成功清理了 %d 条过期通知", deleted_count)
        except Exception:
            logger.exception("启动时清理过期通知失败")

    # “发射后不管”
    asyncio.create_task(_run_async_cleanup())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在应用启动时，调用我们的触发器函数
    await _cleanup_notifications_on_startup()
    yield
    # (此处可以添加应用关闭时需要执行的代码)

# 创建 FastAPI 应用实例
app = FastAPI(lifespan=lifespan)
```

## 工作流程类比：项目经理与工人

你可以把这个流程想象成一个项目开工的场景：

1.  **`lifespan` 函数**：是总指挥，负责宣布项目启动。
2.  **`_cleanup_notifications_on_startup` 函数**：是项目经理。
3.  **`_run_async_cleanup` 函数**：是工头。
4.  **`_run_sync_cleanup` 函数**：是真正干活的工人。

流程如下：
*   项目启动时（应用启动），总指挥（`lifespan`）找到了项目经理（`_cleanup_notifications_on_startup`）。
*   项目经理接到指令后，他不会自己去打扫卫生（执行耗时任务），因为这会耽误他宣布开工。他找到了工头（`_run_async_cleanup`），并用 `asyncio.create_task` 对他说：“你带人去把卫生打了，不用向我汇报，打完就行。” 然后项目经理立刻向总指挥报告“指令已下达”，总指挥随即宣布“项目正式运行！”（`yield`）。
*   工头（`_run_async_cleanup`）接到任务后，他也不会自己去干活，因为他要随时待命。他找到了一个工人（通过 `asyncio.to_thread` 创建的线程），对他说：“你去把卫生打了（`_run_sync_cleanup`），打完告诉我结果。”
*   工人在后台线程里默默打扫卫生。工头则 `await` 等待工人完工。
*   工人完工后，向工头报告“打扫了100处垃圾”。工头记录下这个成果（`logger.info`），任务完成。

整个过程中，总指挥和项目经理都没有被“打扫卫生”这个具体任务所耽搁，项目（Web应用）得以第一时间启动并接待客户（处理请求）。

## 总结

通过 `lifespan` + `asyncio.create_task` + `asyncio.to_thread` 的组合，我们实现了一个健壮、高效的非阻塞启动任务模式。它保证了：
- **快速启动**：应用无需等待耗时任务完成。
- **无阻塞**：耗时的同步代码在独立的线程中运行，不影响主事件循环。
- **逻辑清晰**：同步代码、异步协调、任务触发的职责分离明确。
- **健壮性**：完善的异常处理确保后台任务的失败不会影响主应用的稳定。

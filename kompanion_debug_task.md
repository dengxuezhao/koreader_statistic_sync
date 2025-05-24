# Context
Filename: kompanion_debug_task.md
Created On: [DateTime]
Created By: AI
Associated Protocol: RIPER-5 + Multidimensional + Agent Protocol

# Task Description
帮我调试我的整个代码库，保障使用run.py可以运行服务，所有功能都正常，未实现的功能补充。

# Project Overview
KOReader Statistic Sync (KOmpanion) 是一个用于同步 KOReader 阅读统计数据的应用。它可能包含用户认证、书籍管理、设备管理、数据同步（通过 WebDAV 或其他方式）以及 OPDS 服务等功能。项目使用 FastAPI 框架，Uvicorn 作为 ASGI 服务器，并可能使用 Alembic 进行数据库迁移。

---
*The following sections are maintained by the AI during protocol execution*
---

# Analysis (Populated by RESEARCH mode)
- **启动脚本**: `run.py` 使用 `uvicorn` 启动 FastAPI 应用，入口为 `app.main:app`。
- **核心应用**: `app/main.py` 定义了 FastAPI 应用，包含：
    - Session 中间件 (SECRET_KEY 来自配置, 默认为随机生成，或来自 `KOMPANION_SECRET_KEY` 环境变量)
    - 静态文件和 Jinja2 模板
    - API 路由: `app.api.v1.api_router`, `app.api.webdav.router`, `app.api.opds.router`
    - 启动时创建数据库表 (`Base.metadata.create_all`) - *潜在问题：与 Alembic 冲突/生产环境不适用。但 .env 配置认证和书籍存储为 `memory`，可能部分缓解此问题，需进一步确认哪些表依赖数据库。*
    - 多个前端 HTML 页面路由，多数需要登录 (`is_user_logged_in` 检查 `request.session["user"]`)。
    - `/healthcheck` 端点。
- **配置文件**: 
    - `app/config.py`: 使用 `pydantic-settings` 管理配置，从环境变量 (前缀 `KOMPANION_`) 或 `.env` 文件加载。
    - `.env` 文件设置：
        - `KOMPANION_AUTH_USERNAME=admin`
        - `KOMPANION_AUTH_PASSWORD=password`
        - `KOMPANION_AUTH_STORAGE=memory` (认证信息存内存)
        - `KOMPANION_PG_URL=postgresql://postgres:postgres@localhost:5432/kompanion`
        - `KOMPANION_BSTORAGE_TYPE=memory` (书籍元数据存内存)
- **数据库**: 使用 SQLAlchemy (从 `Base`, `engine` 推断)，`alembic.ini` 和 `migrations/` 表明使用 Alembic。`PG_URL` 在 `.env` 中配置。
- **依赖**: `requirements.txt` 包含 FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic 等标准依赖。
- **认证服务 (`AuthService`) 混乱**: 
    - **存在两个 `AuthService` 定义**:
        1.  `app.service.auth.AuthService`: 
            - 通过 `app.dependencies.get_auth_service` 和 `app.service/__init__.py` 正确注入。
            - 依赖 `UserRepo` (当前为 `MemoryUserRepo`)。
            - 处理用户注册、登录 (bcrypt)、会话、设备管理 (MD5 for KOReader)。
            - **没有 `authenticate_admin` 方法。**
        2.  `app.service.auth_service.AuthService`:
            - 未通过标准依赖注入系统集成。
            - **有 `authenticate_admin` 方法**，直接从配置读取管理员凭据。
            - 包含独立的内存设备管理。
            - 其 `check_device_password` 被 WebDAV/OPDS 的 `basic_auth` 直接调用 (非 FastAPI Depends)。
    - **主要问题**: 
        - `app/api/v1/auth.py` 中的 `web_login` (前端登录处理) 依赖注入的是 `app.service.auth.AuthService`，但却尝试调用其不存在的 `authenticate_admin` 方法。这会导致管理员登录失败 (AttributeError)。
        - WebDAV/OPDS 认证逻辑与主应用认证逻辑分离，直接使用了 `app.service.auth_service.AuthService` 的部分功能。
- **待确认/潜在问题点**:
    1.  **数据库初始化与存储配置**: `app/main.py` 中的 `create_all` 的实际影响，考虑到 `.env` 中 `AUTH_STORAGE` 和 `BSTORAGE_TYPE` 均为 `memory`，并且 `AuthService` 存在混乱。需要理清数据持久化策略。
    2.  **管理员用户初始化与登录**: 鉴于 `AuthService` 的混乱，管理员账户的创建（如果 `AUTH_STORAGE=memory`）和登录流程 (`web_login`) 存在严重问题。
    3.  **依赖注入的服务实现** (功能是否完整且与配置 (`memory` storage) 及统一后的 `AuthService` 兼容):
        - `get_book_shelf` / `BookShelf`
        - `get_progress_sync` / `ProgressSync`
        - `get_reading_stats` / `ReadingStats`
    4.  **API 路由功能** (功能是否完整且与配置 (`memory` storage) 及统一后的 `AuthService` 兼容):
        - `app.api.v1.api_router` (其他非 auth 路由)
        - `app.api.webdav.router` (特别是认证部分)
        - `app.api.opds.router` (特别是认证部分)
    5.  **未实现的功能补充**: 在解决现有问题后，需要明确哪些功能是预期但尚未实现的，并进行补充。

# Proposed Solution (Populated by INNOVATE mode)
主要目标是统一认证逻辑，解决 `AuthService` 的混乱问题，确保管理员能够登录，并使 WebDAV/OPDS 认证与主系统一致。

**首选方案：增强 `app.service.auth.AuthService` 并移除 `app.service.auth_service.AuthService`**

1.  **统一 `AuthService` 实现:**
    *   **目标**: `app.service.auth.AuthService` (以下简称 `MainAuthService`) 成为唯一的认证服务。
    *   **管理员认证**: 
        *   在 `MainAuthService` 中增加一个方法，例如 `async def authenticate_admin_via_config(self, username: str, password: str) -> Optional[UserSessionInfo]:`。
        *   此方法直接从 `self.settings` (需要确保 `MainAuthService` 能访问 `Settings`，可以通过构造函数注入或从 `self.user_repo` 间接获取) 读取 `AUTH_USERNAME` 和 `AUTH_PASSWORD` 进行比较。
        *   成功则返回 `UserSessionInfo(id="config_admin", username=username, is_superuser=True)`。
        *   修改 `app/api/v1/auth.py` 中的 `web_login` 端点，使其调用 `auth_service.authenticate_admin_via_config()`。
    *   **设备认证 (WebDAV/OPDS)**:
        *   确保 `MainAuthService` 的 `check_device_password(self, device_name: str, password: str, plain: bool = False)` 方法能够正确处理KOReader的MD5密码逻辑 (目前看起来是正确的，`plain=True` 时直接比较传入的MD5哈希，`plain=False` 时将传入的明文密码MD5哈希后再比较)。
        *   修改 `app/api/webdav/router.py` 和 `app/api/opds/router.py` 中的 `basic_auth` 依赖函数：
            *   使其通过 `auth_service: Annotated[AuthService, Depends(get_auth_service)]` 获取 `MainAuthService` 实例。
            *   调用 `auth_service.check_device_password()` 进行设备认证。
            *   对于 OPDS，如果设备认证失败，可以尝试调用 `auth_service.check_password()` (或一个更通用的用户认证方法) 进行普通用户认证（如果OPDS也支持普通用户登录）。
    *   **清理**: 删除 `app.service.auth_service.py` 文件及其所有引用。

2.  **管理员用户初始化与 `.env` 配置**: 
    *   由于 `AUTH_STORAGE=memory`，通过上述 `authenticate_admin_via_config` 方法，管理员用户不需要在 `MemoryUserRepo` 中显式创建。认证直接基于配置文件。
    *   `app/main.py` 中 `Initialize auth service with admin user will be done later` 的注释可以移除或更新，说明管理员通过配置进行认证。

3.  **数据库表创建 (`create_all`) 与 Alembic**:
    *   **调研**: 检查 `app.models` (或 SQLAlchemy 模型定义的位置)，确定在 `AUTH_STORAGE=memory` 和 `BSTORAGE_TYPE=memory` 的情况下，`Base.metadata.create_all` 实际会创建哪些表。
    *   **策略**: 
        *   如果这些表并非必要（例如，与内存存储服务相关的模型不应该在数据库中创建），或者如果所有核心数据都由内存服务处理，可以考虑在特定配置下（如全内存模式）条件性地跳过 `app/main.py` 中的 `create_all`。
        *   长期来看，所有数据库结构变更应由 Alembic 管理。生产环境中不应依赖 `create_all`。

4.  **后续检查与功能实现**: 
    *   在认证问题解决后，系统性检查和调试其他服务 (`BookShelf`, `ProgressSync`, `ReadingStats`) 和 API 路由。
    *   明确并实现标记为"未实现"或功能不完整的部分 (例如 WebDAV 的实际目录服务, OPDS 书籍列表, `/books` 和 `/devices` 页面的后端逻辑)。

**此方案的优点**: 
- 保持了依赖注入的清晰性。
- 重用了大部分现有的、结构较好的 `app.service.auth.AuthService` 代码。
- 逐步统一认证逻辑。

# Implementation Plan (Generated by PLAN mode)
Implementation Checklist:
1. [Specific action 1]
2. [Specific action 2]
...
n. [Final action]
```

# Current Execution Step (Updated by EXECUTE mode when starting a step)
> Currently executing: "[Step number and name]"

# Task Progress (Appended by EXECUTE mode after each step completion)
*   [DateTime]
    *   Step: [Checklist item number and description]
    *   Modifications: [List of file and code changes, including reported minor deviation corrections]
    *   Change Summary: [Brief summary of this change]
    *   Reason: [Executing plan step [X]]
    *   Blockers: [Any issues encountered, or None]
    *   User Confirmation Status: [Success / Success with minor issues / Failure]
*   [DateTime]
    *   Step: ...

# Final Review (Populated by REVIEW mode)
[对最终计划的实施合规性评估摘要，是否发现未报告的偏差] 
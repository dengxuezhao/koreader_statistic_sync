# KOmpanion Python版

KOmpanion是一个与KOReader紧密集成的书架Web应用程序。
这是使用Python（FastAPI）重新实现的版本，基于原始的Go实现。

## 主要功能

- 上传和查看您的书架
- 通过OPDS下载书籍
- KOReader同步阅读进度API
- 通过WebDAV获取KOReader书籍统计数据
- 完整的Web用户界面，支持书籍和设备管理

## 安装

### 使用Docker Compose（推荐）

1. 克隆仓库
```bash
git clone https://github.com/yourusername/kompanion-python.git
cd kompanion-python
```

2. 启动服务
```bash
docker-compose up -d
```

这将启动PostgreSQL数据库和KOmpanion应用程序，您可以通过访问 http://localhost:8080 使用该应用程序。

### 本地开发

1. 克隆仓库
```bash
git clone https://github.com/yourusername/kompanion-python.git
cd kompanion-python
```

2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
pip install -r requirements.txt
```

3. 设置环境变量

您可以直接在`.env`文件中设置以下环境变量：

```
KOMPANION_AUTH_USERNAME=admin
KOMPANION_AUTH_PASSWORD=password
KOMPANION_AUTH_STORAGE=memory
KOMPANION_PG_URL=postgresql://postgres:postgres@localhost:5432/kompanion
KOMPANION_BSTORAGE_TYPE=memory
```

4. 运行应用程序

**使用新的启动脚本**（推荐）:
```bash
# 简单启动
python run.py

# 指定主机和端口
python run.py --host 0.0.0.0 --port 9090

# 开发模式（启用热重载）
python run.py --reload

# 禁用详细日志输出
python run.py --no-log
```

**使用uvicorn直接启动**:
```bash
uvicorn app.main:app --reload
```

## 配置

以下环境变量可用于配置应用程序：

- `KOMPANION_AUTH_USERNAME` - 管理员用户名（必需）
- `KOMPANION_AUTH_PASSWORD` - 管理员密码（必需）
- `KOMPANION_AUTH_STORAGE` - 认证存储类型（"postgres"或"memory"，默认："postgres"）
- `KOMPANION_HTTP_PORT` - HTTP服务端口（默认：8080）
- `KOMPANION_LOG_LEVEL` - 日志级别（"debug"、"info"或"error"，默认："info"）
- `KOMPANION_PG_URL` - PostgreSQL连接URL
- `KOMPANION_PG_POOL_MAX` - PostgreSQL连接池大小（默认：2）
- `KOMPANION_BSTORAGE_TYPE` - 书籍存储类型（"postgres"、"memory"或"filesystem"，默认："postgres"）
- `KOMPANION_BSTORAGE_PATH` - 当存储类型为"filesystem"时的文件系统路径

## 本地测试

详细的本地测试指南请参阅 [LOCAL_TESTING.md](LOCAL_TESTING.md) 文件。此文档提供了完整的测试指南，包括:

- 环境设置
- 运行应用程序
- API测试示例
- 用户认证测试
- 书籍管理测试
- 阅读进度和统计测试
- KOReader集成测试
- 常见问题解决方案

## KOReader设置

### Web界面

首先，您需要添加您的设备：
1. 访问服务
2. 登录
3. 单击设备
4. 添加设备名称和密码

**警告：** 设备密码以不带盐的md5哈希存储，以兼容[kosync插件](https://github.com/koreader/koreader/blob/master/plugins/kosync.koplugin/main.lua#L544)。

### KOReader设置

在KOReader中配置以下插件：
1. 云存储
   1. 添加新的WebDAV：URL - `https://your-kompanion.org/webdav/`，用户名 - 设备名，密码 - 密码
2. 统计 - 设置 - 云同步
   1. 列表为空没关系，只需按下**长按选择当前文件夹**。
3. 打开书籍 - 工具 - 进度同步
   1. 自定义同步服务器：`https://your-kompanion.org/`
   2. 登录：用户名 - 设备名，密码 - 密码
4. 设置OPDS目录：
   1. 工具栏 -> 搜索 -> OPDS目录
   2. 点击加号
   3. 目录URL：`https://your-kompanion.org/opds/`，用户名 - 设备名，密码 - 密码

## 开发

本项目使用FastAPI框架开发，主要组件包括：

- FastAPI：Web框架
- SQLAlchemy：ORM
- Pydantic：数据验证
- Alembic：数据库迁移
- Jinja2：模板渲染

### 项目结构

```
pythonversion/
├── app/                    # 应用程序主体
│   ├── api/                # API路由
│   ├── entity/             # 实体模型
│   ├── repository/         # 数据访问层
│   ├── service/            # 业务逻辑层
│   ├── storage/            # 存储抽象层
│   └── web/                # Web界面
├── migrations/             # 数据库迁移
├── tests/                  # 测试
├── run.py                  # 便捷启动脚本
├── LOCAL_TESTING.md        # 本地测试指南
├── README.md               # 项目文档
├── requirements.txt        # 依赖管理
└── Dockerfile              # Docker构建文件
```

## 贡献

欢迎贡献！请随时提交问题或拉取请求。

## 功能介绍

### Web用户界面

KOmpanion提供了一个功能完善的Web用户界面，可以直接在浏览器中管理您的书籍和设备：

- **控制台**: 展示书籍和设备的统计信息，提供主要功能的快速入口。
- **书库管理**: 上传、查看、排序和下载您的电子书。
- **设备管理**: 添加和管理KOReader设备，方便进行统计和进度同步。

### OPDS目录

KOmpanion提供OPDS（Open Publication Distribution System）目录，使您能够通过KOReader或其他支持OPDS的阅读器访问您的书库：

- 完整的书籍元数据
- 支持封面图片
- 分类浏览

### 同步功能

- **进度同步**: 在多台KOReader设备间同步阅读进度。
- **统计同步**: 通过WebDAV获取KOReader的阅读统计数据。 
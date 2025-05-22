# KOmpanion Python版本 - 本地测试指南

本文档提供了在本地环境中运行和测试KOmpanion Python版本的详细指南。

## 目录

- [环境设置](#环境设置)
- [运行应用程序](#运行应用程序)
- [功能测试](#功能测试)
  - [Web界面测试](#web界面测试)
  - [用户认证API测试](#用户认证api测试)
  - [书籍管理API测试](#书籍管理api测试)
  - [进度同步API测试](#进度同步api测试)
  - [统计API测试](#统计api测试)
  - [KOReader集成测试](#koreader集成测试)
- [故障排除](#故障排除)
- [API参考](#api参考)

## 环境设置

### 前提条件

- Python 3.9或更高版本
- pip（Python包管理器）
- PostgreSQL（可选，默认配置使用内存存储）

### 安装依赖

1. 进入项目目录：
   ```bash
   cd pythonversion
   ```

2. 安装所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 配置环境变量

项目默认使用`.env`文件中的配置。以下是默认配置：

```
KOMPANION_AUTH_USERNAME=admin
KOMPANION_AUTH_PASSWORD=password
KOMPANION_AUTH_STORAGE=memory
KOMPANION_PG_URL=postgresql://postgres:postgres@localhost:5432/kompanion
KOMPANION_BSTORAGE_TYPE=memory
```

这个配置使用内存存储模式，不需要PostgreSQL数据库。如果您想使用PostgreSQL：

1. 确保PostgreSQL数据库已安装并运行
2. 修改`.env`文件中的`KOMPANION_AUTH_STORAGE`和`KOMPANION_BSTORAGE_TYPE`为`postgres`
3. 确保`KOMPANION_PG_URL`指向正确的PostgreSQL连接URL

## 运行应用程序

### 启动应用

在项目根目录下运行：

```bash
# 使用新的run.py脚本运行（推荐）
python run.py --reload

# 或者使用uvicorn直接运行
python -m uvicorn app.main:app --reload --port 8080
```

应用将在`http://localhost:8080`上运行，并且开启了热重载功能，当您修改代码时应用会自动重启。

### 访问应用

- Web界面：打开浏览器访问 http://localhost:8080/
- API文档：打开浏览器访问 http://localhost:8080/docs 或 http://localhost:8080/redoc

## 功能测试

### Web界面测试

KOmpanion现在提供了一个完整的Web用户界面，让您可以直接在浏览器中管理KOReader书籍和设备。

#### 1. 管理员登录

1. 访问 http://localhost:8080/login
2. 使用您在环境变量中设置的管理员账户登录：
   - 用户名：`KOMPANION_AUTH_USERNAME`的值（默认为`admin`）
   - 密码：`KOMPANION_AUTH_PASSWORD`的值（默认为`password`）
3. 登录后，您将被重定向到控制台页面

#### 2. 控制台

控制台页面显示您的书籍和设备的基本统计信息，以及主要功能的快速入口。测试以下功能：

1. 检查顶部导航菜单是否包含：控制台、书库、设备和登出选项
2. 验证书籍和设备的统计数据是否正确显示
3. 确认OPDS链接是否正确显示，并且可以复制

#### 3. 书库管理

访问 http://localhost:8080/books 测试书籍管理功能：

1. **上传书籍**：
   - 点击"选择电子书文件"按钮
   - 选择一个EPUB、MOBI或PDF文件
   - 点击"上传"按钮
   - 验证上传进度条是否正常显示
   - 确认上传成功后书籍是否出现在列表中

2. **书籍列表**：
   - 验证书籍卡片是否正确显示书名、作者和封面
   - 测试排序功能（按上传时间、书名、作者）
   - 测试分页功能（如果有多本书）

3. **书籍操作**：
   - 测试下载按钮是否可以正常下载书籍
   - 测试删除按钮是否可以正常删除书籍

#### 4. 设备管理

访问 http://localhost:8080/devices 测试设备管理功能：

1. **添加设备**：
   - 在设备名称和密码字段中输入信息
   - 点击"添加设备"按钮
   - 确认设备成功添加并显示在列表中
   - 记录设备名称和密码，这将用于KOReader设备配置

2. **设备列表**：
   - 验证设备列表是否正确显示设备名称和添加时间
   - 测试删除按钮是否可以正常删除设备

#### 5. 登出

1. 点击顶部导航栏中的"登出"选项
2. 确认您被重定向到登录页面或主页
3. 尝试访问控制台、书库或设备页面，应该会被重定向到登录页面

### 用户认证API测试

您可以使用curl、Postman或任何API测试工具测试以下API端点：

#### 1. 注册新用户

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser", "password":"testpassword"}'
```

#### 2. 用户登录获取令牌

```bash
curl -X POST http://localhost:8080/api/v1/auth/token \
  -d "username=testuser&password=testpassword" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

将返回的访问令牌保存为环境变量（示例为Linux/macOS）：

```bash
export TOKEN=<返回的access_token值>
```

#### 3. 获取当前用户信息

```bash
curl -X GET http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. 注册新设备

```bash
curl -X POST http://localhost:8080/api/v1/auth/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"mydevice"}'
```

#### 5. 获取设备列表

```bash
curl -X GET http://localhost:8080/api/v1/auth/devices \
  -H "Authorization: Bearer $TOKEN"
```

### 书籍管理API测试

#### 1. 上传新书籍

准备一个电子书文件（EPUB、PDF或MOBI格式）进行测试：

```bash
curl -X POST http://localhost:8080/api/v1/books \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/ebook.epub"
```

保存返回的书籍ID：

```bash
export BOOK_ID=<返回的book_id值>
```

#### 2. 获取书籍列表

```bash
curl -X GET "http://localhost:8080/api/v1/books?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. 获取书籍详情

```bash
curl -X GET http://localhost:8080/api/v1/books/$BOOK_ID \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. 更新书籍元数据

```bash
curl -X PUT http://localhost:8080/api/v1/books/$BOOK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"新标题", "author":"新作者", "publisher":"新出版商"}'
```

#### 5. 下载书籍

```bash
curl -X GET http://localhost:8080/api/v1/books/$BOOK_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded_book.epub
```

#### 6. 查看书籍封面

```bash
curl -X GET http://localhost:8080/api/v1/books/$BOOK_ID/cover \
  -H "Authorization: Bearer $TOKEN" \
  -o book_cover.jpg
```

### 进度同步API测试

#### 1. 更新阅读进度

```bash
curl -X PUT http://localhost:8080/api/v1/progress/progress \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ=" \
  -H "Content-Type: application/json" \
  -d '{
    "document": "document_hash",
    "percentage": 25.5,
    "progress": "page 50",
    "device": "mydevice",
    "device_id": "device123",
    "timestamp": 1620000000
  }'
```

注意：Basic认证的值是`设备名:设备密码`的Base64编码。

#### 2. 获取阅读进度

```bash
curl -X GET http://localhost:8080/api/v1/progress/progress/document_hash \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ="
```

### 统计API测试

#### 1. 获取阅读统计

```bash
curl -X GET "http://localhost:8080/api/v1/stats?book_id=document_hash" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2. 获取阅读摘要

```bash
curl -X GET "http://localhost:8080/api/v1/stats/summary?period=month" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. 获取书籍统计

```bash
curl -X GET http://localhost:8080/api/v1/stats/books/document_hash \
  -H "Authorization: Bearer $TOKEN"
```

#### 4. 获取阅读趋势

```bash
curl -X GET "http://localhost:8080/api/v1/stats/trends?metric=reading_time&period=week&last_n=4" \
  -H "Authorization: Bearer $TOKEN"
```

### KOReader集成测试

#### WebDAV接口测试

##### 1. 上传统计数据

准备一个SQLite数据库文件（可以是空的）进行测试：

```bash
curl -X PUT http://localhost:8080/webdav/statistics.sqlite3 \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ=" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @/path/to/statistics.sqlite3
```

##### 2. 下载统计数据

```bash
curl -X GET http://localhost:8080/webdav/statistics.sqlite3 \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ=" \
  -o downloaded_statistics.sqlite3
```

#### OPDS接口测试

##### 1. 获取OPDS根目录

```bash
curl -X GET http://localhost:8080/opds/ \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ="
```

##### 2. 获取最新书籍列表

```bash
curl -X GET http://localhost:8080/opds/newest/ \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ="
```

##### 3. 下载书籍

```bash
curl -X GET http://localhost:8080/opds/book/$BOOK_ID/download \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ=" \
  -o opds_downloaded_book.epub
```

##### 4. 查看书籍封面

```bash
curl -X GET http://localhost:8080/opds/book/$BOOK_ID/cover \
  -H "Authorization: Basic bXlkZXZpY2U6ZGV2aWNlcGFzc3dvcmQ=" \
  -o opds_book_cover.jpg
```

## 故障排除

### 常见问题

#### 1. 运行应用时出现`ModuleNotFoundError: No module named 'app'`

确保您在正确的目录中运行命令。您应该在`pythonversion`目录中，而不是在内部的`pythonversion`子目录中。

#### 2. 数据库连接错误

如果您使用PostgreSQL模式（将`KOMPANION_AUTH_STORAGE`和`KOMPANION_BSTORAGE_TYPE`设置为`postgres`），请确保：

- PostgreSQL数据库已安装并运行
- 数据库`kompanion`已创建
- `.env`文件中的`KOMPANION_PG_URL`指向正确的连接URL
- 用户`postgres`具有正确的权限

#### 3. 静态资源加载错误

如果Web界面中的CSS、JavaScript或图片无法加载，请确保：

- 静态文件目录`app/web/static`存在
- 静态文件已正确创建（CSS、JavaScript文件）

## API参考

完整的API文档可在应用运行时通过访问 http://localhost:8080/docs 或 http://localhost:8080/redoc 获取。 
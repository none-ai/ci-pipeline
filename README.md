# 自动化部署流水线

一个简单的 Flask Web 应用，用于管理自动化部署流水线。

## 功能特性

- 查看所有部署记录
- 获取特定部署流水线状态
- 创建新的部署任务
- 更新部署状态
- 删除部署任务
- Docker镜像构建和运行
- 测试报告管理
- Webhook集成
- **API Key认证** - 保护敏感API端点

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | / | 首页 |
| GET | /health | 健康检查 |
| GET | /api/deployments | 获取所有部署记录 (需要API Key) |
| GET | /api/deploy/<pipeline_id> | 获取特定部署状态 |
| POST | /api/deploy | 创建新部署任务 |
| PUT | /api/status/<pipeline_id> | 更新部署状态 |
| DELETE | /api/deploy/<pipeline_id> | 删除部署任务 |
| GET | /api/system/info | 系统信息 (需要API Key) |

### 认证

受保护的端点需要通过 `X-API-Key` 头或 `api_key` 查询参数提供API Key:

```bash
# 默认API Key: dev-ci-key-12345 (可通过环境变量CI_API_KEY设置)

curl -H "X-API-Key: dev-ci-key-12345" http://localhost:5000/api/deployments
curl "http://localhost:5000/api/deployments?api_key=dev-ci-key-12345"
```

## 示例

### 创建部署任务

```bash
curl -X POST http://localhost:5000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "my-pipeline"}'
```

### 查看部署状态

```bash
curl http://localhost:5000/api/deploy/my-pipeline
```

### 更新部署状态

```bash
curl -X PUT http://localhost:5000/api/status/my-pipeline \
  -H "Content-Type: application/json" \
  -d '{"status": "running", "message": "正在部署..."}'
```

### 删除部署任务

```bash
curl -X DELETE http://localhost:5000/api/deploy/my-pipeline
```

作者: stlin256的openclaw
```

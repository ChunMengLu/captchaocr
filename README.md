# Captcha OCR API

基于 ddddocr + FastAPI 实现的通用验证码识别服务

## 特性

- 🚀 基于 FastAPI 框架，高性能异步处理
- 🔄 支持多线程 OCR 实例池，提高并发处理能力
- 📦 简化依赖，仅需核心库
- 🐳 支持 Docker 部署
- 📝 自动生成 API 文档（Swagger UI）

## 快速开始

### 环境要求

- Python >= 3.8

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

通过环境变量配置服务参数（可选）：

```bash
# 监听地址（默认: 0.0.0.0）
export LISTEN_HOST=0.0.0.0

# 监听端口（默认: 5000）
export PORT=5000

# OCR 工作线程数（默认: 10）
export WORKER_THREADS=10
```

### 启动服务

```bash
python main.py
```

或者使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 5000
```

### API 文档

启动服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## API 接口

### POST /ocr

验证码识别接口

**请求参数：**
- `file`: 图片文件（multipart/form-data，支持 jpg, png, jpeg 格式）

**响应示例：**
```json
{
  "status": true,
  "msg": "SUCCESS",
  "result": "识别结果",
  "usage": 0.123
}
```

**使用示例：**

```bash
curl -X POST "http://localhost:5000/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@captcha.png"
```

### GET /

健康检查接口

**响应示例：**
```json
{
  "status": true,
  "msg": "Captcha OCR Service is running",
  "workers": 10,
  "available_workers": 8
}
```

## 部署方式

### Docker 部署

#### 构建镜像

```bash
docker build -t captchaocr .
```

#### 运行容器

```bash
docker run -d \
  -p 5000:5000 \
  -e WORKER_THREADS=10 \
  --name captchaocr \
  captchaocr
```

#### 查看日志

```bash
docker logs -f captchaocr
```

### Docker Compose 部署

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  captchaocr:
    build: .
    container_name: captchaocr
    ports:
      - "5000:5000"
    environment:
      - LISTEN_HOST=0.0.0.0
      - PORT=5000
      - WORKER_THREADS=10
    restart: unless-stopped
```

启动服务：

```bash
docker-compose up -d
docker-compose logs -f
```

### 生产环境部署

#### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:5000 \
  --timeout 120
```

#### 使用 Nginx 反向代理

Nginx 配置示例：

```nginx
upstream captchaocr {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 10M;

    location / {
        proxy_pass http://captchaocr;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 性能优化

1. **调整 WORKER_THREADS**：根据服务器 CPU 核心数和并发需求调整 OCR 工作线程数
2. **使用多进程**：在生产环境使用 Gunicorn 多 worker 模式
3. **监控和日志**：建议集成监控系统（如 Prometheus）和日志收集系统

## 故障排查

### 检查服务状态

```bash
curl http://localhost:5000/
```

### 查看日志

Docker 部署：
```bash
docker logs -f captchaocr
```

### 常见问题

1. **端口被占用**：修改 PORT 环境变量或检查端口占用情况
2. **内存不足**：减少 WORKER_THREADS 数量
3. **识别速度慢**：增加 WORKER_THREADS 数量或使用更高配置的服务器

## 技术栈

- FastAPI: 现代、快速的 Web 框架
- ddddocr: 验证码识别库
- uvicorn: ASGI 服务器

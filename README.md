# 会议纪要智能整理与待办提取系统

本项目用于处理会议录音或会议原始文字，自动生成结构化会议纪要，并提取待办事项。系统支持人工确认待办，确认后的待办可按状态追踪。

## 功能概览

- 会议文本整理：提取会议主题、参与人员、讨论要点、决议事项。
- 音频转写：上传会议音频后调用科大讯飞极速录音转写。
- 待办提取：从会议纪要中提取任务描述、负责人、截止日期。
- 待办确认：人工确认 AI 生成的待办草稿后写入正式待办。
- 待办追踪：按待开始、进行中、已完成筛选和更新待办。

## 技术架构

- 后端 API：FastAPI
- AI 工作流：LangChain + LangGraph
- 前端：Vue + Vite
- 数据库：MySQL
- 消息队列：Kafka
- 缓存/扩展组件：Redis
- 本地中间件运行方式：Docker Compose
- 应用服务运行方式：本机 Python 虚拟环境 + 本机 Node 环境

也就是说：**MySQL、Redis、Kafka 放在 Docker 里运行；FastAPI、AI worker、Vue 前端在本机运行。**

## 一、新电脑环境准备

请先安装：

- Docker Desktop Windows
- Python 3.11 或 3.12
- Node.js 20+
- Git
- 可选：ffmpeg，用于把 m4a/wav/mp3 转成讯飞推荐格式

确认命令可用：

```powershell
docker --version
python --version
node --version
npm --version
git --version
```

如果要测试音频上传，建议也确认：

```powershell
ffmpeg -version
```

## 二、拉取项目

示例目录使用 `D:\demo\meeting-minutes-ai`，你也可以换成自己的目录。

```powershell
cd D:\demo
git clone 你的GitHub仓库地址 meeting-minutes-ai
cd D:\demo\meeting-minutes-ai
```

## 三、创建 Python 虚拟环境

建议把虚拟环境放到 `D:\demo\.venv`，避免默认装到 C 盘。

```powershell
python -m venv D:\demo\.venv
D:\demo\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

## 四、安装前端依赖

```powershell
cd D:\demo\meeting-minutes-ai\frontend
npm.cmd install
cd D:\demo\meeting-minutes-ai
```

## 五、配置环境变量

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`。

如果只想先跑通系统页面，可以先使用 mock：

```env
LLM_PROVIDER=mock
ASR_PROVIDER=mock
```

如果要接入真实 DeepSeek 和科大讯飞，配置为：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=你的DeepSeekKey
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro

ASR_PROVIDER=iflytek-speed
XFEI_APP_ID=你的讯飞APPID
XFEI_API_KEY=你的讯飞APIKey
XFEI_API_SECRET=你的讯飞APISecret
XFEI_ASR_DOMAIN=pro_ost_ed
XFEI_ASR_LANGUAGE=zh_cn
XFEI_ASR_ACCENT=mandarin
XFEI_ASR_VSPP_ON=1
```

数据库和中间件默认配置如下，通常不用改：

```env
DATABASE_URL=mysql+pymysql://meeting:meeting_pwd@127.0.0.1:3306/meeting_minutes
REDIS_URL=redis://127.0.0.1:6379/0
KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092

MYSQL_DATABASE=meeting_minutes
MYSQL_USER=meeting
MYSQL_PASSWORD=meeting_pwd
MYSQL_ROOT_PASSWORD=root_pwd
```

音频文件保存目录默认：

```env
STORAGE_AUDIO_DIR=D:/demo/.storage/audio
```

## 六、启动 MySQL、Redis、Kafka

确保 Docker Desktop 已启动，然后执行：

```powershell
docker-compose up -d mysql redis kafka
```

查看容器状态：

```powershell
docker ps
```

看到以下容器正常运行即可：

- `meeting_minutes_mysql`
- `meeting_minutes_redis`
- `meeting_minutes_kafka`

## 七、初始化数据库

执行数据库迁移：

```powershell
cd D:\demo\meeting-minutes-ai
D:\demo\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

创建管理员账号：

```powershell
$env:PYTHONPATH="backend"
D:\demo\.venv\Scripts\python.exe -m app.cli.seed_admin --username admin --password admin123 --display-name admin
```

## 八、启动后端 API

打开一个新的 PowerShell 窗口：

```powershell
cd D:\demo\meeting-minutes-ai
D:\demo\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

验证后端：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

期望输出：

```text
status
------
ok
```

## 九、启动 AI worker

再打开一个新的 PowerShell 窗口：

```powershell
cd D:\demo\meeting-minutes-ai
$env:PYTHONPATH="backend"
D:\demo\.venv\Scripts\python.exe -m app.worker.main
```

worker 正常启动后通常不会持续输出日志，它会等待 Kafka 里的任务消息。

注意：如果修改了 `.env`、AI 提示词、ASR 代码或 worker 代码，需要重启 worker。

## 十、启动 Vue 前端

再打开一个新的 PowerShell 窗口：

```powershell
cd D:\demo\meeting-minutes-ai\frontend
npm.cmd run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

默认管理员账号：

```text
用户名：admin
密码：admin123
```

## 十一、创建普通用户

可以使用管理员登录后通过接口创建，也可以直接用命令创建一个普通用户：

```powershell
cd D:\demo\meeting-minutes-ai
$env:PYTHONPATH="backend"
D:\demo\.venv\Scripts\python.exe -c "from app.core.db import SessionLocal; from app.core.security import hash_password; from app.models.user import User, UserRole, UserStatus; from sqlalchemy import select; db=SessionLocal(); user=db.scalar(select(User).where(User.username=='member')); user=user or User(username='member',password_hash=hash_password('member123'),display_name='普通用户',email=None,role=UserRole.MEMBER,status=UserStatus.ACTIVE); db.add(user); db.commit(); print('member / member123'); db.close()"
```

普通用户账号：

```text
用户名：member
密码：member123
```

## 十二、音频上传要求

当前科大讯飞极速录音转写链路推荐上传：

```text
MP3 / lame 编码 / 16kHz / 单声道
```

如果你手里是 m4a 文件，可以用 ffmpeg 转换：

```powershell
ffmpeg -i "D:\path\input.m4a" -ac 1 -ar 16000 -codec:a libmp3lame -b:a 64k "D:\path\meeting-16k-mono.mp3"
```

然后上传 `meeting-16k-mono.mp3`。

## 十三、常用验证命令

后端测试：

```powershell
cd D:\demo\meeting-minutes-ai
$env:PYTHONPATH="backend"
D:\demo\.venv\Scripts\python.exe -m pytest backend\tests -q
```

后端代码检查：

```powershell
D:\demo\.venv\Scripts\ruff.exe check backend
```

数据库迁移检查：

```powershell
D:\demo\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini check
```

前端测试和构建：

```powershell
cd D:\demo\meeting-minutes-ai\frontend
npm.cmd test
npm.cmd run build
```

## 十四、常见问题

### 1. 前端打不开或接口报错

确认后端是否启动：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

### 2. 新建会议一直处理中

确认 worker 是否启动：

```powershell
cd D:\demo\meeting-minutes-ai
$env:PYTHONPATH="backend"
D:\demo\.venv\Scripts\python.exe -m app.worker.main
```

### 3. 会议结果还是 mock

检查 `.env`：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=你的DeepSeekKey
```

修改 `.env` 后需要重启 backend 和 worker。

### 4. 音频上传后 ASR 失败

常见原因：

- 科大讯飞应用没有开通极速录音转写服务。
- `XFEI_APP_ID / XFEI_API_KEY / XFEI_API_SECRET` 不匹配。
- 音频不是 16kHz 单声道 MP3。
- 文件虽然叫 `.mp3`，但实际是 m4a/mp4 容器。

建议先用 ffmpeg 转换后再上传：

```powershell
ffmpeg -i "input.m4a" -ac 1 -ar 16000 -codec:a libmp3lame -b:a 64k "meeting-16k-mono.mp3"
```

### 5. 页面时间比真实时间少 8 小时

请确认后端是最新代码，并重启 backend。当前 API 会把 UTC 时间返回为带 `Z` 的 ISO 字符串，浏览器会自动显示成本地时间。

## 十五、服务启动顺序总结

新电脑第一次运行，按顺序执行：

```text
1. docker-compose up -d mysql redis kafka
2. alembic upgrade head
3. seed admin
4. 启动 FastAPI backend
5. 启动 AI worker
6. 启动 Vue frontend
7. 打开 http://127.0.0.1:5173
```

# Email Priority Agent Prototype

一个基于 Streamlit 的邮件优先级分类原型，支持多模型切换：

- Claude
- GPT
- Gemini
- MiniMax

## 项目结构

```text
prototype-upload/
├── app.py
├── core/
├── config/
├── test_cases/
├── requirements.txt
└── .env.example
```

## 本地运行

1. 创建虚拟环境并安装依赖：

```bash
pip install -r requirements.txt
```

2. 复制配置文件：

```bash
cp .env.example .env
```

3. 在 `.env` 中填入你拥有的 API Key。

4. 启动应用：

```bash
streamlit run app.py
```

## 环境变量

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `MINIMAX_API_KEY`

可选模型覆盖：

- `ANTHROPIC_MODEL`
- `OPENAI_MODEL`
- `GEMINI_MODEL`
- `MINIMAX_MODEL`

## 上传仓库前说明

- `.env` 不要上传
- 本仓库已通过 `.gitignore` 排除缓存和本地配置
- 如果要公开仓库，请确认 `config/user_context.json` 中的人名和业务信息可以公开

# 使用官方 Python 3.12 轻量级镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /code

# --- 关键步骤：安装 OpenCV 所需的系统依赖 ---
# slim 镜像为了精简，缺少一些图形库，会导致 OpenCV 报错。这里必须手动安装。
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单到容器中
COPY ./requirements.txt /code/requirements.txt

# 安装 Python 依赖
# --no-cache-dir 可以减小镜像体积
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 复制项目的源代码目录到容器的 /code/src
COPY ./src /code/src

# --- Hugging Face 特有配置 ---
# HF Spaces 默认监听 7860 端口，我们需要让 uvicorn 启动在这个端口上。
# 且必须监听 0.0.0.0 (允许外部访问)
CMD ["uvicorn", "src.medcrux.api.main:app", "--host", "0.0.0.0", "--port", "7860"]

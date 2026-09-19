# Mekiki Reader — Hugging Face の Docker Space 用（SPEC v2.4 §3・§9）
#
# 基底は Python 3.13.15 の slim（Debian trixie）。タグではなくダイジェストで固定する
# （2026-09-19 に Docker Hub の registry で確認。python:3.13-slim・3.13.15-slim・3.13.15-slim-trixie は同じダイジェスト）。
FROM python:3.13.15-slim-trixie@sha256:9d2e5553305c7c7b0097999bb17187c69b921ccd6bc9d40e4bb5ebe652c00285

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MEKIKI_READER_MODE=spaces

# Spaces はコンテナを利用者 ID 1000 で動かす
RUN useradd --create-home --uid 1000 user

WORKDIR /home/user/app

# 依存は推移依存までハッシュで固定（requirements.txt は uv pip compile --generate-hashes --universal）。
# ソースからの組み立てはしない（ハッシュを持たない組み立て用の依存を入れないため）。
COPY requirements.txt ./
RUN pip install --require-hashes --only-binary=:all: -r requirements.txt

# コードと同梱データは root の持ち物のまま置き、実行する利用者は読むだけにする
COPY app.py ./
COPY mekiki_reader/ ./mekiki_reader/
COPY data/ ./data/

USER user
ENV HOME=/home/user
EXPOSE 7860
# 停止の合図。app.py は SIGTERM も受けるが、Ctrl-C と同じ扱いの SIGINT を明示しておく
STOPSIGNAL SIGINT
CMD ["python", "app.py"]

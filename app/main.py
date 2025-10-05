from fastapi import FastAPI

app = FastAPI(title="个人博客系统 API", description="基于 FastAPI 构建的博客系统后端", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "欢迎访问博客系统 API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# 也可以直接使用 uv 运行：
# uv run uvicorn app.main:app --reload

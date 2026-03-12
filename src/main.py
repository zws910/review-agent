from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from agent import CodeReviewAgent
from github_client import GitHubClient
from code_reviewer import CodeReviewer
import os
import re
from typing import List
from models import ReviewComment
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="AI Code Review Agent",
    description="使用LangGraph和OpenAI进行自动化代码审查的Agent系统",
    version="1.0.0"
)

class ReviewRequest(BaseModel):
    pr_number: int = Field(..., description="GitHub PR号码", json_schema_extra={"example": 123})

class ReviewURLRequest(BaseModel):
    pr_url: str = Field(
        ..., 
        description="GitHub PR的完整URL地址",
        json_schema_extra={"example": "https://github.com/owner/repo/pull/123"},
        pattern=r"https://github\.com/[^/]+/[^/]+/pull/\d+"
    )

class ReviewResponse(BaseModel):
    pr_id: int = Field(..., description="PR的ID号")
    pr_title: str = Field(..., description="PR的标题")
    comments: List[ReviewComment] = Field(..., description="AI审查生成的评论列表")
    total_issues: int = Field(..., description="发现的问题总数")

@app.post("/review", response_model=ReviewResponse, tags=["Code Review"])
async def review_pr(request: ReviewRequest):
    """
    通过PR号进行代码审查
    
    此端点使用PR号码进行审查，需要环境变量中已设置仓库信息。
    
    ### 环境变量要求
    - `GITHUB_TOKEN`: GitHub Personal Access Token（必需）
    - `REPO_OWNER`: 仓库所有者（必需）
    - `REPO_NAME`: 仓库名称（必需）
    - `OPENAI_API_KEY`: OpenAI API密钥（必需）
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("REPO_OWNER")
        repo_name = os.getenv("REPO_NAME")

        if not all([github_token, repo_owner, repo_name]):
            raise HTTPException(status_code=500, detail="Missing environment variables: GITHUB_TOKEN, REPO_OWNER, REPO_NAME")

        github_client = GitHubClient(github_token, repo_owner, repo_name)
        reviewer = CodeReviewer()
        agent = CodeReviewAgent(github_client, reviewer)

        comments, pr_title, pr_id = agent.review_pr(request.pr_number)

        return ReviewResponse(
            pr_id=pr_id,
            pr_title=pr_title,
            comments=comments,
            total_issues=len(comments)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/review/url", response_model=ReviewResponse, tags=["Code Review"])
async def review_pr_by_url(request: ReviewURLRequest):
    """
    通过GitHub PR URL进行AI代码审查 (推荐)
    
    此端点接受一个GitHub Pull Request的完整URL，自动提取仓库信息和PR号码，
    然后使用AI模型对PR中的代码变更进行智能审查。
    
    ### 功能特性
    - 自动解析GitHub URL，无需手动填写仓库信息
    - 支持多维度代码审查：风格、安全、性能、可维护性等
    - 使用OpenAI GPT-4进行深度代码分析
    - 返回结构化的审查意见，包括问题位置、描述和严重程度
    
    ### 环境变量要求
    - `GITHUB_TOKEN`: GitHub Personal Access Token（必需）
    - `OPENAI_API_KEY`: OpenAI API密钥（必需）
    
    ### 输入参数
    - `pr_url`: GitHub PR的完整URL，格式为 `https://github.com/{owner}/{repo}/pull/{number}`
    
    ### 返回值
    - `pr_id`: PR的编号
    - `pr_title`: PR的标题
    - `comments`: 审查意见数组，每个意见包含：
      - `file_path`: 文件路径
      - `line`: 代码行号
      - `comment`: 问题描述
      - `severity`: 严重程度（info/warning/error）
    - `total_issues`: 发现的问题总数
    
    ### 使用示例
    ```bash
    curl -X POST http://localhost:8000/review/url \\
      -H "Content-Type: application/json" \\
      -d '{"pr_url": "https://github.com/python/cpython/pull/123"}'
    ```
    
    ### 响应示例
    ```json
    {
      "pr_id": 123,
      "pr_title": "Fix memory leak in parser module",
      "total_issues": 3,
      "comments": [
        {
          "file_path": "Modules/parsermodule.c",
          "line": 256,
          "comment": "Missing NULL check before dereferencing pointer",
          "severity": "error"
        }
      ]
    }
    ```
    """
    try:
        # Parse GitHub URL
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, request.pr_url)
        
        if not match:
            raise HTTPException(status_code=400, detail="Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/number")
        
        repo_owner = match.group(1)
        repo_name = match.group(2)
        pr_number = int(match.group(3))
        
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise HTTPException(status_code=500, detail="Missing GITHUB_TOKEN environment variable")

        github_client = GitHubClient(github_token, repo_owner, repo_name)
        reviewer = CodeReviewer()
        agent = CodeReviewAgent(github_client, reviewer)

        comments, pr_title, pr_id = agent.review_pr(pr_number)

        return ReviewResponse(
            pr_id=pr_id,
            pr_title=pr_title,
            comments=comments,
            total_issues=len(comments)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["System"])
async def health_check():
    """
    健康检查端点
    
    用于检查API服务是否正常运行。
    
    ### 返回值
    - `status`: "ok" 表示服务正常
    """
    return {"status": "ok"}

if __name__ == "__main__":
    # 检查是否在GitHub Actions环境中
    if os.getenv("GITHUB_ACTIONS") or os.getenv("REPO_OWNER"):
        # GitHub Actions模式：运行命令行审查
        main()
    else:
        # 本地开发模式：启动web服务器
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class CodeChange(BaseModel):
    file_path: str
    old_code: str
    new_code: str
    line_start: int
    line_end: int

class ReviewComment(BaseModel):
    file_path: str = Field(..., description="变更文件的相对路径")
    line: int = Field(..., description="问题所在的代码行号（1-based）")
    comment: str = Field(..., description="AI生成的审查意见，包含具体的问题描述和建议")
    severity: str = Field(
        ..., 
        description="问题的严重程度",
        enum=["info", "warning", "error"]
    )

class PullRequest(BaseModel):
    id: int
    title: str
    body: str
    changes: List[CodeChange]
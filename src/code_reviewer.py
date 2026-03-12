from typing import List
from models import ReviewComment, CodeChange
from langchain_openai import ChatOpenAI
import os
import json
import re

class CodeReviewer:
    def __init__(self):
        api_key = os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise ValueError("MOONSHOT_API_KEY environment variable is not set")
        
        self.llm = ChatOpenAI(
            model="moonshot-v1-8k",
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
            temperature=0.3
        )

    def review_code_change(self, change: CodeChange) -> List[ReviewComment]:
        """
        Analyze a code change using AI and generate review comments.
        """
        try:
            # Prepare the prompt
            prompt = f"""You are an expert code reviewer. Analyze the following code change and provide specific, actionable review comments.

File: {change.file_path}

Old Code:
{change.old_code or "(new file)"}

New Code:
{change.new_code[:2000]}

Please identify issues in these categories:
1. Style & Readability (info severity)
2. Potential Bugs (warning severity)
3. Security Risks (error severity)
4. Performance Issues (warning severity)
5. Maintainability (info severity)

For each issue found, provide a JSON array with objects containing:
- "line": approximate line number (1-based)
- "comment": specific issue description
- "severity": "info", "warning", or "error"

Only return valid JSON array. Example format:
[
  {{"line": 5, "comment": "Missing error handling", "severity": "warning"}},
  {{"line": 10, "comment": "Variable name is unclear", "severity": "info"}}
]

If no issues found, return an empty array [].
"""
            
            # Call LLM
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse JSON response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if not json_match:
                return []
            
            json_str = json_match.group(0)
            review_data = json.loads(json_str)
            
            # Convert to ReviewComment objects
            comments = []
            for item in review_data:
                comment = ReviewComment(
                    file_path=change.file_path,
                    line=item.get("line", change.line_start),
                    comment=item.get("comment", ""),
                    severity=item.get("severity", "info")
                )
                comments.append(comment)
            
            return comments
            
        except Exception as e:
            print(f"Error reviewing {change.file_path}: {str(e)}")
            return []

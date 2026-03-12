from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from models import PullRequest, ReviewComment
from github_client import GitHubClient
from code_reviewer import CodeReviewer
import requests

class ReviewState(TypedDict):
    pr: PullRequest
    comments: List[ReviewComment]
    current_change_index: int

class CodeReviewAgent:
    def __init__(self, github_client: GitHubClient, reviewer: CodeReviewer):
        self.github_client = github_client
        self.reviewer = reviewer
        self.graph = self._build_graph()

    def _build_graph(self):
        def fetch_pr(state: ReviewState) -> ReviewState:
            # PR already fetched, just return
            return state

        def review_next_change(state: ReviewState) -> ReviewState:
            if state["current_change_index"] >= len(state["pr"].changes):
                return state

            change = state["pr"].changes[state["current_change_index"]]
            new_comments = self.reviewer.review_code_change(change)
            state["comments"].extend(new_comments)
            state["current_change_index"] += 1
            return state

        def should_continue_review(state: ReviewState) -> str:
            if state["current_change_index"] < len(state["pr"].changes):
                return "review_next"
            return "post_comments"

        def post_comments(state: ReviewState) -> ReviewState:
            # Post comments to GitHub
            pr_number = state["pr"].id
            
            # Get the latest commit SHA for the PR
            commit_url = f"{self.github_client.base_url}/pulls/{pr_number}"
            commit_response = requests.get(commit_url, headers=self.github_client.headers)
            if commit_response.status_code == 200:
                commit_id = commit_response.json()["head"]["sha"]
                
                for comment in state["comments"]:
                    # Post each comment
                    self.github_client.post_comment(
                        pr_number=pr_number,
                        comment=f"**{comment.severity.upper()}**: {comment.comment}",
                        commit_id=commit_id,
                        path=comment.file_path,
                        line=comment.line
                    )
            else:
                print(f"Failed to get PR commit info: {commit_response.status_code}")
            
            return state

        graph = StateGraph(ReviewState)

        graph.add_node("fetch_pr", fetch_pr)
        graph.add_node("review_next_change", review_next_change)
        graph.add_node("post_comments", post_comments)

        graph.set_entry_point("fetch_pr")
        graph.add_edge("fetch_pr", "review_next_change")
        graph.add_conditional_edges(
            "review_next_change",
            should_continue_review,
            {
                "review_next": "review_next_change",
                "post_comments": "post_comments"
            }
        )
        graph.add_edge("post_comments", END)

        return graph.compile()

    def review_pr(self, pr_number: int):
        pr = self.github_client.get_pull_request(pr_number)
        initial_state = ReviewState(
            pr=pr,
            comments=[],
            current_change_index=0
        )
        result_state = self.graph.invoke(initial_state)
        return result_state["comments"], pr.title, pr.id

    def run_review(self, pr_number: int) -> None:
        """
        运行完整的代码审查流程
        
        Args:
            pr_number: PR编号
        """
        try:
            print(f"正在获取PR #{pr_number}的数据...")
            pr = self.github_client.get_pull_request(pr_number)
            print(f"PR标题: {pr.title}")
            print(f"发现 {len(pr.changes)} 个代码变更")
            
            initial_state = ReviewState(
                pr=pr,
                comments=[],
                current_change_index=0
            )
            
            print("开始AI代码审查...")
            result_state = self.graph.invoke(initial_state)
            
            comments = result_state["comments"]
            print(f"审查完成，发现 {len(comments)} 个问题")
            
            # 打印审查结果摘要
            severity_count = {"info": 0, "warning": 0, "error": 0}
            for comment in comments:
                severity_count[comment.severity] += 1
            
            print(f"问题统计: {severity_count['error']} 个错误, {severity_count['warning']} 个警告, {severity_count['info']} 个信息")
            
        except Exception as e:
            print(f"代码审查过程中发生错误: {e}")
            raise
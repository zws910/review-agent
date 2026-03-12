# Code Review Agent

一个基于Kimi AI的自动代码审查工具。

## 功能特性

- 自动分析GitHub Pull Request中的代码变更
- 使用Kimi AI进行智能代码审查
- 生成详细的审查意见和建议
- 支持多种编程语言
- 集成GitHub Actions自动触发

## 快速开始

### 本地运行

1. 克隆仓库：
```bash
git clone <repository-url>
cd review-agent
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量：
```bash
export MOONSHOT_API_KEY="your-moonshot-api-key"
export GITHUB_TOKEN="your-github-token"
```

4. 运行代码审查：
```bash
python src/main.py <repo_owner> <repo_name> <pr_number>
```

### GitHub Actions部署

#### 1. 在目标仓库中添加workflow

在你的目标GitHub仓库中创建 `.github/workflows/ai-code-review.yml`：

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [ main, develop ]

jobs:
  code-review:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code review agent
      uses: actions/checkout@v4
      with:
        repository: 'your-username/review-agent'  # 替换为你的review-agent仓库
        path: 'review-agent'
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        cd review-agent
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: Run AI Code Review
      env:
        MOONSHOT_API_KEY: ${{ secrets.MOONSHOT_API_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        REPO_OWNER: ${{ github.repository_owner }}
        REPO_NAME: ${{ github.event.repository.name }}
        PR_NUMBER: ${{ github.event.number }}
      run: |
        cd review-agent
        python src/main.py
```

#### 2. 配置GitHub Secrets

在目标仓库的Settings > Secrets and variables > Actions中添加：

- `MOONSHOT_API_KEY`: 从[Moonshot平台](https://platform.moonshot.cn/)获取的API密钥
- `GITHUB_TOKEN`: 使用默认的 `${{ secrets.GITHUB_TOKEN }}`，它会自动提供

#### 3. 配置仓库权限

确保workflow有足够的权限。在仓库设置中：

1. 去到 Settings > Actions > General
2. 在 "Workflow permissions" 部分选择 "Read and write permissions"
3. 勾选 "Allow GitHub Actions to create and approve pull requests"

## 配置

### 环境变量

- `MOONSHOT_API_KEY`: Moonshot API密钥（必需）
- `GITHUB_TOKEN`: GitHub个人访问令牌（必需）
- `REPO_OWNER`: 目标仓库所有者（可选，从命令行参数获取）
- `REPO_NAME`: 目标仓库名称（可选，从命令行参数获取）
- `PR_NUMBER`: PR编号（可选，从命令行参数获取）

### 支持的模型

- moonshot-v1-8k (默认)
- moonshot-v1-32k
- moonshot-v1-128k
- kimi-k2-turbo-preview
- kimi-k2.5

## 工作流程

1. 当PR被创建或更新时，GitHub Actions自动触发
2. 下载代码审查工具代码
3. 安装依赖
4. 获取PR的代码变更
5. 使用Kimi AI分析代码
6. 在PR中发布审查意见

## 自定义配置

你可以修改workflow文件来自定义：

- 触发分支
- Python版本
- 使用的AI模型（修改环境变量）
- 审查规则（修改prompt）

## 故障排除

### 常见问题

1. **权限不足**: 确保workflow有写权限
2. **API密钥无效**: 检查Moonshot API密钥是否正确
3. **依赖安装失败**: 检查requirements.txt文件
4. **代码审查失败**: 检查GitHub token权限

### 日志查看

在Actions标签页查看workflow运行日志，定位问题所在。
"""
GitHub MCP 爬虫
监控 GitHub 仓库的更新（Issues, PRs, Commits, Releases）
"""

from typing import Dict, Optional, List
from loguru import logger
import requests
import os
from datetime import datetime, timedelta

from src.crawlers.base import BaseCrawler


class GitHubMCP(BaseCrawler):
    """GitHub MCP 爬虫"""
    
    def __init__(self, 
                 token: str = None,
                 timeout: int = 30, 
                 max_retries: int = 3, 
                 retry_delay: int = 2):
        """
        初始化 GitHub MCP 爬虫
        
        Args:
            token: GitHub Personal Access Token（默认从环境变量读取）
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        super().__init__(timeout, max_retries, retry_delay)
        
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            logger.warning("未配置 GITHUB_TOKEN，GitHub MCP 将使用匿名访问（有速率限制）")
        
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Intelligence-System/1.0'
        }
        
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        self.session.headers.update(headers)
    
    def crawl(self, url: str, source_name: str, **kwargs) -> Optional[Dict]:
        """
        监控 GitHub 仓库
        
        Args:
            url: GitHub 仓库 URL（如 https://github.com/owner/repo）
            source_name: 数据源名称
            **kwargs: 额外参数
                - monitor_types: 监控类型列表 ['commits', 'issues', 'pulls', 'releases']
                - since_days: 监控最近几天的更新（默认 7）
                
        Returns:
            采集结果字典
        """
        try:
            # 解析仓库信息
            repo_info = self._parse_repo_url(url)
            if not repo_info:
                logger.error(f"无效的 GitHub URL: {url}")
                return None
            
            owner = repo_info['owner']
            repo = repo_info['repo']
            
            logger.info(f"[GitHub MCP] 监控仓库: {owner}/{repo}")
            
            # 获取监控类型
            monitor_types = kwargs.get('monitor_types', ['commits', 'issues', 'pulls', 'releases'])
            since_days = kwargs.get('since_days', 7)
            since_date = datetime.now() - timedelta(days=since_days)
            
            # 收集各类更新
            content_parts = []
            content_parts.append(f"# GitHub 仓库监控: {owner}/{repo}\n")
            content_parts.append(f"监控时间: 最近 {since_days} 天\n\n")
            content_parts.append("---\n\n")
            
            # 监控 Commits
            if 'commits' in monitor_types:
                commits = self._get_commits(owner, repo, since_date)
                if commits:
                    content_parts.append(f"## 📝 最近提交 ({len(commits)} 条)\n\n")
                    for commit in commits[:10]:  # 最多显示 10 条
                        content_parts.append(f"- **{commit['date']}**: {commit['message']}\n")
                        content_parts.append(f"  作者: {commit['author']}\n")
                        content_parts.append(f"  链接: {commit['url']}\n\n")
                    content_parts.append("---\n\n")
            
            # 监控 Issues
            if 'issues' in monitor_types:
                issues = self._get_issues(owner, repo, since_date)
                if issues:
                    content_parts.append(f"## 🐛 最近 Issues ({len(issues)} 条)\n\n")
                    for issue in issues[:10]:
                        content_parts.append(f"- **#{issue['number']}**: {issue['title']}\n")
                        content_parts.append(f"  状态: {issue['state']} | 创建: {issue['created_at']}\n")
                        content_parts.append(f"  链接: {issue['url']}\n\n")
                    content_parts.append("---\n\n")
            
            # 监控 Pull Requests
            if 'pulls' in monitor_types:
                pulls = self._get_pulls(owner, repo, since_date)
                if pulls:
                    content_parts.append(f"## 🔀 最近 Pull Requests ({len(pulls)} 条)\n\n")
                    for pr in pulls[:10]:
                        content_parts.append(f"- **#{pr['number']}**: {pr['title']}\n")
                        content_parts.append(f"  状态: {pr['state']} | 创建: {pr['created_at']}\n")
                        content_parts.append(f"  链接: {pr['url']}\n\n")
                    content_parts.append("---\n\n")
            
            # 监控 Releases
            if 'releases' in monitor_types:
                releases = self._get_releases(owner, repo)
                if releases:
                    content_parts.append(f"## 🚀 最近发布 ({len(releases)} 条)\n\n")
                    for release in releases[:5]:
                        content_parts.append(f"- **{release['tag']}**: {release['name']}\n")
                        content_parts.append(f"  发布时间: {release['published_at']}\n")
                        content_parts.append(f"  链接: {release['url']}\n\n")
                    content_parts.append("---\n\n")
            
            content = ''.join(content_parts)
            
            result = {
                'source': source_name,
                'source_url': url,
                'content': content[:10000],
                'raw_html': '',
                'status_code': 200,
                'repo_info': {
                    'owner': owner,
                    'repo': repo,
                    'full_name': f"{owner}/{repo}"
                }
            }
            
            logger.info(f"[GitHub MCP] 监控成功: {owner}/{repo}")
            return result
            
        except Exception as e:
            logger.error(f"[GitHub MCP] 监控异常: {e}", exc_info=True)
            return None
    
    def _parse_repo_url(self, url: str) -> Optional[Dict]:
        """
        解析 GitHub 仓库 URL
        
        Args:
            url: GitHub URL
            
        Returns:
            仓库信息字典
        """
        # 支持多种格式
        # https://github.com/owner/repo
        # github.com/owner/repo
        # owner/repo
        
        url = url.replace('https://', '').replace('http://', '')
        url = url.replace('github.com/', '')
        
        parts = url.strip('/').split('/')
        
        if len(parts) >= 2:
            return {
                'owner': parts[0],
                'repo': parts[1]
            }
        
        return None
    
    def _get_commits(self, owner: str, repo: str, since: datetime) -> List[Dict]:
        """获取最近的提交"""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{owner}/{repo}/commits",
                params={'since': since.isoformat()},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            commits = []
            for commit in response.json():
                commits.append({
                    'sha': commit['sha'][:7],
                    'message': commit['commit']['message'].split('\n')[0],
                    'author': commit['commit']['author']['name'],
                    'date': commit['commit']['author']['date'][:10],
                    'url': commit['html_url']
                })
            
            return commits
            
        except Exception as e:
            logger.error(f"获取 commits 失败: {e}")
            return []
    
    def _get_issues(self, owner: str, repo: str, since: datetime) -> List[Dict]:
        """获取最近的 Issues"""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                params={'since': since.isoformat(), 'state': 'all'},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            issues = []
            for issue in response.json():
                # 排除 Pull Requests
                if 'pull_request' not in issue:
                    issues.append({
                        'number': issue['number'],
                        'title': issue['title'],
                        'state': issue['state'],
                        'created_at': issue['created_at'][:10],
                        'url': issue['html_url']
                    })
            
            return issues
            
        except Exception as e:
            logger.error(f"获取 issues 失败: {e}")
            return []
    
    def _get_pulls(self, owner: str, repo: str, since: datetime) -> List[Dict]:
        """获取最近的 Pull Requests"""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls",
                params={'state': 'all'},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            pulls = []
            for pr in response.json():
                created_at = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                if created_at >= since.replace(tzinfo=created_at.tzinfo):
                    pulls.append({
                        'number': pr['number'],
                        'title': pr['title'],
                        'state': pr['state'],
                        'created_at': pr['created_at'][:10],
                        'url': pr['html_url']
                    })
            
            return pulls
            
        except Exception as e:
            logger.error(f"获取 pulls 失败: {e}")
            return []
    
    def _get_releases(self, owner: str, repo: str) -> List[Dict]:
        """获取最近的 Releases"""
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{owner}/{repo}/releases",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            releases = []
            for release in response.json():
                releases.append({
                    'tag': release['tag_name'],
                    'name': release['name'] or release['tag_name'],
                    'published_at': release['published_at'][:10],
                    'url': release['html_url']
                })
            
            return releases
            
        except Exception as e:
            logger.error(f"获取 releases 失败: {e}")
            return []


# 测试代码
if __name__ == "__main__":
    # 测试 GitHub MCP
    crawler = GitHubMCP()
    
    result = crawler.crawl_with_retry(
        url="https://github.com/cabforum/servercert",
        source_name="CAB Forum Server Certificate",
        monitor_types=['commits', 'issues', 'pulls', 'releases'],
        since_days=30
    )
    
    if result:
        print(f"\nGitHub MCP 监控成功:")
        print(f"  来源: {result['source']}")
        print(f"  仓库: {result['repo_info']['full_name']}")
        print(f"  内容长度: {len(result['content'])}")
        print(f"  内容预览:\n{result['content'][:800]}...")
    else:
        print("GitHub MCP 监控失败")

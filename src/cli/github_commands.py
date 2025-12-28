"""GitHub CLI commands for workflow automation."""

import click
from src.github.workflow import GitHubWorkflow


@click.group()
def github_cli():
    """GitHub workflow automation commands."""
    pass


@github_cli.command()
@click.option('--owner', required=True, help='Repository owner')
@click.option('--repo', required=True, help='Repository name')
@click.argument('title')
@click.argument('body')
@click.option('--labels', multiple=True, help='Issue labels')
def create_issue(owner, repo, title, body, labels):
    """Create GitHub issue."""
    workflow = GitHubWorkflow(owner, repo)
    issue_number = workflow.create_issue(title, body, list(labels) if labels else None)
    click.echo(f"Created issue #{issue_number}")


@github_cli.command()
@click.option('--owner', required=True, help='Repository owner')
@click.option('--repo', required=True, help='Repository name')
@click.argument('issue_number', type=int)
@click.argument('feature_name')
@click.option('--from-branch', default='main', help='Source branch')
def create_branch(owner, repo, issue_number, feature_name, from_branch):
    """Create feature branch from issue."""
    workflow = GitHubWorkflow(owner, repo)
    branch_name = workflow.create_feature_branch(issue_number, feature_name, from_branch)
    click.echo(f"Created branch: {branch_name}")


@github_cli.command()
@click.option('--owner', required=True, help='Repository owner')
@click.option('--repo', required=True, help='Repository name')
@click.argument('branch')
@click.option('--base', default='main', help='Base branch')
@click.option('--issue', type=int, help='Issue number to link')
@click.argument('title')
@click.argument('body')
def create_pr(owner, repo, branch, base, issue, title, body):
    """Create pull request."""
    workflow = GitHubWorkflow(owner, repo)
    pr_number = workflow.create_pull_request(branch, base, title, body, issue)
    click.echo(f"Created PR #{pr_number}")


@github_cli.command()
@click.option('--owner', required=True, help='Repository owner')
@click.option('--repo', required=True, help='Repository name')
@click.argument('pr_number', type=int)
@click.option('--method', default='squash', type=click.Choice(['merge', 'squash', 'rebase']))
def merge_pr(owner, repo, pr_number, method):
    """Merge pull request."""
    workflow = GitHubWorkflow(owner, repo)
    success = workflow.merge_pull_request(pr_number, method)
    if success:
        click.echo(f"Merged PR #{pr_number}")
    else:
        click.echo(f"✗ Failed to merge PR #{pr_number}", err=True)


import git
import nonebot
from git.exc import InvalidGitRepositoryError, GitCommandError
from nonebot.utils import run_sync

from .config import Config

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config.dict())
resources_path = config.resources_path


@run_sync
def git_clone(repo_url, clone_to_path):
    repo = git.Repo.clone_from(repo_url, clone_to_path, multi_options=['--depth=1'])
    if repo:
        return True
    else:
        return False


@run_sync
def git_pull():
    try:
        repo = git.Repo(resources_path)
    except InvalidGitRepositoryError:
        return False
    origin = repo.remotes.origin
    try:
        origin.pull()
        return True
    except GitCommandError as e:
        if 'timeout' in e.stderr or 'unable to access' in e.stderr:
            return False

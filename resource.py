from git import Repo


def git_clone(repo_url, clone_to_path):
    repo = Repo.clone_from(repo_url, clone_to_path, multi_options=['--depth=1'])
    if repo:
        return True
    else:
        return False


def git_pull(repo_path):
    repo = Repo(repo_path)
    origin = repo.remotes.origin
    pull_info = origin.pull()
    for info in pull_info:
        print(f'Pulled: {info.ref.name}, Status: {info.flags}')
    if pull_info:
        return True
    else:
        return False

# import os
import logging
from pprint import pprint
import git
from git import Repo

# from typing import List, Dict
# from dataclasses import dataclass
# from types import SimpleNamespace

# from pathlib import Path

# from superconf.anchors import PathAnchor

# from paasify_v4.common import read_file, from_yaml
# from paasify_v4.core import AppNode, setup_once, requires_setup_node

logger = logging.getLogger(__name__)


# g = git.cmd.Git("/path/to/git/repo")
# print(g.execute("git remote show origin"))  # git remote show origin
# print(g.execute(["git", "remote", "show", "origin"]))  # same as above
# print(g.remote(verbose=True))  # git remote --verbose


def git_repo(path):
    "Prepare git command for a given repo"
    cmd = git.cmd.Git(path)
    return cmd


class GitRepo:
    "Git repo class"

    def __init__(self, path):
        self.path = path
        self.repo = Repo(path)
        self.cmd = git.cmd.Git(path)

    def remotes(self):
        "Get remote"
        remotes = {}
        for remote in self.repo.remotes:
            remotes[remote.name] = remote.url
        return remotes

    def remote(self, name="origin"):
        "Get remote by name, otherwise return default origin remote or None"
        remotes = self.remotes()

        if name in remotes:
            return remotes[name]
        return None

    def branch(self):
        "Get current branch"
        return self.repo.active_branch

    def is_dirty(self):
        "Check if repo is dirty"
        return self.repo.is_dirty(untracked_files=True)

    def git_status(self):
        "Get git status"
        ret = self.repo.git.status()
        # pprint(type(ret))
        # pprint(ret)
        return ret

        # if name is None:
        #     if "origin" in remotes:
        #         return remotes["origin"]
        #     else:
        #         return None

        # if name in remotes:
        #     return remotes[name]
        # return None

    # def remotes_v1(self, simple=True):
    #     "Get remote"
    #     ret = self.cmd.remote(verbose=True)
    #     pprint(type(ret))
    #     pprint(ret)
    #     return ret

    # def branches(self):
    #     "Get branches"

"""Paasify Engine management

This class helps to deal with docker engine versions
"""

# pylint: disable=logging-fstring-interpolation
# pylint: disable=invalid-name

import os
import re
import logging
import json

from distutils.version import StrictVersion

# from packaging.version import StrictVersion
from pprint import pprint

import semver

# from semver.version import Version

import sh

from cafram.utils import _exec
from cafram.nodes import NodeMap

import paasify.errors as error
from paasify.common import cast_docker_compose
from paasify.framework import PaasifyObj


log = logging.getLogger(__name__)


def bin2utf8(obj):
    "Transform sh output bin to utf-8"

    if hasattr(obj, "stdout"):
        obj.txtout = obj.stdout.decode("utf-8").rstrip("\n")
    else:
        obj.txtout = None
    if hasattr(obj, "stderr"):
        obj.txterr = obj.stderr.decode("utf-8").rstrip("\n")
    else:
        obj.txterr = None
    return obj


#####################

# https://www.docker.com/blog/announcing-compose-v2-general-availability/
# v1 vs v2
#  v2 fully support --project-name while v1 does not


class EngineCompose(NodeMap, PaasifyObj):
    "Generic docker-engine compose API"

    _node_parent_kind = ["PaasifyStack"]

    version = None
    docker_file_exists = False
    # docker_file_path = None
    arg_prefix = []

    conf_default = {
        "stack_name": None,
        "stack_path": None,
        "docker_file": "docker-compose.yml",
        # "docker_file_path": None,
    }

    ident = "default"

    compose_bin = "docker"
    # compose_pre = [
    #        "compose",
    #        "--file", "myfile.yml",
    #        "--project-name", "project-name",
    #        ]

    # compose_bin = "docker-compose"
    # compose_pre = [
    #        "--file", "myfile.yml",
    #        "--project-name", "project-name",
    #        ]

    def node_hook_init(self):
        "Create instance attributes"

        self.docker_file_path = None
        self.arg_prefix_full = []
        self.arg_prefix = []

    def node_hook_children(self):
        "Create stack context on start"

        # Get parents
        # stack = self._node_parent
        # prj = stack.prj

        # Init object
        # self.stack_name = self.stack_name
        # self.stack_path = self.stack_path
        # self.docker_file_path = self.docker_file_path or os.path.join(self.stack_path, self.docker_file)
        # pprint (self.__dict__)
        self.docker_file_path = os.path.join(self.stack_path, self.docker_file)
        # pprint (self.__dict__)

        # dsfsdf

        # Pre build args
        self.arg_prefix = [
            "compose",
            "--project-name",
            f"{self.stack_name}",
            # "--project-directory", f"{self.stack_path}",
        ]
        self.arg_prefix_full = [
            "compose",
            "--project-name",
            f"{self.stack_name}",
            "--file",
            f"{self.docker_file_path}",
        ]

    def node_hook_final(self):
        "Enable cli logging"
        self.set_logger("paasify.cli.engine")

    def run(self, cli_args=None, command=None, logger=None, **kwargs):
        "Wrapper to execute commands"

        command = command or self.compose_bin
        cli_args = cli_args or []

        # print ("RUN WRAPPER:", command, cli_args, self.log, kwargs)
        result = _exec(command, cli_args=cli_args, logger=self.log, **kwargs)
        # bin2utf8(result)

        if result:
            result = bin2utf8(result)
            log.notice(result.txtout)

        return result

    def require_stack(self):
        "Ensure stack context"

        if not self.stack_name:
            assert False, "Command not available for stacks!"

    def require_compose_file(self):
        "Raise an exception when compose file is absent"

        self.require_stack()

        if not os.path.isfile(self.docker_file_path):
            self.log.warning("Please build stack first")
            raise error.BuildStackFirstError("Docker file is not built yet !")

    def assemble(self, compose_files, env_file=None, env=None):
        "Generate docker-compose file"

        self.require_stack()

        cli_args = list(self.arg_prefix)

        if env_file:
            cli_args.extend(["--env-file", env_file])
        for file in compose_files:
            cli_args.extend(["--file", file])
        cli_args.extend(
            [
                "config",
                # "--no-interpolate",
                # "--no-normalize",
            ]
        )

        env_string = env or {}
        env_string = {
            k: cast_docker_compose(v) for k, v in env.items() if v is not None
        }

        out = self.run(cli_args=cli_args, _out=None, _env=env_string)
        return out

    # pylint: disable=invalid-name
    def up(self, **kwargs):
        "Start containers"

        self.require_compose_file()
        cli_args = self.arg_prefix_full + [
            "up",
            "--detach",
        ]
        out = self.run(cli_args=cli_args, **kwargs)
        return out

    def down(self, **kwargs):
        "Stop containers"

        self.require_stack()
        # cli_args = list(self.arg_prefix)
        cli_args = self.arg_prefix_full + [
            # "--project-name",
            # self.stack_name,
            "down",
            "--remove-orphans",
        ]

        try:
            out = self.run(cli_args=cli_args, **kwargs)
            # out = _exec("docker-compose", cli_args, **kwargs)
            # if out:
            #    bin2utf8(out)
            #    log.notice(out.txtout)

        # pylint: disable=no-member
        except sh.ErrorReturnCode_1 as err:
            bin2utf8(err)

            # This is U.G.L.Y
            if not "has active endpoints" in err.txterr:
                raise error.DockerCommandFailed(f"{err.txterr}")

        return out

    def logs(self, follow=False):
        "Return container logs"

        self.require_stack()
        sh_options = {}
        cli_args = self.arg_prefix + [
            # "--project-name",
            # self.stack_name,
            "logs",
        ]
        if follow:
            cli_args.append("-f")
            sh_options["_fg"] = True

        out = self.run(cli_args=cli_args, **sh_options)
        print(out)

    # pylint: disable=invalid-name
    def ps(self):
        "Return container processes"

        self.require_stack()

        # Prepare command
        cli_args = self.arg_prefix + [
            # "compose",
            # "--project-name",
            # self.stack_name,
            "ps",
            "--all",
            "--format",
            "json",
        ]
        result = self.run(cli_args=cli_args, _out=None)

        # Report output from json
        stdout = result.txtout
        payload = json.loads(stdout)
        for svc in payload:

            # Get and filter interesting ports
            published = svc["Publishers"] or []
            published = [x for x in published if x.get("PublishedPort") > 0]

            # Reduce duplicates
            for pub in published:
                if pub.get("URL") == "0.0.0.0":
                    pub["URL"] = "::"

            # Format port strings
            exposed = []
            for port in published:
                src_ip = port["URL"]
                src_port = port["PublishedPort"]
                dst_port = port["TargetPort"]
                prot = port["Protocol"]

                r = f"{src_ip}:{src_port}->{dst_port}/{prot}"
                exposed.append(r)

            # Remove duplicates ports and show
            exposed = list(set(exposed))
            print(
                f"  {svc['Project'] :<32} {svc['ID'][:12] :<12} {svc['Name'] :<40} {svc['Service'] :<16} {svc['State'] :<10} {', '.join(exposed)}"
            )


class EngineComposeV2(EngineCompose):
    "Docker-engine: Support for version until 2.6"

    ident = "docker compose 2"


class EngineComposeV1(EngineCompose):
    "Docker-engine: Support for version until 1.29"

    ident = "docker-compose 1"

    # pylint: disable=invalid-name
    def ps(self):
        cli_args = [
            "--file",
            self.docker_file_path,
            "ps",
            "--all",
        ]

        result = _exec("docker-compose", cli_args, _fg=True)

        return result


class EngineCompose_16(EngineCompose):
    "Docker-engine: Support for version until 1.6"

    ident = "docker-compose-1.6"


class EngineDetect:
    "Class helper to retrieve the appropriate docker-engine class"

    versions = {
        "docker": {
            "20.10.17": {},
        },
        "docker-compose": {
            "2.0.0": EngineComposeV2,
            "1.0.0": EngineComposeV1,
            # "2.6.1": EngineCompose_26,
            # "1.29.0": EngineCompose_129,
            # "1.6.3": EngineCompose_16,
        },
        "podman-compose": {},
    }

    def detect_docker_compose(self):
        "Detect current version of docker compose. Return a docker-engine class."

        # pylint: disable=no-member

        # Try docker-compose v1

        # Try docker compose v2
        out = "No output for command"
        patt = r"version v?(?P<version>(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+))"
        try:
            log.notice("This can take age when debugger is enabled...")
            out = _exec("docker", ["compose", "version"])
            # TOFIX: This takes ages in debugger, when above _log_msg is unset ?
            # out = cmd('--version')
            bin2utf8(out)
        except sh.ErrorReturnCode as err:
            # raise error.DockerUnsupportedVersion(
            #    f"Impossible to guess docker-compose version: {out}"
            # ) from err

            # pylint: disable=no-member
            try:

                # cmd = sh.Command("docker-compose", _log_msg='paasify')
                log.notice("This can take age when debugger is enabled...")
                out = _exec("docker-compose", ["--version"])
                # TOFIX: This takes ages in debugger, when above _log_msg is unset ?
                # out = cmd('--version')
                bin2utf8(out)
            except sh.ErrorReturnCode:
                raise error.DockerUnsupportedVersion(
                    f"Impossible to guess docker-compose version: {out}"
                ) from err

        # Scan version
        match = re.search(patt, out.txtout)
        if match:
            version = match.groupdict()
        else:
            msg = f"Output format of docker-compose is not recognised: {out.txtout}"
            raise error.DockerUnsupportedVersion(msg)
        curr_ver = version["version"]

        # Scan available versions
        versions = list(self.versions["docker-compose"].keys())
        versions.sort(key=StrictVersion)
        versions.reverse()
        match = None
        for version in versions:
            works = semver.match(curr_ver, f">={version}")
            if works:
                match = version
                break

        if not match:
            raise error.DockerUnsupportedVersion(
                f"Version of docker-compose is not supported: {curr_ver}"
            )

        cls = self.versions["docker-compose"][match]
        cls.version = match
        cls.name = "docker-compose"
        cls.ident = match
        return cls

    def detect(self, engine=None):
        "Return the Engine class that match engine string"

        if not engine:
            log.info("Guessing best docker engine ...")
            obj = self.detect_docker_compose()
        else:

            if engine not in self.versions["docker-compose"]:
                versions = list(self.versions["docker-compose"].keys())
                log.warning(f"Please select engine one of: {versions}")
                raise error.DockerUnsupportedVersion(
                    f"Unknown docker-engine version: {engine}"
                )
            obj = self.versions["docker-compose"][engine]
        # if not result:
        #     raise error.DockerUnsupportedVersion(f"Can;t find docker-compose")

        log.debug(f"Detected docker-compose version: {obj.version}")

        return obj

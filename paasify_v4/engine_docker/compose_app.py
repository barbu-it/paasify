# from paasify_v4.core import AppNode

from pprint import pprint
import re
import sh
from shutil import which
from types import SimpleNamespace
import logging

from clak.common import to_boolean
from mrjk_components.py_helpers.string_template import StringTemplate
from paasify_v4.common import (
    find_file_in_path,
    dict_to_env,
    write_file,
    read_file,
    from_yaml,
    to_domain,
    flatten,
)
from paasify_v4.lib.shexec import shexec

logger = logging.getLogger(__name__)


class DockerEngine:
    "DockerEngine class"

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)

    def __init__(self, docker_socket=None):

        self.docker_bin = None
        self.docker_env = {}

        self.get_docker_bin(docker_socket=docker_socket)

        # See: https://docs.docker.com/reference/cli/docker/#environment-variables
        # DOCKER_TLS
        # DOCKER_TLS_VERIFY
        # BUILDKIT_PROGRESS
        # DOCKER_CONTEXT
        # DOCKER_CONFIG
        # DOCKER_CERT_PATH
        # DOCKER_API_VERSION
        # HTTP_PROXY
        # HTTPS_PROXY
        # NO_PROXY

    def get_docker_bin(self, docker_socket=None):
        "Return the path to the docker binary"

        match_docker = which("docker") or None

        if not match_docker:
            logger.warning("Docker binary not found")

        self.docker_bin = match_docker
        self.docker_env = {}
        if docker_socket:
            self.docker_env["DOCKER_HOST"] = docker_socket

    def run_docker_cmd(self, args):
        "Run a docker command"
        assert isinstance(args, list), f"args must be a list, got {type(args)}"

        cmd = [self.docker_bin] + args
        extra_env = self.docker_env
        print("RUN DOCKER CMD", " ".join(cmd), extra_env)
        out = shexec(cmd, _env=extra_env)  # , logger=logger)
        return out

    def get_docker_version(self):
        "Return docker version"
        out = self.run_docker_cmd(["--version"])
        # return out

        std_out = out.stdout.decode("utf-8")

        rgx = r"Docker version (?P<version>\d+.\d+.\d+),?.*"
        match = re.search(rgx, std_out)
        if match:
            return match.group("version")

        raise Exception("Failed to get docker version")


class ComposeEngine(DockerEngine):
    "ComposeEngine class"

    def __init__(self, prefered_bin=None, **kwargs):

        super().__init__(**kwargs)

        # compose_cmd_prefix, is_standalone =
        self.get_compose_bin(prefered_bin)

        # Other env
        self.docker_socket = kwargs.get("docker_socket", None)

    def get_compose_bin(self, prefered_bin=None):
        "Return the path to the docker compose binary"

        compose_cmd_prefix = ["compose"]
        compose_is_standalone = False
        if prefered_bin:
            match_compose = which(prefered_bin)
            if not match_compose:
                raise Exception(f"Docker compose binary not found: {prefered_bin}")

            if "docker-compose" in prefered_bin:
                compose_is_standalone = True
                compose_cmd_prefix = []

        else:
            match_compose = self.docker_bin
            if not match_compose:
                match_compose = which("docker-compose")
                compose_is_standalone = True
                compose_cmd_prefix = []

        assert match_compose, "Docker compose binary not found"

        self.is_standalone = compose_is_standalone
        self.compose_cmd = match_compose
        self.compose_args = compose_cmd_prefix
        self.compose_cmd_prefix = [match_compose] + compose_cmd_prefix
        # self.docker_cmd_prefix = [docker_bin] if docker_bin else None

    def run_compose_cmd(self, args):
        "Run a compose command"

        assert isinstance(args, list), f"args must be a list, got {type(args)}"
        cmd = self.compose_cmd_prefix + args
        extra_env = self.docker_env
        print("RUN COMPOSE CMD", " ".join(cmd), extra_env)
        out = shexec(cmd, _env=extra_env)  # , logger=logger)
        return out

    def get_compose_version(self):
        "Return compose version"

        if self.is_standalone:
            # prefix_cmd = self.compose_cmd_prefix + ["--version"]
            prefix_cmd = ["--version"]
        else:
            # prefix_cmd = self.compose_cmd_prefix + ["version"]
            prefix_cmd = ["version"]

        out = self.run_compose_cmd(prefix_cmd)
        std_out = out.stdout.decode("utf-8")

        rgx = r"Docker Compose version v?(?P<version>\d+.\d+.\d+)"
        match = re.search(rgx, std_out)
        if match:
            return match.group("version")

        raise Exception("Failed to get compose version")


class ComposedApp:
    "ComposeApp class"

    paasify_type = "compose_app"

    def __init__(
        self, name=None, project_dir=None, compose_files=None, prefered_bin=None
    ):
        self.name = name
        self.project_dir = project_dir
        self.compose_files = compose_files or []

        # Temporary
        prefered_bin = "/home/jez/.local/bin/docker-compose"
        self.engine = ComposeEngine(
            prefered_bin=prefered_bin, docker_socket="tcp://0.0.0.0:2375"
        )

    # Core API
    # ===============

    def get_engine_infos(self):
        "Return infos about the compose engine"

        return {
            "compose_version": self.engine.get_compose_version(),
            "compose_command": self.engine.compose_cmd,
            "compose_args": self.engine.compose_args,
            "compose_standalone": self.engine.is_standalone,
            "docker_version": self.engine.get_docker_version(),
            "docker_command": self.engine.docker_bin,
        }

    def get_compose_cmd_prefix(self):
        "Return stack command prefixes"

        # Options docker compose:
        #       --all-resources              Include all resources, even those not used by services
        #       --ansi string                Control when to print ANSI control characters
        #                                    ("never"|"always"|"auto") (default "auto")
        #       --compatibility              Run compose in backward compatibility mode
        #       --dry-run                    Execute command in dry run mode
        #       --env-file stringArray       Specify an alternate environment file
        #   -f, --file stringArray           Compose configuration files
        #       --parallel int               Control max parallelism, -1 for unlimited (default -1)
        #       --profile stringArray        Specify a profile to enable
        #       --progress string            Set type of progress output (auto, tty, plain, json, quiet)
        #                                    (default "auto")
        #       --project-directory string   Specify an alternate working directory
        #                                    (default: the path of the, first specified, Compose file)
        #   -p, --project-name string        Project name

        prefix_cmd = [
            "docker",
            "compose",
            # "--project-name",
            # self.name,
            # "--project-directory",
            # self.project_dir,
        ]
        if self.name:
            prefix_cmd.extend(["--project-name", self.name])
        if self.project_dir:
            prefix_cmd.extend(["--project-directory", self.project_dir])
        prefix_cmd.extend(flatten([["--file", file] for file in self.compose_files]))
        return prefix_cmd

    # Generic helpers
    # ===============

    def get_profiles(self, interpolate=False):
        "Return list of profiles"
        cmd = self.get_compose_cmd_prefix() + ["config", "--profiles"]
        if not interpolate:
            cmd.append("--no-interpolate")
        out = shexec(cmd).stdout.decode("utf-8")  # , logger=logger)
        return out.splitlines()

    def get_volumes(self, interpolate=False):
        "Return list of volumes names"

        cmd = self.get_compose_cmd_prefix() + ["config", "--volumes"]
        if not interpolate:
            cmd.append("--no-interpolate")
        out = shexec(cmd).stdout.decode("utf-8")  # , logger=logger)
        return out.splitlines()

    def get_services(self, interpolate=False) -> list[str]:
        "Return list of services"

        cmd = self.get_compose_cmd_prefix() + ["config", "--services"]
        if not interpolate:
            cmd.append("--no-interpolate")
        out = shexec(cmd).stdout.decode("utf-8")  # , logger=logger)
        return out.splitlines()

    def get_images(self, interpolate=False) -> list[str]:
        "Return list of images"

        cmd = self.get_compose_cmd_prefix() + ["config", "--images"]
        if not interpolate:
            cmd.append("--no-interpolate")
        out = shexec(cmd).stdout.decode("utf-8")  # , logger=logger)
        return out.splitlines()

    def get_variables(self):
        "Return list of variables"

        cmd = self.get_compose_cmd_prefix() + ["config", "--variables"]
        out = shexec(cmd).stdout.decode("utf-8")  # , logger=logger)
        payload = out.splitlines()[1:]

        ret = {}
        for line in payload:
            data = line.split()
            ret[data[0]] = SimpleNamespace(
                # name=data[0],
                required=to_boolean(data[1]) if len(data) > 1 else None,
                # default=data[2] if len(data) > 2 else None,
                # alternate=data[3] if len(data) > 3 else None,
            )
        return ret

    def get_variables2(self):
        "Return list of variables, alternative to get_variables with StringTemplate"

        cmd = self.get_compose_cmd_prefix() + [
            "config",
            "--no-interpolate",
            "--no-path-resolution",
        ]
        out = shexec(cmd).stdout.decode("utf-8")  # , logger=logger)
        varnames = StringTemplate(out).get_identifiers()
        return varnames

    # Stack assembling
    # ===============

    def assemble(
        self,
        profiles="*",
        dry_run=False,
        normalize=False,
        interpolate=False,
        path_resolution=False,
        output="yaml",
    ):
        "Assemble docker compose config"

        cmd = self.get_compose_cmd_prefix()

        if not isinstance(profiles, list):
            profiles = [profiles]
        if profiles:
            cmd.append("--profile")
            cmd.append(",".join(profiles))
            # cmd.append("'%s'" % ",".join(profiles))

        cmd.extend(["config", "--format", output])

        # Add options
        if interpolate is False:
            cmd.append("--no-interpolate")
        if path_resolution is False:
            cmd.append("--no-path-resolution")
        if normalize is False:
            cmd.append("--no-normalize")
        if dry_run is True:
            cmd.append("--dry-run")

        # Run assembling
        out = shexec(cmd)
        std_out = out.stdout.decode("utf-8")
        std_err = out.stderr.decode("utf-8")
        if std_err:
            logger.warning("Warnings while running command:\n%s", std_err)

        return std_out

    # Options docker compose config:
    #       --dry-run                 Execute command in dry run mode
    #       --environment             Print environment used for interpolation.
    #       --format string           Format the output. Values: [yaml | json] (default "yaml")
    #       --hash string             Print the service config hash, one per line.
    #       --images                  Print the image names, one per line.
    #       --no-consistency          Don't check model consistency - warning: may produce invalid
    #                                 Compose output
    #       --no-interpolate          Don't interpolate environment variables
    #       --no-normalize            Don't normalize compose model
    #       --no-path-resolution      Don't resolve file paths
    #   -o, --output string           Save to file (default to stdout)
    #       --profiles                Print the profile names, one per line.
    #   -q, --quiet                   Only validate the configuration, don't print anything
    #       --resolve-image-digests   Pin image tags to digests
    #       --services                Print the service names, one per line.
    #       --variables               Print model variables and default values.
    #       --volumes                 Print the volume names, one per line.

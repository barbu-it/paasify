"""
Paasify errors
"""


class PaasifyError(Exception):
    """Base class for other exceptions"""

    paasify = True
    rc = 1

    def __init__(self, message, rc=None, advice=None):
        # self.paasify = True
        self.advice = advice

        # pylint: disable=invalid-name
        self.rc = rc or self.rc
        super().__init__(message)


class ProjectNotFound(PaasifyError):
    """Raised when project is not found"""

    rc = 17


class ProjectInvalidConfig(PaasifyError):
    """Raised when project config contains errors"""

    rc = 18


class ShellCommandFailed(PaasifyError):
    """Raised when project config contains errors"""

    rc = 18


class StackNotFound(PaasifyError):
    """Raised when stack is not found"""

    rc = 19


class StackMissingOrigin(PaasifyError):
    """Raised when a stack origin is not determined"""

    rc = 20


class DockerBuildConfig(PaasifyError):
    "Raised when docker-config failed"
    rc = 30


class DockerCommandFailed(PaasifyError):
    "Raised when docker-config failed"
    rc = 32


class JsonnetBuildFailed(PaasifyError):
    "Raised when jsonnet failed"
    rc = 31


class DockerUnsupportedVersion(PaasifyError):
    "Raised when docker-config failed"
    rc = 33


class JsonnetProcessError(PaasifyError):
    "Raised when jsonnet file can't be executed"
    rc = 34


class InvalidConfig(PaasifyError):
    "Raised when invalid syntax for config"
    rc = 36


class PaasifyNestedProject(PaasifyError):
    "Raised when a project is created into an existing project"
    rc = 35


class StackMissingDockerComposeFile(PaasifyError):
    """Raised when a stack can't find a docker-compose.yml"""

    rc = 38


class BuildStackFirstError(PaasifyError):
    """Raised when a trying to interact with stack but docker-compose.yml is missing"""

    rc = 39


class OnlyOneStackAllowed(PaasifyError):
    """Raised when trying to apply command one more than one stack"""

    rc = 41


class YAMLError(PaasifyError):
    """Raised when having issues with YAML file"""

    rc = 42


class MissingTag(PaasifyError):
    """Raised when referencing unexistant tag"""

    rc = 43


class MissingApp(PaasifyError):
    """Raised when referencing unknown app"""

    rc = 44


class ConfigBackendError(PaasifyError):
    """Raised when could not work with cafram"""

    rc = 45


class InvalidSourceConfig(PaasifyError):
    """Raised when a source is not configured properly"""

    rc = 46

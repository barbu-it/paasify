from paasify_v4.exceptions import PaasifyEngineError


class DockerBackendAbsent(PaasifyEngineError):
    "Raised when can't connect to socket"

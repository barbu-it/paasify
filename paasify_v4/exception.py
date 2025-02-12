class PaasifyError(Exception):
    "Base class for all Paasify errors"


class PaasifyWorkdirNotFoundError(PaasifyError):
    "Error when a workdir is not found"


class PaasifyConfigError(PaasifyError):
    "Error when a config is invalid"

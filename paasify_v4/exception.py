class PaasifyError(Exception):
    "Base class for all Paasify errors"


class PaasifyWorkdirNotFoundError(PaasifyError):
    "Error when a workdir is not found"

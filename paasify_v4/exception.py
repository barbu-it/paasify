class PaasifyError(Exception):
    "Argument error"

    rc = 99
    advice = None
    message = None

    def __init__(self, message=None, **kwargs):
        self.message = message
        self.meta = kwargs
        super().__init__(message)

    def __getattr__(self, key):
        return self.meta.get(key, None)


# Top level classes
# ==============================


class PaasifyEngineError(PaasifyError):
    "Error with engine"


class PaasifyAssembleError(PaasifyError):
    "Error with assembling"


class PaasifyCliError(PaasifyError):
    "Error with CLI"


class PaasifyCatalogError(PaasifyError):
    "Error with catalog"


class PaasifyPodError(PaasifyError):
    "Error with pod"


class PaasifyStackError(PaasifyError):
    "Error with stack"


class PaasifyNamespaceError(PaasifyError):
    "Error with namespace"


# User errors
# ==============================


class PaasifyWorkdirNotFoundError(PaasifyError):
    "Error when a workdir is not found"


class PaasifyConfigError(PaasifyError):
    "Error when a config is invalid"


class PaasifySetupError(PaasifyError):
    "Error when a setup is invalid"


class PaasifyAppNotFoundError(PaasifyError):
    "Error when an app is not found"


class PaasifyPodNotFoundError(PaasifyError):
    "Error when a pod is not found"

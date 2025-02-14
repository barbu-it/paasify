"Main paasify app class"

import logging
from pprint import pprint
import os

import paasify_v4.exception as exc
from paasify_v4.core_catalog import PaasifyCatalog
from paasify_v4.core_namespace import PaasifyNamespace
from paasify_v4.core_stack import PaasifyStack


logger = logging.getLogger(__name__)


class PaasifyRunner:
    "Main runner class"

    def __init__(self, path=None, start_path=None, collections_paths=None):

        self.req_path = path
        self.start_path = start_path or os.getcwd()

        # Fetch catalog
        self._catalog = PaasifyCatalog(collections_paths=collections_paths)

    @property
    def catalog(self):
        "Return catalog"
        return self._catalog

    @property
    def stack(self):
        "Return stack"

        try:
            namespace = self.namespace
        except exc.PaasifyWorkdirNotFoundError:
            namespace = None

        return PaasifyStack(
            path=self.req_path or self.start_path,
            search_up=bool(self.start_path),
            catalog=self.catalog,
            namespace=namespace,
        )

    @property
    def namespace(self):
        "Return namespace"
        return PaasifyNamespace(
            path=self.req_path or self.start_path,
            search_up=bool(self.start_path),
            catalog=self.catalog,
        )

    @property
    def pod(self):
        "Return pod"

        stack = self.stack
        if stack.sub_path:
            return stack[stack.sub_path]

        logger.warning("You are not in a pod directory, go into a pod subdirectory to activate")
        raise exc.PaasifyWorkdirNotFoundError(f"Can't find current pod in: {stack}")


    @property
    def current(self):
        "Return current item"

        attrs = ["pod", "stack", "namespace"]
        errors = []
        for attr in attrs:
            try:
                item = getattr(self, attr)
                if item:
                    return item
            except exc.PaasifyWorkdirNotFoundError as err:
                errors.append(err)

        errors = "\n  - ".join([str(x) for x in errors])
        raise exc.PaasifyWorkdirNotFoundError(f"Can't find current item in: {errors}")

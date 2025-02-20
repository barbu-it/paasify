"Main paasify app class"

import logging
from pprint import pprint
import os

import paasify_v4.exception as exc
from paasify_v4.models.core_catalog import PaasifyCatalog
from paasify_v4.models.core_namespace import PaasifyNamespace
from paasify_v4.models.core_stack import PaasifyStack


logger = logging.getLogger(__name__)


class PaasifyRunner:
    "Main runner class"

    def __init__(self, path=None, start_path=None, collections_paths=None):

        self.req_path = path
        self.start_path = start_path or os.getcwd()

        # Fetch catalog
        self._catalog = PaasifyCatalog(collections_paths=collections_paths)
        self._namespace = None
        self._stack = None
        self._pod = None

    @property
    def catalog(self):
        "Return catalog"
        return self._catalog

    @property
    def namespace(self):
        "Return namespace"
        if self._namespace is None:
            self._namespace = PaasifyNamespace(
                path=self.req_path or self.start_path,
                search_up=bool(self.start_path),
                catalog=self.catalog,
            )
        return self._namespace

    @property
    def stack(self):
        "Return stack"

        try:
            namespace = self.namespace
        except exc.PaasifyWorkdirNotFoundError:
            namespace = None

        if self._stack is None:
            self._stack = PaasifyStack(
                path=self.req_path or self.start_path,
                search_up=bool(self.start_path),
                catalog=self.catalog,
                parent=namespace,
            )
        return self._stack

    @property
    def pod(self):
        "Return pod"

        stack = self.stack
        if not stack.sub_path:
            raise exc.PaasifyWorkdirNotFoundError(f"Can't find current pod in: {stack}")

        if self._pod is None:
            self._pod = stack[stack.sub_path]
        return self._pod

        # logger.warning("You are not in a pod directory, go into a pod subdirectory to activate")

    def get_current(self):
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

"Main paasify app class"

import logging
from pprint import pprint
import os
from paasify_v4.core_catalog_cli import AppGroup, CollectionGroup

from paasify_v4.common import truncate, to_yaml
import paasify_v4.exception as exc

from paasify_v4.core_catalog import PaasifyCatalog
from paasify_v4.core_namespace import PaasifyNamespace
from paasify_v4.core_stack import PaasifyStack


logger = logging.getLogger(__name__)


class PaasifyRunner:
    "Main runner class"

    def __init__(self, start_path=None, collections_paths=None):

        self.start_path = start_path or os.getcwd()

        # Fetch catalog
        self.collections_paths = collections_paths
        self.catalog = PaasifyCatalog(collections_paths=collections_paths)

    def get(self, path=None):
        "Return closest item from path"

        path = path or self.start_path
        search_up = True

        stack = None
        ns = None
        errors = []
        try:
            stack = PaasifyStack(path=path, search_up=search_up, catalog=self.catalog)
        except exc.PaasifyWorkdirNotFoundError as err:
            errors.append(err)

        try:
            ns = PaasifyNamespace(path=path, search_up=search_up, catalog=self.catalog)
        except exc.PaasifyWorkdirNotFoundError as err:
            errors.append(err)

        if not stack and not ns:
            # assert False, "No item found"
            errors = "\n  - ".join([str(x) for x in errors])
            raise exc.PaasifyWorkdirNotFoundError(errors)

        ret = None
        if stack:
            # Return stack context with attached namespace
            stack.ns = ns
            ret = stack

            # Directory return app/pod if in stack subpath
            if stack.sub_path:
                logger.info("%s detected, looking for app %s", stack, stack.sub_path)
                # print("SUB PATH:", out.sub_path)
                ret = stack[stack.sub_path]
        elif ns:
            # Return namespace context
            ret = ns

        return ret

    # def find_closest_workdir(self, path=None, search_up=True, kind=None):
    #     "Find the closest workdir"

    #     # Prepare args
    #     items = kind or [
    #         PaasifyStack,
    #         PaasifyNamespace,
    #     ]
    #     items = [items] if not isinstance(items, list) else items
    #     if not path:
    #         path = os.getcwd()
    #     items_names = " or ".join([getattr(x, "__name__", str(x)) for x in items])

    #     # Loop over first match
    #     logger.debug("Searching for %s in path: %s", items_names, path)
    #     errors = []
    #     for item in items:
    #         assert isinstance(item, type), f"Item must be a type, not {type(item)}"
    #         try:
    #             out = item(path=path, search_up=search_up)
    #             logger.info("Found item: %s in %s", out, ~out.path)

    #             if item is PaasifyStack:

    #                 try:
    #                     out.ns = PaasifyNamespace(path=path, search_up=search_up)
    #                 except exc.PaasifyWorkdirNotFoundError:
    #                     pass

    #                 if out.sub_path:
    #                     logger.info("%s detected, looking for app %s", item, out.sub_path)
    #                     # print("SUB PATH:", out.sub_path)
    #                     out = out[out.sub_path]
    #                 # assert False, "WIP"

    #             return out
    #         except exc.PaasifyWorkdirNotFoundError as err:
    #             logger.debug("Can't find %s in path '%s': %s", item.__name__, path, err)
    #             errors.append(err)

    #     # msg = f"Can't find any {items_names} in path: {last_error}"
    #     errors = "\n  - ".join([str(x) for x in errors])
    #     search = "in parent directories" if search_up else "in paths"
    #     errors = f"Can't find any {items_names} {search}:\n  - {errors}"
    #     raise exc.PaasifyWorkdirNotFoundError(errors)

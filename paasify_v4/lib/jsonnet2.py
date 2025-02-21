import json
import logging
import os
from pprint import pformat, pprint  # noqa: F401
from types import SimpleNamespace

import _jsonnet

logger = logging.getLogger(__name__)
_logger = logger


class JsonnetError(Exception):
    "Jsonnet error"


class JsonnetBuildFailed(JsonnetError):
    "Jsonnet build failed"


def try_path(dir_, rel):
    "Helper function to load a jsonnet file into memory for _jsonnet"

    if not rel:
        return None, None
        # raise RuntimeError("Got invalid filename (empty string).")

    if rel[0] == "/":
        full_path = rel
    else:
        full_path = os.path.join(dir_, rel)

    if full_path[-1] == "/":
        return None, None
        # raise RuntimeError("Attempted to import a directory")

    if not os.path.isfile(full_path):
        return full_path, None
    with open(
        full_path,
        encoding="utf-8",
    ) as file_:
        return full_path, file_.read()


class JsonnetProcessor:
    def __init__(self):
        "Init jsonnet processor"
        # logger = _logger or logger

        # print("INIT Jsonnet Porcessor")

    def process_jsonnet_exec(self, file, action, data, import_dirs=None):
        "Process jsonnet file"

        # Developper init
        import_dirs = import_dirs or []
        data = data or {}
        assert isinstance(data, dict), f"Data must be dict, got: {data}"
        # assert len(import_dirs) > 2, f"Missing import dirs, got: {import_dirs}"

        # TODO: Enforce jsonnet API
        # assert action in [
        #     "metadata",
        #     "vars_default",
        #     "vars_override",
        #     "process_globals", # Testing WIP
        #     "process_transform", # Testing WIPP
        #     "docker_override",
        # ], f"Action not supported: {action}"

        # Prepare input variables
        mod_ident = os.path.splitext(os.path.basename(file))[0]
        ext_vars = {
            "parent": json.dumps(mod_ident),
            "action": json.dumps(action),
        }
        for key, val in data.items():
            # print("SERIALIZE")
            # pprint(val)
            ext_vars[key] = json.dumps(val)

        # Jsonnet import callback
        def import_callback(dir_, rel):
            "Helper function to load a jsonnet libraries in lookup paths"

            test_dirs = [dir_] + import_dirs
            for test_dir in test_dirs:
                full_path, content = try_path(test_dir, rel)
                logger.info("Load '%s' jsonnet from: %s", rel, full_path)
                if content:
                    return full_path, content.encode()

            test_dirs = " ".join(test_dirs)
            raise RuntimeError(
                f"Jsonnet file not found '{rel}' in any of these paths: {test_dirs}"
            )

        # Process jsonnet tag
        logger.info("Process jsonnet: %s (action=%s)", file, action)
        try:
            # result = SimpleNamespace(
            #     file=file,
            #     ext_vars=ext_vars,
            #     import_callback=import_callback,
            # )
            # pprint(result)
            # pylint: disable=c-extension-no-member
            result = _jsonnet.evaluate_file(
                file,
                ext_vars=ext_vars,
                import_callback=import_callback,
            )
        except RuntimeError as err:
            # logger.critical(f"Can't parse jsonnet file: {file}")
            raise JsonnetBuildFailed(err) from None

        # Return python object from json output
        result = json.loads(result)
        return result

    # def process_jsonnet_exec(self, file, action, data, import_dirs=None):
    #     "Process jsonnet file"

    #     # Developper init
    #     import_dirs = import_dirs or []
    #     data = data or {}
    #     assert isinstance(data, dict), f"Data must be dict, got: {data}"
    #     # assert len(import_dirs) > 2, f"Missing import dirs, got: {import_dirs}"

    #     # TODO: Enforce jsonnet API
    #     # assert action in [
    #     #     "metadata",
    #     #     "vars_default",
    #     #     "vars_override",
    #     #     "process_globals", # Testing WIP
    #     #     "process_transform", # Testing WIPP
    #     #     "docker_override",
    #     # ], f"Action not supported: {action}"

    #     # Prepare input variables
    #     mod_ident = os.path.splitext(os.path.basename(file))[0]
    #     ext_vars = {
    #         "parent": json.dumps(mod_ident),
    #         "action": json.dumps(action),
    #     }
    #     for key, val in data.items():
    #         ext_vars[key] = json.dumps(val)

    #     def try_path(dir_, rel):
    #         "Helper function to load a jsonnet file into memory for _jsonnet"

    #         if not rel:
    #             return None, None
    #             # raise RuntimeError("Got invalid filename (empty string).")

    #         if rel[0] == "/":
    #             full_path = rel
    #         else:
    #             full_path = os.path.join(dir_, rel)

    #         if full_path[-1] == "/":
    #             return None, None
    #             # raise RuntimeError("Attempted to import a directory")

    #         if not os.path.isfile(full_path):
    #             return full_path, None
    #         with open(
    #             full_path,
    #             encoding="utf-8",
    #         ) as file_:
    #             return full_path, file_.read()

    #     # Jsonnet import callback
    #     def import_callback(dir_, rel):
    #         "Helper function to load a jsonnet libraries in lookup paths"

    #         test_dirs = [dir_] + import_dirs
    #         for test_dir in test_dirs:
    #             full_path, content = try_path(test_dir, rel)
    #             logger.trace(f"Load '{rel}' jsonnet from: {full_path}")
    #             if content:
    #                 return full_path, content.encode()

    #         test_dirs = " ".join(test_dirs)
    #         raise RuntimeError(
    #             f"Jsonnet file not found '{rel}' in any of these paths: {test_dirs}"
    #         )

    #     # Process jsonnet tag
    #     logger.trace(f"Process jsonnet: {file} (action={action})")
    #     try:
    #         # pylint: disable=c-extension-no-member
    #         result = _jsonnet.evaluate_file(
    #             file,
    #             ext_vars=ext_vars,
    #             import_callback=import_callback,
    #         )
    #     except RuntimeError as err:
    #         logger.critical(f"Can't parse jsonnet file: {file}")
    #         raise error.JsonnetBuildFailed(err)

    #     # Return python object from json output
    #     result = json.loads(result)
    #     return result

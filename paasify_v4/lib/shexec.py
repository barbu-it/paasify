import logging

import sh

_logger = logging.getLogger(__name__)


def custom_log(ran, call_args, pid=None):
    # assert False
    return f"{ran}"


def shexec(command, logger=None, **kwargs):
    "Execute any command"

    # Check arguments
    # cli_args = cli_args or []
    # assert isinstance(cli_args, list), f"_exec require a list, not: {type(cli_args)}"

    # logger.info("SHEXEC: %s", command)

    logger = logger or _logger

    # Prepare context
    sh_opts = {
        # "_in": sys.stdin,
        # "_out": sys.stdout,
    }
    sh_opts = kwargs or sh_opts

    # Bake command
    cmd_name = command[0]
    cmd_args = command[1:]
    cmd = sh.Command(cmd_name)
    cmd = cmd.bake(*cmd_args)

    # Log command
    if logger:
        cmd_line = [f"{key}='{val}'" for key, val in sh_opts.get("_env", {}).items()]
        # pylint: disable=protected-access
        cmd_line = (
            cmd_line
            + [cmd.__name__]
            + [x.decode("utf-8") for x in cmd._partial_baked_args]
        )
        cmd_line = " ".join(cmd_line)
        logger.info(cmd_line)  # Support exec level !!!

    # Execute command via sh
    try:
        output = cmd(_log_msg=custom_log, **sh_opts)
        return output

    except sh.ErrorReturnCode as err:
        logger.error(f"Error while running command: {' '.join(command)}")
        # log.critical (f"Command failed with message:\n{err.stderr.decode('utf-8')}")

        # pprint (err.__dict__)
        # raise error.ShellCommandFailed(err)
        # sys.exit(1)
        raise err

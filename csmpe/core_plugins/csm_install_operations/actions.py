"""This is a module providing FSM actions for Install Operations plugins."""


def a_error(plugin_ctx, ctx):
    """Display the error message."""
    message = ctx.ctrl.after.strip().splitlines()[-1]
    plugin_ctx.error(message)
    return False

import re

def format_tuple(name, args):
    if len(args) == 1:
        args[0] = filter_sensitive(args[0])
        return f"{name}({args[0]})"

    args = tuple(filter_sensitive(arg) for arg in args)
    return f"{name}{args}"

def filter_sensitive(arg):
    return re.sub(r"(\?[^\s]+)"," ",str(arg))

def format_exception(e):
    return format_tuple(e.__class__.__name__, e.args)


def err_msg(msg, e):
    return f"Error: {msg} -- {format_exception(e)}"

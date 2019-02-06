def format_tuple(name, args):
    if len(args) == 1:
        return f"{name}({args[0]})"
    return f"{name}{args}"

def format_exception(e):
    return format_tuple(e.__class__.__name__, e.args)

def err_msg(msg, e):
    return f"Error: {msg} -- {format_exception(e)}"
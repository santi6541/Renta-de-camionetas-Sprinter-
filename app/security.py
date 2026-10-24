from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    def decorate(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.rol not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorate

import functools

from django.contrib import messages
from django.shortcuts import redirect

from common.db import db_cursor
from .session import get_user_from_session


def login_required_custom(role=None):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id, user_role = get_user_from_session(request)
            if not user_id:
                return redirect('login')
            if role and user_role != role:
                return redirect('login')
            if user_role == 'doctor':
                with db_cursor() as cur:
                    cur.execute(
                        'SELECT is_active FROM "USER" WHERE user_id = %s',
                        (user_id,),
                    )
                    row = cur.fetchone()
                if row and not row[0]:
                    request.session.flush()
                    messages.error(
                        request,
                        'Your doctor account is inactive. Please contact a clinic admin.',
                    )
                    return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

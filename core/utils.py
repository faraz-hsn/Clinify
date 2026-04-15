import functools
from django.shortcuts import redirect


def get_user_from_session(request):
    return request.session.get('user_id'), request.session.get('user_role')


def login_required_custom(role=None):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id, user_role = get_user_from_session(request)
            if not user_id:
                return redirect('login')
            if role and user_role != role:
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

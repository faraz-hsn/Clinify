def get_user_from_session(request):
    return request.session.get('user_id'), request.session.get('user_role')

import zoneinfo

from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = request.COOKIES.get('tz')
        if tz:
            try:
                timezone.activate(zoneinfo.ZoneInfo(tz))
            except (zoneinfo.ZoneInfoNotFoundError, ValueError):
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)

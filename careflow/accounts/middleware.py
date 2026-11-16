from datetime import timedelta
from django.conf import settings
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import F
from django.shortcuts import render
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.cache import add_never_cache_headers
from .models import RequestBucket


def take_bucket(scope, value, limit):
    now = timezone.now()
    window = int(now.timestamp()) // 900
    key = salted_hmac("careflow-account-rate", f"{scope}:{window}:{value}").hexdigest()
    with transaction.atomic():
        RequestBucket.objects.filter(expires_at__lt=now).delete()
        bucket, _ = RequestBucket.objects.get_or_create(
            key=key, defaults={"expires_at": now + timedelta(minutes=30)})
        updated = RequestBucket.objects.filter(pk=key, count__lt=limit).update(count=F("count") + 1)
    return bool(updated)


class AccountSafety:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        account_page = request.path_info.startswith("/accounts/")
        login = request.path_info in ("/login/", "/portal/login/")
        if request.method == "POST" and (account_page or login):
            # Do not trust arbitrary client-supplied proxy headers.
            ip = request.META.get("REMOTE_ADDR", "unknown")
            value = request.POST.get("username", "").strip().lower()[:254]
            try:
                limited = not take_bucket("auth-ip", ip, settings.CAREFLOW_AUTH_IP_LIMIT)
                if value:
                    limited = limited or not take_bucket("auth-identity", value, settings.CAREFLOW_AUTH_IDENTITY_LIMIT)
            except (OperationalError, IntegrityError):
                return render(request, "accounts/unavailable.html", status=503)
            if limited:
                response = render(request, "accounts/limited.html", status=429)
                response["Retry-After"] = "900"
                add_never_cache_headers(response)
                return response
        response = self.get_response(request)
        if account_page or login:
            add_never_cache_headers(response)
            response["Referrer-Policy"] = "same-origin"
        return response

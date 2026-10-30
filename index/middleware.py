from datetime import timedelta

from django.utils import timezone

from .models import UserActivity


class OnlineUsersMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        if request.user.is_authenticated:

            now = timezone.now()
            cutoff = now - timedelta(minutes=1)

            updated = UserActivity.objects.filter(
                user_id=request.user.pk,
                last_seen__lt=cutoff
            ).update(last_seen=now)

            if not updated:
                exists = UserActivity.objects.filter(
                    user_id=request.user.pk
                ).exists()

                if not exists:
                    UserActivity.objects.create(
                        user=request.user,
                        last_seen=now
                    )

        return response
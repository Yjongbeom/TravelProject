from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from chat.views import UserGetAndCreateView
from django.http import HttpResponse


def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('chat/', include('chat.urls')),
    path('users/', UserGetAndCreateView.as_view()),
    path('', health_check),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

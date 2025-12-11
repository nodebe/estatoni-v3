from django.urls import path, include
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView


urlpatterns = [
    path("auth/", include("account.v1.urls.auth")),
    path("profile/", include("account.v1.urls.profile")),
    path("roles/", include("roles_permissions.urls")),
    path("users/", include("account.v1.urls.user")),
    # path("crm/", include("crm.v1.urls.crm")),
    path("media/", include("media.urls")),
    path("location/", include("location.v1.urls")),
    path('doc/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('doc/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls')),

    # Swagger API Schema Engine paths
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # This renders the actual interactive web dashboard page
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
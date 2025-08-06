"""
URL configuration for web_transformation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _

# Change the header of the admin panel.
admin.site.site_title = "EnhanceX site admin (DEV)"
admin.site.site_header = 'EnhanceX Admin Panel'
admin.site.index_title = 'EnhanceX '

urlpatterns = i18n_patterns(
    path("secretadmin/", admin.site.urls),
    path('', include('Fit4.urls')),
    #path('ckeditor/', include('ckeditor_uploader.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    #path('', include('account.urls')),
    path('', include(('account.urls', 'account'), namespace='account')),
    path(_('reports/'), include('reports.urls')), # Including reports app

    # Charts
    path('', include('dashboard.urls')),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
    path('api/accounts/', include('account.api_urls')),
    path('pdfconverter/', include('pdf2pptxsite.urls')),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
	

handler500 = 'Fit4.views.custom_server_error'
handler404 = 'Fit4.views.custom_404_view'
handler403 = 'Fit4.views.custom_403_view'
handler400 = 'Fit4.views.custom_400_view'
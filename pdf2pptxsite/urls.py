from django.urls import path
from . import views

app_name = 'pdf2pptxsite'

urlpatterns = [
    path("convert", views.index, name="convert_to_pptx"),
    path("convert/", views.ajax_convert, name="ajax_convert"),
]
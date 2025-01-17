from django.urls import path, include
from . import views
urlpatterns = [
    path("crear",views.create),
    path("editar/<int:id>",views.update),
    path("eliminar/<int:id>",views.destroy)
]

from django.urls import path,re_path
from . import views


urlpatterns = [
    path('', views.index,),
    path('filtro', views.filter),
    path('guardar',views.create),
    path('chat/<int:id>',views.chat),
    path('notification',views.notification),
    path('eliminar/<int:id>',views.destroy),
    path('eliminar/chat/<int:id>',views.delete)
]



from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path("admin/", admin.site.urls,),

    path('api/', include([
    path("login/",views.login,name="login"),
    path("getToken/<int:id>",views.getTokenByUserId),
    path('register/', views.register, name="register"),
    path("users/", include("users.urls")),
    path("chats/", include("chats.urls")),
    path("messages/", include("message.urls"))
 ])),
]
                             

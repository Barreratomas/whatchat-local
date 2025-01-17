from django.urls import path, include
from . import views


urlpatterns = [
    path("",views.index),
    path("me",views.me,name="me"),
    path("actualizar",views.update),
    path("guardar",views.store),
    path("eliminar/<int:id>",views.destroy),
    path("solicitud/",include([
        path("enviar",views.send_friend_request),
        path("aceptar/<int:id>",views.accept_friend_request),
        path("rechazar/<int:id>",views.reject_friend_request),
        path("pendiente/",views.view_pending_requests),
    ])),
    path("amigos/",views.view_friends),
    path("amigos/eliminar",views.remove_friend),
    path("amigos/bloquear",views.block_friend),
    path("amigos/desbloquear",views.unblock_friend),




]








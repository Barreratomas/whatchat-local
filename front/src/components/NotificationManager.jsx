import { useEffect } from "react";

// Función que solicita permiso para notificaciones
const requestNotificationPermission = () => {
  if (Notification.permission === "default") {
    Notification.requestPermission()
      .then((permission) => {
        console.log("Permiso de notificación:", permission);
      })
      .catch((err) => {
        console.error("Error al solicitar permiso para notificaciones:", err);
      });
  }
};

// Función para mostrar una notificación
const showNotification = (notification, activeChatId) => {
  if (Notification.permission === "granted" && notification?.data) {
    if (notification.data.chat_id !== activeChatId) {
      new Notification(
        `${notification.data.other_user.username}`,
        {
          body: notification.data.last_message.content,
          icon: "/path-to-your-icon.png",
        }
      );
    }
  }
};

export const NotificationManager = ({
  notification,
  activeChatId,
  onNotificationHandled,
}) => {
  useEffect(() => {
    // Solicitar permiso para notificaciones
    requestNotificationPermission();

    // Mostrar la notificación solo si no están en el mismo chat
    if (notification && notification.data && notification.data.chat_id !== activeChatId) {
      showNotification(notification, activeChatId);

      // Llamar a la función de reinicio en el Layout
      if (onNotificationHandled) {
        onNotificationHandled();
      }
    }
  }, [notification, activeChatId, onNotificationHandled]);

  return null; // Este componente no necesita renderizar nada
};

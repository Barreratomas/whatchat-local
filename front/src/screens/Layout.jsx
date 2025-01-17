import React, { useEffect, useState, useRef } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom"; // Importa useLocation
import "../styles/layout.css";
import { useServerStatus } from "../components/ServerStatusProvider";
import { useNotification } from "../components/Notification";
import { NotificationManager } from "../components/NotificationManager";
import Modal from "../components/modal";

export const UserContext = React.createContext(null);

const Layout = () => {
  const location = useLocation();

  const navigate = useNavigate();
  const { checkServerStatus, user, error } = useServerStatus();
  const { addNotification } = useNotification();

  const chatsSocketRef = useRef(null);
  const [filteredChats, setFilteredChats] = useState([]);
  const [chats, setChats] = useState([]);

  const [usernameFilter, setUsernameFilter] = useState("");
  const [isFiltering, setIsFiltering] = useState(false);

  const [showModal, setShowModal] = useState(false);

  const [hasCheckedUser, setHasCheckedUser] = useState(false);

  const contextMenuRef = useRef(null);

  const [contextMenu, setContextMenu] = useState(null);
  const [selectedChat, setSelectedChat] = useState(null);

  const [notification, setNotification] = useState(null);
  const [notificationReceived, setNotificationReceived] = useState(false); // Nuevo estado

  const [activeChatId, setActiveChatId] = useState(null);
  const activeChatIdRef = useRef(null);

  useEffect(() => {
    const match = location.pathname.match(/^\/chat\/(\d+)$/);
    if (match) {
      const chatId = parseInt(match[1], 10);
      setActiveChatId(chatId);
      activeChatIdRef.current = chatId; // Sincroniza la referencia
    } else {
      setActiveChatId(null);
      activeChatIdRef.current = null;
    }
  }, [location]);

  useEffect(() => {
    const fetchUser = async () => {
      if (!hasCheckedUser) {
        if (!user || !user.data?.users?.username) {
          await checkServerStatus();

          if (user && !user.data?.users?.username) {
            setShowModal(true);
            setHasCheckedUser(true);
          }
        }
      }
    };

    fetchUser();
  }, [checkServerStatus, hasCheckedUser, user]);

  useEffect(() => {
    if (user && user.data && user.data.users) {
      const token = localStorage.getItem("token");
      const chatsSocket = new WebSocket(
        `ws://localhost:8000/ws/chats/?token=${token}&user_id=${user.data.users.id}`
      );
      chatsSocketRef.current = chatsSocket;

      chatsSocket.onopen = () => {
        console.log("Conexión WebSocket abierta");
      };

      chatsSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "chat_list") {
          //  console.log("Chats recibidos desde WebSocket", data.chats);

          const updatedChats = data.chats.map((chat) => ({
            name: chat.other_user,
            last: chat.last_message.content,
            seen: chat.last_message.seen,
            id: chat.id,
            unseen_count: chat.unseen_messages_count,
          }));

          setChats((prevChats) => {
            // Combinar los chats anteriores y nuevos
            const combinedChats = [
              ...prevChats.filter(
                (prevChat) =>
                  !updatedChats.some((newChat) => newChat.id === prevChat.id)
              ),
              ...updatedChats,
            ];

            // Ordenar por el tiempo del último mensaje en orden descendente
            return combinedChats.sort(
              (a, b) => b.lastMessageTime - a.lastMessageTime
            );
          });
        }
        if (data.type === "notification") {
          setNotificationReceived(true);
          if (data.notification.data.chat_id === activeChatIdRef.current) {
            setNotificationReceived(false);

          }
          setNotification(data.notification) 
        }
      };

      chatsSocket.onclose = () => {
        console.log("Conexión WebSocket cerrada");
      };

      return () => {
        if (chatsSocketRef.current) {
          chatsSocketRef.current.close();
        }
      };
    }
  }, [user, usernameFilter]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        contextMenuRef.current &&
        !contextMenuRef.current.contains(e.target)
      ) {
        setContextMenu(null);
      }
    };

    if (contextMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [contextMenu]);

  const handleCreateChat = async (username_2) => {
    try {
      const response = await fetch("http://localhost:8000/api/chats/guardar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ username: username_2 }),
      });

      const data = await response.json();

      if (response.ok) {
        navigate(`/chat/${data.data.id}`);
      } else {
        console.error("Error al crear el chat:", data.message);
      }
    } catch (error) {
      console.error("Error al llamar a la API:", error);
    }
  };

  const handleSaveUsername = async (username) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/users/actualizar",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ username }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setShowModal(false);
        addNotification(
          "Nombre de usuario " +
            data.data.username +
            " fue asignado correctamente",
          "success"
        );
      } else {
        addNotification(
          "Error al asignar el nombre de usuario: " + data.errors.username[0],
          "danger"
        );
      }
    } catch (error) {
      addNotification("Error en la solicitud: " + error.message, "danger");
    }
  };

  // Función para buscar chats o amigos filtrados
  const fetchChatsOrFriends = async (username) => {
    setUsernameFilter(username);

    if (username.trim() === "") {
      setFilteredChats([]);
      setIsFiltering(false);
    } else {
      setIsFiltering(true);

      try {
        const response = await fetch("http://localhost:8000/api/chats/filtro", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username: username }),
        });

        const data = await response.json();

        if (data.code === 200) {
          const formattedChats = data.data.chats.map((chat) => ({
            name: chat.other_user,
            last: chat.last_message.content,
            seen: chat.last_message.seen,
            id: chat.id,
          }));

          setFilteredChats(formattedChats);
        } else {
          console.error("Error al obtener los chats filtrados", data.message);
        }
      } catch (error) {
        console.error("Error en la solicitud de chats:", error);
      }
    }
  };

  const handleRightClick = (e, chat) => {
    e.preventDefault();
    setSelectedChat(chat);
    setContextMenu({ x: e.clientX, y: e.clientY });
  };

  const handleMenuOption = async (option) => {
    if (option === "eliminar") {
      if (selectedChat) {
        try {
          const response = await fetch(
            `http://127.0.0.1:8000/api/chats/eliminar/${selectedChat.id}`,
            {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${localStorage.getItem("token")}`,
              },
            }
          );

          if (response.ok) {
            setChats((prevChats) =>
              prevChats.filter((chat) => chat.id !== selectedChat.id)
            );
            addNotification("Chat eliminado correctamente", "success");
          } else {
            console.error("Error al eliminar el chat");
            addNotification("Error al eliminar el chat", "danger");
          }
        } catch (error) {
          console.error("Error en la solicitud de eliminación:", error);
          addNotification(
            "Error al eliminar el chat: " + error.message,
            "danger"
          );
        }
      }
    }
    setContextMenu(null);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/iniciar-sesion");
  };

  const resetNotificationReceived = () => {
    setNotificationReceived(false);
  };

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <UserContext.Provider value={user}>
      <div className="container-fluid layout">
        <div className="row">
          <div>
         
            {notificationReceived && notification && (
              <NotificationManager
                notification={notification}
                activeChatId={activeChatId}
                onNotificationHandled={resetNotificationReceived}
              />
            )}
          </div>

          <div className="p-2 nav navbar">
            <div className="container-fluid d-flex flex-wrap justify-content-between align-items-center">
              <div className="d-flex flex-wrap align-items-center nav-options">
                <div className="nav-item" onClick={() => navigate(`/`)}>
                  Inicio
                </div>
                <div className="nav-item" onClick={() => navigate(`/amigos`)}>
                  Amigos
                </div>
                <div
                  className="nav-item"
                  onClick={() => navigate(`/amigos/añadir`)}
                >
                  Añadir amigos
                </div>
                <div
                  className="nav-item"
                  onClick={() => navigate(`/amigos/pendiente`)}
                >
                  Solicitudes pendientes
                </div>
              </div>
              <div className="nav-item logout" onClick={handleLogout}>
                Cerrar sesión
              </div>
            </div>
          </div>
        </div>

        <div className="row layout-row">
          <div className="col-md-4 col-lg-3 lista">
            <div className="list d-flex flex-column">
              <h3>Chats</h3>

              <div className="search-chat">
                <input
                  type="text"
                  placeholder="Buscar chats"
                  value={usernameFilter}
                  onChange={(e) => fetchChatsOrFriends(e.target.value)}
                />
              </div>

              <div className="chats">
                {isFiltering ? (
                  // Si se está filtrando, mostrar los chats filtrados
                  filteredChats.length > 0 ? (
                    filteredChats.map((chat) => (
                      <div
                        key={chat.id}
                        className="chat"
                        onClick={() => {
                          if (typeof chat.id === "string") {
                            handleCreateChat(chat.id);
                          } else {
                            navigate(`/chat/${chat.id}`);
                          }
                        }}
                      >
                        <div className="chat-header">
                          <div className="person">
                            <p>{chat.name}</p>
                          </div>

                          <div className="message-list-info">
                            {chat.unseen_count > 0 && (
                              <div className="message-count">
                                <p>+{chat.unseen_count}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p>No se encontraron chats.</p>
                  )
                ) : // Si no se está filtrando, mostrar los chats completos
                chats.length > 0 ? (
                  chats.map((chat) => (
                    <div
                      key={chat.id}
                      className="chat"
                      onClick={() => navigate(`/chat/${chat.id}`)}
                      onContextMenu={(e) => handleRightClick(e, chat)}
                    >
                      <div className="chat-header">
                        <div className="person">
                          <p>{chat.name}</p>
                        </div>

                        <div className="message-list-info">
                          {chat.unseen_count > 0 && (
                            <div className="message-count">
                              <p>+{chat.unseen_count}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No tenes chats.</p>
                )}
              </div>
            </div>
          </div>

          <div className="col-md-8 col-lg-9 p-0">
            <Outlet context={{ chatsSocketRef }} />
            {/* <Outlet/> */}
          </div>
        </div>
        {/* Menú contextual */}
        {contextMenu && (
          <div
            ref={contextMenuRef} // Asocia la referencia al menú
            style={{
              position: "absolute",
              top: `${contextMenu.y}px`,
              left: `${contextMenu.x}px`,
            }}
            className="context-menu"
          >
            <div
              className="eliminar-chat"
              onClick={() => handleMenuOption("eliminar")}
            >
              Eliminar chat
            </div>
          </div>
        )}
      </div>

      {/* Modal para actualizar el nombre de usuario */}
      <Modal
        show={showModal}
        onSave={(username) => handleSaveUsername(username)}
      />
    </UserContext.Provider>
  );
};

export default Layout;

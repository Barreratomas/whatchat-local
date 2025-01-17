import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/friends.css";
import { useNotification } from "../components/Notification";

const Friends = () => {
  const navigate = useNavigate();

  const [friends, setFriends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const token = localStorage.getItem("token");
  const { addNotification } = useNotification();
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredFriends, setFilteredFriends] = useState([]);
  const [activeMenu, setActiveMenu] = useState(null);

  // Función para obtener la lista de amigos
  const fetchFriends = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/users/amigos", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Error al obtener los amigos.");
      }

      const data = await response.json();
      console.log(data);
      setFilteredFriends(data.friends);
      setFriends(data.friends);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const handleSearchChange = (e) => {
    const term = e.target.value.toLowerCase();
    setSearchTerm(term);

    // Filtrar la lista de amigos según el término de búsqueda
    const filtered = friends.filter((friend) =>
      friend.username.toLowerCase().includes(term)
    );
    setFilteredFriends(filtered);
  };

  useEffect(() => {
    fetchFriends();
  }, [fetchFriends]);

  // Función para bloquear un amigo
  const blockFriend = async (friendId, username) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/users/amigos/bloquear",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ to_user_id: friendId }),
        }
      );

      const data = await response.json();
      if (data.success) {
        addNotification(`${username} bloqueado correctamente.`, "success");

        fetchFriends();
      } else {
        addNotification(`Error: ${data.message}`, "danger");
      }
    } catch (err) {
      addNotification(`Error: ${err.message}`, "danger");
    }
  };

  // Función para desbloquear un amigo
  const unblockFriend = async (friendId, username) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/users/amigos/desbloquear",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ to_user_id: friendId }),
        }
      );

      const data = await response.json();
      if (data.success) {
        addNotification(`${username} desbloqueado correctamente.`, "success");

        fetchFriends();
      } else {
        addNotification(`Error: ${data.message}`, "danger");
      }
    } catch (err) {
      addNotification(`Error: ${err.message}`, "danger");
    }
  };

  // Función para eliminar un amigo
  const removeFriend = async (friendId, username) => {
    try {
      const response = await fetch(
        "http://localhost:8000/api/users/amigos/eliminar",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ to_user_id: friendId }),
        }
      );

      const data = await response.json();
      if (data.success) {
        addNotification(
          `${username} eliminado de amigos correctamente.`,
          "success"
        );

        fetchFriends();
      } else {
        addNotification(`Error: ${data.message}`, "danger");
      }
    } catch (err) {
      addNotification(`Error: ${err.message}`, "danger");
    }
  };

  useEffect(() => {
    fetchFriends();
  }, [fetchFriends]);

  const toggleMenu = (id) => {
    setActiveMenu(activeMenu === id ? null : id); // Alternar el menú
  };

  if (loading) return <div>Cargando amigos...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="content-friends">
      <div className="friends-list">
        <h4 className="friends-list-title">
          Lista de Amigos-{filteredFriends.length}
        </h4>

        {/* Barra de búsqueda */}
        <input
          type="text"
          placeholder="Buscar amigos..."
          value={searchTerm}
          onChange={handleSearchChange}
          className="search-friend"
        />

        {filteredFriends.length > 0 ? (
          <ul className="content-list-friends">
            {filteredFriends.map((friend) => (
              <div
                key={friend.id}
                style={{ marginBottom: "10px", position: "relative" }}
              >
                <div className="friends-list-friend">
                  <span>{friend.username}</span>
                  <div className="friend-actions">
                    <div
                      className="to_friend_chat"
                      onClick={() => navigate(`/chat/${friend.chat_id}`)}
                    >
                      <i className="bi bi-chat-fill"></i>
                    </div>
                    <div
                      onClick={() => toggleMenu(friend.id)}
                      className="friend_option"
                    >
                      <i className="bi bi-three-dots-vertical"></i>
                    </div>
                  </div>
                </div>
                {activeMenu === friend.id && (
                  <div className="friend-menu-options">
                    {!friend.blocked && (
                      <div
                        onClick={() =>
                          blockFriend(friend.user_id, friend.username)
                        }
                      >
                        Bloquear
                      </div>
                    )}
                    {friend.blocked && (
                      <div
                        onClick={() =>
                          unblockFriend(friend.user_id, friend.username)
                        }
                      >
                        Desbloquear
                      </div>
                    )}
                    <div
                      onClick={() =>
                        removeFriend(friend.user_id, friend.username)
                      }
                    >
                      Eliminar
                    </div>
                  </div>
                )}
              </div>
            ))}
          </ul>
        ) : (
          <p>No se encontraron amigos.</p>
        )}
      </div>
    </div>
  );
};

export default Friends;

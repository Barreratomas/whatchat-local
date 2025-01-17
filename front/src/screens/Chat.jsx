import React, { useEffect, useState, useRef, useContext } from "react";
import { useParams } from "react-router-dom";
import "../styles/chat.css";
import { UserContext } from "../screens/Layout";
import { useOutletContext } from "react-router-dom";

const Chat = () => {
  const user = useContext(UserContext);
  const { chatsSocketRef } = useOutletContext();

  const userID = user?.data?.users?.id;
  const username = user?.data?.users?.username;
  const [otherUser, setOtherUser] = useState(null);

  const { id } = useParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const chatSocketRef = useRef(null);
  const [socketReady, setSocketReady] = useState(false);

  const [contextMenu, setContextMenu] = useState(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const contextMenuRef = useRef(null);

  const [editingMessage, setEditingMessage] = useState(null);
  const [editInput, setEditInput] = useState("");

  const chatEndRef = useRef(null); 
  const [isFirstLoad, setIsFirstLoad] = useState(false); 
  const [isSecondLoad, setIsSecondLoad] = useState(false); 
  useEffect(() => {
    setMessages([]);
 
  }, [id]); 

  useEffect(() => {
    if (isFirstLoad && chatEndRef.current && !!!isSecondLoad) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
      setIsSecondLoad(true); // Marcar
    }
  }, [isFirstLoad,isSecondLoad,id]); 

  useEffect(() => {
    const token = localStorage.getItem("token");

    const chatSocket = new WebSocket(
      `ws://localhost:8000/ws/chat/${id}/?token=${token}`
    );
    chatSocketRef.current = chatSocket;

    chatSocket.onopen = () => {
      console.log("WebSocket abierto");
      setSocketReady(true);

      if (chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(
          JSON.stringify({
            type: "mark_seen",
            room_id: id,
            user_id: userID,
          })
        );
      }

      
      if (chatsSocketRef.current?.readyState === WebSocket.OPEN && otherUser) {
        chatsSocketRef.current.send(
          JSON.stringify({
            type: "update_chat_list",
            user_id: userID,
            other_user_id: otherUser.id,
          })
        );
      }
    };

    chatSocket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        // console.log("Respuesta del WebSocket:", data);

        switch (data.type) {
          case "message_deleted":

            if (data.message_id) {
              setMessages((prevMessages) =>
                prevMessages.filter((msg) => msg.id !== data.message_id)
              );
            } else {
              console.warn("message_id no recibido para message_deleted.");
            }
            break;

          case "message_updated":
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === data.message_id
                  ? { ...msg, message: data.new_content }
                  : msg
              )
            );
            break;

          case "messages_marked_seen":
    

            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.user_id !== data.user_id ? { ...msg, seen: true } : msg
              )
            );
            break;

          case "chat_message":
            setMessages((prevMessages) => [
              ...prevMessages,
              ...data.messages.map((msg) => ({
                message: msg.content,
                username: msg.username || "Otro Usuario",
                datetime: msg.timestamp,
                user_id: msg.user,
                self: msg.user === userID,
                seen: msg.seen,
                id: msg.id,
              })),
            ]);
            // marcar como visto
            chatSocketRef.current.send(
              JSON.stringify({
                type: "mark_seen",
                room_id: id,
                user_id: userID,
              })
            );

            

            if (data.other_user) {
              setOtherUser({
                id: data.other_user.id,
                username: data.other_user.username,
                email: data.other_user.email,
              });
              chatsSocketRef.current.send(
                JSON.stringify({
                  type: "update_chat_list",
                  user_id: userID, 
                  other_user_id: data.other_user.id, 
                })
              );
            }
  
            setIsFirstLoad(true);
            break;
          default:
            console.warn("Tipo de mensaje desconocido:", data.type);
        }
      } catch (error) {
        console.error("Error procesando mensaje WebSocket:", error);
      }
    };

  
    chatSocket.onclose = () => {
      console.log("WebSocket cerrado. No se intentará reconectar.");
      setSocketReady(false);
      setIsSecondLoad(false);
      setIsFirstLoad(false);
    }

    chatSocket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
    
    return () => {
      chatSocket.close();
    };
  }, [id, userID,chatsSocketRef]);

  const sendMessage = () => {
    if (input.trim() && socketReady) {
      if (chatSocketRef.current.readyState === WebSocket.OPEN) {
        chatSocketRef.current.send(
          JSON.stringify({
            type: "send_message",
            message: input.trim(),
            user_id: userID,
            username: username,
          })
        );
        setInput("");

        chatsSocketRef.current.send(
          JSON.stringify({
            type: "update_chat_list",
            notification:"notification",
            user_id: userID, 
            other_user_id: otherUser.id, 
          })
        );


      } else {
        console.log("WebSocket no está abierto");
      }
    }
  };



  const deleteMessage = (messageId) => {
    if (chatSocketRef.current.readyState === WebSocket.OPEN) {
      chatSocketRef.current.send(
        JSON.stringify({
          type: "delete_message",
          message_id: messageId,
        })
      );
    }
  };

  const updateMessage = (messageId, newContent) => {
    if (chatSocketRef.current.readyState === WebSocket.OPEN) {
      chatSocketRef.current.send(
        JSON.stringify({
          type: "update_message",
          message_id: messageId,
          content: newContent,
        })
      );
    }
  };

  const handleContextMenu = (e, message) => {
    e.preventDefault();
    setSelectedMessage(message);

    const menuWidth = contextMenuRef.current?.offsetWidth || 0;
    const newX = e.pageX - menuWidth;
    const newY = e.pageY;

    setContextMenu({
      x: newX,
      y: newY,
    });
  };

  const handleClickOutside = () => {
    setContextMenu(null);
  };

  useEffect(() => {
    document.addEventListener("click", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, []);

  const startEditing = (message) => {
    setEditingMessage(message.id);
    setEditInput(message.message);
  };

  const finishEditing = () => {
    if (editingMessage !== null && editInput.trim()) {
      updateMessage(editingMessage, editInput.trim());
    }
    setEditingMessage(null);
    setEditInput("");
  };

  const autoExpand = (e) => {
    e.target.style.height = "20px"; // Altura mínima
    e.target.style.height = `${e.target.scrollHeight}px`;
  };
  return (
    <div className="inchat">
      <div className="contact">
        <p>{otherUser?.username || ""}</p>
      </div>
      <div className="chat-box">
        {messages.map((msg, index) => {
          return (
            <div
              key={index}
              className={`message ${msg.self ? "self" : "other"}`}
              onContextMenu={(e) => handleContextMenu(e, msg)}
            >
              <div className={`message-info`}>
                <p className="username-message">{msg.username}</p>
                <p className="date-message">
                  {new Date(msg.datetime).toLocaleDateString("es-ES", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                  })}{" "}
                  {new Date(msg.datetime).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>

              {editingMessage === msg.id ? (
                <textarea
                  className="input-edit-message auto-expand"
                  value={editInput}
                  onChange={(e) => {
                    setEditInput(e.target.value);
                    autoExpand(e);
                  }}
                  onBlur={finishEditing}
                  autoFocus
                />
              ) : (
                <p>{msg.message}</p>
              )}

              <div className={`message-details `}>
                <div className="message-seen"></div>
                <small className="fst-italic fw-bold seen">
                  {msg.seen && "Visto"}
                </small>
              </div>
            </div>
          );
        })}
          <div ref={chatEndRef} /> 

      </div>
      {contextMenu && (
        <div
          className="context-menu"
          ref={contextMenuRef}
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <div
            className="option-context-menu"
            onClick={() => startEditing(selectedMessage)}
          >
            Editar
          </div>

          <div
            className="option-context-menu"
            onClick={() => deleteMessage(selectedMessage.id)}
          >
            Eliminar
          </div>
        </div>
      )}
      <div className="input-box">
        <input
          type="text"
          placeholder="Escribe un mensaje..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              sendMessage();
            }
          }}
        />
        <button onClick={sendMessage}>Enviar</button>
      </div>
    </div>
  );
};

export default Chat;

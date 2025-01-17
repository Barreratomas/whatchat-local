import React, { createContext, useState, useContext, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const ServerStatusContext = createContext();

export const ServerStatusProvider = ({ children }) => {
  const [serverStatus, setServerStatus] = useState(false);
  const [user, setUser] = useState(null); // Estado para almacenar los datos del usuario

  const [error, setError] = useState(null); 
  const navigate = useNavigate(); // Hook para redireccionar

  const checkServerStatus = useCallback(async () => {
    const token = localStorage.getItem("token");

    if (!token) {
      setServerStatus(false);
      setUser(null);
      setError("No token found");
      navigate("/iniciar-sesion"); // Redirigir a la página de inicio de sesión
      return null;
    }

    try {
      const response = await axios.get("http://127.0.0.1:8000/api/users/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.status === 200) {
        setServerStatus(true);
        setError(null); 
        setUser(response.data); // Almacenar los datos del usuario

        return response.data; // Devolver los datos del usuario
      }
    } catch (error) {
      console.error("Error de autenticación:", error.response || error);
      setError(error.response ? error.response.data.message || "Error inesperado" : "Error de conexión con el servidor");
    }

    setServerStatus(false);
    setUser(null);
    return null;
  }, [navigate]);

  return (
    <ServerStatusContext.Provider value={{ serverStatus, user, checkServerStatus, error }}>
      {children}
    </ServerStatusContext.Provider>
  );
};

export const useServerStatus = () => useContext(ServerStatusContext);

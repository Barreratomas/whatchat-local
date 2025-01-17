import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useNotification } from "../components/Notification";

import "../styles/login.css";

const Register = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { addNotification } = useNotification();

  const handleRegister = async (e) => {
    e.preventDefault(); 

    try {
      const response = await fetch("http://localhost:8000/api/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
        }),
      });
    
      const data = await response.json();
    
      if (response.ok) {
        // Si la respuesta es exitosa (status 2xx), limpia los campos y navega
        setUsername("");
        setEmail("");
        setPassword("");
        navigate("/iniciar-sesion");
      }else {
        // Procesar errores del servidor y mostrar solo los mensajes
        if (data.errors) {
          Object.keys(data.errors).forEach(field => {
            const errorMessages = data.errors[field].join(", "); 
            addNotification(errorMessages, "danger");
          });
        } else {
          console.log("Errores del servidor:", data.detail || "Error desconocido");
        }
      }
    } catch (error) {
      // Si ocurre un error en la solicitud (como problemas de red), lo mostramos en consola
      console.error("Error en la solicitud:", error.message);
    }
  };

  // Alternar la visibilidad de la contraseña
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="container login-container">
      <div className="row justify-content-center col-sm-6 col-md-6 col-lg-4">
        <div>
          <h2 className="text-center text-light">Registrarse</h2>
          <form onSubmit={handleRegister} className="form-container">
            <div className="form-group">
              <label htmlFor="username" className="text-light">Nombre de usuario</label>
              <input
                type="text"
                id="username"
                className="form-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)} // Actualizar el estado
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="email" className="text-light">Correo electrónico</label>
              <input
                type="email"
                id="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)} // Actualizar el estado
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password" className="text-light">Contraseña</label>
              <div className="password-container">
                <input
                  type={showPassword ? "text" : "password"}  // Alternar tipo de input
                  id="password"
                  className="form-control"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)} // Actualizar el estado
                  required
                />
                <span
                  className="password-toggle"
                  onClick={togglePasswordVisibility}
                  style={{ cursor: 'pointer' }}
                >
                  {showPassword ? (
                    <i className="bi bi-eye-slash"></i>  // Ícono de contraseña oculta
                  ) : (
                    <i className="bi bi-eye"></i>  // Ícono de contraseña visible
                  )}
                </span>
              </div>
            </div>
            <div className="login-btn text-center">
              <button type="submit" className="btn btn-primary btn-block mt-3">
                Crear cuenta
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Register;

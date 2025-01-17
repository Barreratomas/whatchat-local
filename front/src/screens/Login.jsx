import React, { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "../styles/login.css";
import { useNotification } from "../components/Notification";


const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const { addNotification } = useNotification();

  const handleLoginSuccess = async (response) => {
    const googleToken = response.credential;

    try {
      const res = await axios.post("http://localhost:8000/api/login/", {
        token: googleToken,
      });

      console.log("Login Success:", res.data);
      localStorage.setItem("token", res.data.token);
      navigate("/");
    } catch (error) {
      console.error("Login Failed:", error);
    }
  };

  const handleLoginFailure = (error) => {
    console.log("Login Failed:", error);
  };

  const handleNormalLogin = async (e) => {
    e.preventDefault();

    try {
      const res = await axios.post("http://localhost:8000/api/login/", {
        email,
        password,
      });
      console.log("Normal Login Success:", res.data);
      localStorage.setItem("token", res.data.token);
      navigate("/");
    } catch (error) {
      if (error.response) {
        // Muestra el mensaje de error enviado desde el backend
        addNotification(error.response.data.detail, "error");
        console.log("Normal Login Failed:", error.response.data.detail);
      } else {
        // Muestra un error genérico si no hay respuesta del servidor
        console.log("Normal Login Failed:", error.message);
      }
    }
  };

  const handleRegisterRedirect = () => {
    navigate("/registrarse");
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="container login-container">
      <div className="row justify-content-center col-sm-6 col-md-6 col-lg-4">
        <div>
          <h2 className="text-center text-light">Iniciar sesión </h2>

          {/* Formulario de inicio de sesión */}
          <form onSubmit={handleNormalLogin} className="form-container">
            <div className="form-group">
              <label htmlFor="email" className="text-light">
                Correo electrónico
              </label>
              <input
                type="email"
                id="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password" className="text-light">
                Contraseña
              </label>
              <div className="password-container">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  className="form-control"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <span
                  className="password-toggle"
                  onClick={togglePasswordVisibility}
                  style={{ cursor: "pointer" }}
                >
                  {showPassword ? (
                    <i className="bi bi-eye-slash"></i>
                  ) : (
                    <i className="bi bi-eye"></i>
                  )}
                </span>
              </div>
            </div>

            <div className="login-btn text-center">
              <button type="submit" className="btn btn-primary btn-block mt-3">
                Ingresar
              </button>
            </div>

            <div className="mt-3 text-center">
              <p className="text-light">
                ¿No tienes una cuenta?{" "}
                <button
                  type="button"
                  className="text-primary register-btn"
                  onClick={handleRegisterRedirect}
                >
                  Regístrate aquí
                </button>
              </p>
            </div>
          </form>

          {/* Google Login Button */}
          <div className="d-flex justify-content-center mt-3">
            <GoogleLogin
              onSuccess={handleLoginSuccess}
              onError={handleLoginFailure}
              useOneTap
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

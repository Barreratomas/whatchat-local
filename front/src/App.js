import "./App.css";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import Layout from "./screens/Layout";
import Login from "./screens/Login";
import Home from "./screens/Home";
import Register from "./screens/Register";
import Chat from "./screens/Chat";
import AddFriend from "./screens/AddFriend";
import PendingRequest from "./screens/PendingRequest";
import Friends from "./screens/Friends";
import { ServerStatusProvider } from "./components/ServerStatusProvider";
import { NotificationProvider } from "./components/Notification";
function App() {
  return (
    <GoogleOAuthProvider clientId="513433306222-0vcfi8o8fr6qeu2snd35778jpn51kjar.apps.googleusercontent.com">
      <Router>
        <div className="App">
        <NotificationProvider>

          <Routes>
              {/* Ruta principal que usa Layout como contenedor */}
              <Route
                path="/"
                element={
                  <ServerStatusProvider>
                    <Layout />
                  </ServerStatusProvider>
                }
              >
                <Route path="/" element={<Home />}>
                  <Route path="amigos/" element={<Friends />} />
                  <Route path="amigos/añadir" element={<AddFriend />} />
                  <Route path="amigos/pendiente" element={<PendingRequest />} />
                </Route>
                <Route path="/chat/:id" element={<Chat />} />
              </Route>

              <Route path="/iniciar-sesion" element={<Login />} />
              <Route path="/registrarse" element={<Register />} />
          </Routes>
          </NotificationProvider>

        </div>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;

import { useState, useEffect } from "react";
import { useNotification } from "../components/Notification";
import "../styles/pendingRequest.css";
const PendingRequest = () => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const token = localStorage.getItem("token");
  const { addNotification } = useNotification();

  // Función para rechazar o aceptar solicitudes
  const handleRequestResponse = async (requestId, action) => {
    try {
      const url = `http://localhost:8000/api/users/solicitud/${action}/${requestId}`;

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        addNotification(
          `Error: No fue posible ${action} la solicitud`,
          "danger"
        );
      }

      // Recargar las solicitudes pendientes después de aceptar o denegar
      const updatedRequests = requests.filter(
        (request) => request.id !== requestId
      );
      setRequests(updatedRequests);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    // Función para obtener las solicitudes pendientes
    const fetchPendingRequests = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/api/users/solicitud/pendiente",
          {
            method: "GET", // Método de solicitud
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`, // Enviar el token en el encabezado de autorización
            },
          }
        );

        if (!response.ok) {
          throw new Error("Error al obtener las solicitudes pendientes");
        }

        const data = await response.json(); // Convertir la respuesta a JSON
        console.log(data);

        // Acceder a las solicitudes desde la propiedad 'pending_requests'
        if (data && Array.isArray(data.pending_requests)) {
          setRequests(data.pending_requests); // Guardar las solicitudes pendientes
        } else {
          setRequests([]); // Si no hay solicitudes pendientes, guardar un array vacío
        }

        setLoading(false); // Detener el estado de carga
      } catch (err) {
        setError(err.message); // Manejo de errores
        setLoading(false); // Detener el estado de carga
      }
    };

    fetchPendingRequests(); // Llamar a la función para obtener las solicitudes pendientes
  }, [token]); // Solo se vuelve a ejecutar cuando cambia el token

  // Renderizado condicional basado en el estado de carga o error
  if (loading) {
    return <div>Cargando...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="pending-content m-5">
      <h3>Solicitudes Pendientes</h3>
      {requests.length === 0 ? (
        <div className="no-pending-content">
          <p className="no-pending">No hay solicitudes pendientes.</p>
        </div>
      ) : (
        <div className="pending-requests">
          {requests.map((request, index) => (
            <div key={index} className="pending-user">
              <p>{request.from_user}</p>
              <div className="pending-options">
                <div
                  onClick={() => handleRequestResponse(request.id, "aceptar")}
                >
                  <i className="bi bi-check-circle"></i>
                </div>
                <div
                  onClick={() => handleRequestResponse(request.id, "rechazar")}
                >
                  <i className="bi bi-x-circle"></i>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PendingRequest;

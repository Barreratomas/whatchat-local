import { useState } from "react";
import "../styles/add-friend.css";
import { useNotification } from "../components/Notification";

const AddFriend = () => {
  // Estado para guardar el nombre de usuario
  const [username, setUsername] = useState("");
  const token = localStorage.getItem("token"); // Obtener el token del localStorage
  const { addNotification } = useNotification(); 


  const handleAddFriend = async (e) => {
    e.preventDefault(); // Evitar el envío predeterminado del formulario

    try {
      const response = await fetch("http://localhost:8000/api/users/solicitud/enviar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,

        },
        body: JSON.stringify({ username }), // Enviar el username al servidor
      });

      const data = await response.json();
      console.log(data);

      if (response.ok) {
        addNotification(`La solicitud fue enviada a  ${username} correctamente.`, "success");

      } else {
        addNotification(`Error: ${data.error}`, "danger");
      }
    } catch (error) {
      addNotification(`Error: ${error.message}`, "danger");
    }
  };

  return (
    <div className="add-friend m-5">
      <h3>Añadir amigos</h3>
      <form
        className="add-friend-form col-12 col-xl-7"
        onSubmit={handleAddFriend}
      >
        <input
          className="input-add-friend"
          type="text"
          placeholder="Podes agregar a un amigo con su nombre de usuario"
          value={username} // Asociar el valor del estado
          onChange={(e) => setUsername(e.target.value)} // Actualizar el estado
        />
        <button className="button-add-friend" type="submit">
          Enviar
        </button>
      </form>
    </div>
  );
};

export default AddFriend;

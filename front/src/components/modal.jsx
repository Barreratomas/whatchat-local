import React, { useState, useEffect } from "react";
import "../styles/modal.css";

const Modal = ({ show, onSave, initialValue = "" }) => {
  const [usernameInput, setUsernameInput] = useState(initialValue);

  useEffect(() => {
    if (show) {
      setUsernameInput(initialValue); // Reinicia el valor cuando se muestra el modal
    }
  }, [show, initialValue]);

  if (!show) {
    return null; // No renderizar el modal si no está visible
  }

  const handleSave = () => {
    if (usernameInput.trim() !== "") {
      onSave(usernameInput); // Llama a la función de guardado con el nombre de usuario
    } else {
      alert("El nombre de usuario no puede estar vacío."); // Validación
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Ingrese un nombre de usuario</h2>
        <p>Elija un nombre de usuario único para su cuenta</p>
        <input
          type="text"
          placeholder="Ingresar nombre de usuario"
          value={usernameInput}
          onChange={(e) => setUsernameInput(e.target.value)}
        />
        <div className="modal-actions">
          <button onClick={handleSave}>Guardar</button>
        </div>
      </div>
    </div>
  );
};

export default Modal;

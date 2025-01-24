# Whatchat

## **Descripción**  
Whatchat permite  a los usuarios comunicarse fácil y rápidamente. Ofrece opciones para gestionar amigos, enviar y recibir mensajes, organizar chats, bloquear o eliminar contactos, y más. Además, cuenta con un sistema de registro e inicio de sesión.

---

## ****Características Principales:****  
## ****Gestión de usuarios:****
- Registro e inicio de sesión seguro.
 
## ****Sistema de amigos:****
- Enviar, aceptar y rechazar solicitudes de amistad.
- Bloquear o eliminar amigos.

## ****Mensajería:****
- Enviar, modificar y eliminar mensajes.
- Filtrar y organizar chats.
- Notificacion de mensajes.
- Indicadores de mensajes no leídos y estado de "visto" en los chats.
- Lista de chats con opciones para filtrar conversaciones.


---
## **Requisitos Previos**  
- [Python](https://www.python.org/).
- [Node.js y npm](https://nodejs.org/en/download/).
- [Docker Desktop](https://www.docker.com/)
- [GIT](https://git-scm.com/). 

---
## **Preparar django:**
- Abre una terminal.
- Navega al back desde el directorio raiz del proyecto:
```
cd back
```

Para instalar las dependencias:
```
pip install -r requirements.txt
```
Para migrar a la base de datos:
```
python manage.py migrate
```
Para iniciar el servidor:
```
 py manage.py runserver
```


---
## **Preparar Docker Desktop:**
Ejecuta en la consola
```
docker run -d --name redis -p 6379:6379 redis
```
Ir a Docker desktop, ingresar a containers e iniciar el container llamado redis


--- 
## **Preparar React:**
- Abre una terminal.
- Navega al front desde el directorio raiz del proyecto:
```
cd front
```
Para instalar las dependencias:
```
npm install
```
Para iniciar el servidor:
```
npm start
```

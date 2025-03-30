const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

// Servir arquivos estáticos
app.use(express.static(__dirname));

// Endpoint padrão
app.get('/', (req, res) => {
  res.sendFile(__dirname + '/client.html');
});

// Configuração do Socket.IO
io.on('connection', (socket) => {
  console.log('Usuario conectado');

  // Envia notificações a cada 5 segundos
  const notificationInterval = setInterval(() => {
    const notification = { message: 'Nova atualização disponível!', timestamp: new Date() };
    socket.emit('notification', notification);
  }, 5000);

  socket.on('disconnect', () => {
    console.log('Usuario desconectado');
    clearInterval(notificationInterval);
  });
});

// Inicializa o servidor na porta 3000
server.listen(3000, () => {
  console.log('Servidor escutando na porta 3000');
});

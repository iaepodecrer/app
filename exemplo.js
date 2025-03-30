/**
 * exemplo.js
 * 
 * Arquivo de exemplo que demonstra funções utilitárias básicas
 * usadas por outros módulos do CrossDebate.
 */

/**
 * Formata uma mensagem adicionando timestamp ISO
 * 
 * @param {string} mensagem - Mensagem original a ser formatada
 * @returns {string} Mensagem formatada com timestamp ISO
 * @example
 * // Retorna algo como: "[2025-03-30T10:15:30.123Z] Olá mundo"
 * formataMensagem("Olá mundo");
 */
function formataMensagem(mensagem) {
  const data = new Date();
  return `[${data.toISOString()}] ${mensagem}`;
}

/**
 * Executa operações da Função A
 * 
 * @returns {void}
 */
function funcaoA() {
  // ...existing code...
  console.log(formataMensagem("Função A chamada"));
  // ...existing code...
}

/**
 * Executa operações da Função B
 * 
 * @returns {void}
 */
function funcaoB() {
  // ...existing code...
  console.log(formataMensagem("Função B chamada"));
  // ...existing code...
}

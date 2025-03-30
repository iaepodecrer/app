# Sistema de Tema Unificado

Este projeto agora utiliza um sistema unificado de gerenciamento de tema, consolidando todas as implementações anteriores em um único utilitário.

## Funcionalidades

- Detecção automática do tema preferido do sistema
- Suporte para tema automático (seguindo o sistema), escuro ou claro
- Salvamento da preferência do usuário
- Sistema de eventos para notificar sobre mudanças de tema
- Compatibilidade com código legado

## Como usar

### Importação

```javascript
// Importe as funções necessárias
import { 
  initTheme, 
  toggleTheme, 
  applyTheme, 
  DARK_THEME, 
  LIGHT_THEME, 
  AUTO_THEME 
} from './js/utils/themeManager.js';
```

### Inicialização

```javascript
// Inicialize o tema (automaticamente ao carregar o DOM)
document.addEventListener('DOMContentLoaded', () => {
  initTheme(); // Não é necessário se você estiver usando o carregamento automático
});
```

### Alternando o tema manualmente

```javascript
// Alternar entre claro e escuro
document.getElementById('themeToggle').addEventListener('click', toggleTheme);
```

### Aplicando um tema específico

```javascript
// Aplicar tema escuro
applyTheme(DARK_THEME);

// Aplicar tema claro
applyTheme(LIGHT_THEME);

// Aplicar tema automático (segue preferência do sistema)
applyTheme(AUTO_THEME);
```

### Respondendo a eventos de tema

```javascript
import { onThemeChange } from './js/utils/themeManager.js';

// Registre um callback para quando o tema mudar
const removeListener = onThemeChange(({ theme, isDark }) => {
  console.log(`Tema alterado para: ${theme} (escuro: ${isDark})`);
  
  // Atualize elementos que dependem do tema
  updateUIForTheme(isDark);
});

// Para remover o listener posteriormente:
// removeListener();
```

## Compatibilidade com código legado

Se você estava usando implementações anteriores, pode continuar utilizando-as por meio da camada de compatibilidade:

```javascript
import { 
  toggleDarkMode, 
  setDarkTheme, 
  isDarkMode 
} from './js/utils/themeCompatibility.js';

// Essas funções continuarão funcionando, mas mostrarão avisos
// de depreciação no console e utilizarão a nova implementação internamente
```

## Botões de alternância de tema

O sistema procura automaticamente por elementos com seletores `.theme-toggle` ou `#themeToggle` para configura-los como botões de alternância.

Para configurar manualmente outros elementos:

```javascript
import { setupThemeToggle } from './js/utils/themeManager.js';

// Configure um botão específico
setupThemeToggle('#meuBotaoDeTema');

// Ou passe o elemento diretamente
const botao = document.querySelector('.botao-tema-personalizado');
setupThemeToggle(botao);
```

## Ícones responsivos ao tema

Adicione a classe `.dark-icon` aos ícones que devem aparecer apenas no tema claro.
Adicione a classe `.light-icon` aos ícones que devem aparecer apenas no tema escuro.

O sistema gerenciará automaticamente a visibilidade desses ícones quando o tema mudar.

# Sistema de Validação e Gerenciamento de Tema

Este projeto implementa um sistema consistente para validação de dados de entrada/saída e um gerenciador unificado de tema claro/escuro para o CrossDebate.

## Sistema de Validação

O sistema de validação oferece funções para validar diferentes tipos de dados de entrada, como:

- Validação de strings vazias
- Validação de emails
- Validação de datas
- Validação numérica e de intervalos
- Sanitização de strings
- Prevenção XSS
- Validação de formulários completos

### Como usar

#### Importando funções de validação

```javascript
import { 
  isEmpty, 
  isValidEmail, 
  hasMinLength, 
  validateForm 
} from './js/utils/validationUtils.js';
```

#### Exemplo de validação de formulário

```javascript
const formData = {
  name: document.getElementById('name').value,
  email: document.getElementById('email').value,
  message: document.getElementById('message').value
};

// Define regras de validação
const validationRules = {
  name: [
    {
      validate: (value) => !isEmpty(value),
      message: 'O nome é obrigatório'
    },
    {
      validate: (value) => hasMinLength(value, 3),
      message: 'O nome deve ter pelo menos 3 caracteres'
    }
  ],
  // Outras regras...
};

// Realiza a validação
const { isValid, errors } = validateForm(formData, validationRules);

if (!isValid) {
  // Exibe erros de validação
  displayErrors(errors);
  return;
}

// Processa os dados válidos...
```

## Gerenciador de Tema

O gerenciador de tema oferece uma solução unificada para alternar entre temas claro e escuro, incluindo:

- Detecção da preferência do sistema operacional
- Salvamento da preferência do usuário
- Alternância simples entre temas
- Atualização automática dos ícones
- Compatibilidade com diferentes convenções de nomes (dark-mode, dark-theme, etc.)

### Como usar

#### Inicializando o tema

```javascript
import { initTheme } from './js/utils/themeManager.js';

document.addEventListener('DOMContentLoaded', function() {
  // Inicializa o sistema de tema
  initTheme();
});
```

#### Alternando o tema manualmente

```javascript
import { toggleTheme } from './js/utils/themeManager.js';

const themeButton = document.querySelector('.theme-toggle');
themeButton.addEventListener('click', toggleTheme);
```

## Exemplo Completo

Um exemplo de implementação completa está disponível no arquivo `exemplo-validacao.html`, que demonstra tanto o sistema de validação quanto o gerenciador de tema em funcionamento.

## Estrutura de Arquivos

- `js/utils/validationUtils.js` - Utilitários de validação de dados
- `js/utils/themeManager.js` - Gerenciador unificado de tema
- `js/form-validation.js` - Exemplo de uso do sistema de validação
- `exemplo-validacao.html` - Exemplo completo de integração

## Benefícios

- **Consistência** - Interface unificada para validação e gerenciamento de tema
- **Modularidade** - Funções independentes que podem ser importadas conforme necessário
- **Manutenção simplificada** - Código consolidado em arquivos utilitários
- **Acessibilidade** - Suporte para preferências de tema do sistema
# Sistema de Eventos Personalizados e Gerenciador de Tema Unificado

Este projeto implementa dois sistemas principais que melhoram a arquitetura da aplicação CrossDebate:

1. **Sistema de Eventos Personalizados (EventBus)**: Para comunicação desacoplada entre componentes
2. **Gerenciador de Tema Unificado**: Consolida todas as funções relacionadas a tema/dark mode

## Sistema de Eventos Personalizados (EventBus)

O sistema de eventos implementa o padrão Pub/Sub (Publisher/Subscriber), permitindo que diferentes partes da aplicação se comuniquem sem serem diretamente acopladas entre si.

### Principais Recursos

- Publicação e assinatura de eventos nomeados
- Histórico automático de eventos (para componentes que se registram após o disparo)
- Callbacks que são executados apenas uma vez (`once`)
- Cancelamento fácil de inscrições com funções retornadas
- Sistema de configuração flexível
- Logging opcional para depuração

### Como Usar

#### Importando o EventBus

```javascript
// Importar a instância principal
import eventBus from './js/utils/eventBus.js';

// Ou importar métodos específicos para uso mais limpo
import { subscribe, publish, unsubscribe } from './js/utils/eventBus.js';
```

#### Publicando Eventos

```javascript
// Publicar um evento simples
publish('usuario:login', { id: 123, nome: 'João' });

// Publicar um evento com a instância do eventBus
eventBus.publish('dados:carregados', { 
  itens: items, 
  origem: 'api', 
  timestamp: Date.now() 
});
```

#### Assinando Eventos

```javascript
// Assinatura básica
subscribe('usuario:login', (data) => {
  console.log(`Usuário logado: ${data.nome}`);
});

// Assinatura com opções
const unsubscribe = subscribe('dados:carregados', (data) => {
  atualizarUI(data.itens);
}, { 
  once: true,                // Executar apenas uma vez
  receiveHistory: true       // Receber eventos passados do histórico
});

// Cancelar a inscrição
unsubscribe();
```

#### Configurando o EventBus

```javascript
import { configure } from './js/utils/eventBus.js';

configure({
  maxHistoryItems: 100,      // Aumentar o limite de histórico
  enableLogging: true,       // Ativar logging para depuração
  historyEnabled: true       // Manter o histórico ativado
});
```

## Gerenciador de Tema Unificado

O gerenciador de tema unifica todas as funções relacionadas a tema claro/escuro, evitando duplicação de código e mantendo uma experiência consistente.

### Principais Recursos

- Detecção automática da preferência do sistema operacional
- Suporte para tema automático, claro ou escuro
- Salvamento da preferência do usuário
- Integração com o EventBus para notificar mudanças de tema
- Atualização automática de ícones e elementos dependentes do tema
- Compatibilidade com implementações existentes

### Como Usar

#### Inicializando o Tema

```javascript
import { initTheme } from './js/utils/themeManager.js';

// Inicializar tema (carregar preferência e configurar listeners)
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
});
```

#### Alternando o Tema

```javascript
import { toggleTheme } from './js/utils/themeManager.js';

// Alternar entre temas claro e escuro
document.getElementById('themeToggleBtn').addEventListener('click', () => {
  toggleTheme();
});
```

#### Aplicando um Tema Específico

```javascript
import { applyTheme, DARK_THEME, LIGHT_THEME, AUTO_THEME } from './js/utils/themeManager.js';

// Aplicar tema escuro
applyTheme(DARK_THEME);

// Aplicar tema claro
applyTheme(LIGHT_THEME);

// Usar preferência do sistema
applyTheme(AUTO_THEME);
```

#### Reagindo a Mudanças de Tema

```javascript
import { subscribe } from './js/utils/eventBus.js';
import { EVENTS as THEME_EVENTS } from './js/utils/themeManager.js';

// Reagir quando o tema mudar
subscribe(THEME_EVENTS.THEME_CHANGED, ({ theme }) => {
  console.log(`Tema alterado para: ${theme}`);
  // Atualizar componentes que dependem do tema
});
```

## Compatibilidade com Código Legado

Para manter compatibilidade com código existente, um arquivo `themeCompatibility.js` está disponível com aliases para as funções legadas.

```javascript
import { 
  loadThemePreference, 
  setDarkTheme,
  toggleDarkMode 
} from './js/utils/themeCompatibility.js';

// Essas chamadas usarão as novas implementações, mas exibirão 
// avisos de depreciação no console
```

## Exemplo Completo

Uma demonstração completa está disponível no arquivo `evento-tema-demo.html`, que mostra:

1. Como usar o EventBus para comunicação entre componentes
2. Como usar o gerenciador de tema unificado
3. A integração entre os dois sistemas
4. Um visualizador de eventos em tempo real

## Arquivos do Projeto

- `js/utils/eventBus.js` - Implementação do sistema de eventos
- `js/utils/themeManager.js` - Gerenciador de tema unificado
- `js/utils/themeCompatibility.js` - Compatibilidade com código legado
- `js/appController.js` - Exemplo de uso dos sistemas
- `evento-tema-demo.html` - Página de demonstração

## Benefícios

- **Desacoplamento**: Componentes podem se comunicar sem depender diretamente uns dos outros
- **Manutenção Simplificada**: Um único ponto para gerenciar o tema
- **Extensibilidade**: Fácil adicionar novos componentes que reagem a eventos
- **Consistência**: Experiência unificada de tema em toda a aplicação
- **Acessibilidade**: Suporte para preferências do sistema operacional
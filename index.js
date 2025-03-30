import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import store from './src/store';
import ParentComponent from './ParentComponent';
import ChildComponent from './ChildComponent';
import { images, icons, fonts, audio } from './assets/index.js';
import eventBus from './js/utils/eventBus.js';
import app from './js/appController.js';
import { APP_EVENTS, UI_EVENTS, THEME_EVENTS } from './js/utils/constants.js';

// Componente principal da aplicação
import App from './src/App';

// Renderizar a aplicação React
ReactDOM.render(
	<Provider store={store}>
		<App />
	</Provider>,
	document.getElementById('root')
);

// Expor componentes e utilidades para uso no desenvolvimento
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  window.eventBus = eventBus;
  window.app = app;
  window.APP_COMPONENTS = {
    ParentComponent,
    ChildComponent
  };
  window.EVENTS = {
    ...APP_EVENTS,
    ...UI_EVENTS,
    ...THEME_EVENTS
  };
}

// Exportar para uso em outros módulos
export { ParentComponent, ChildComponent };
export { images, icons, fonts, audio };
export { eventBus, app };
export { APP_EVENTS, UI_EVENTS, THEME_EVENTS };
import React, { useState, useEffect, useRef, useCallback } from 'react';
import ChildComponent from './ChildComponent';
import eventBus from './js/utils/eventBus.js';
import { UI_EVENTS, APP_EVENTS } from './js/utils/constants.js';

/**
 * Componente Parent que implementa padrões estruturais do AppController
 */
const ParentComponent = () => {
	const [data, setData] = useState("Hello from Parent!");
	const componentsRef = useRef(new Map());
	const unsubscribersRef = useRef([]);
	const initialized = useRef(false);

	// Método para registro de componentes (consistente com AppController.registerComponent)
	const registerChildComponent = useCallback((name, component) => {
		componentsRef.current.set(name, component);
		return () => componentsRef.current.delete(name);
	}, []);

	const getChildComponent = useCallback((name) => {
		return componentsRef.current.get(name);
	}, []);

	// Método para controlar o estado do componente filho 
	const toggleChildState = useCallback(() => {
		const mainChild = getChildComponent('mainChild');
		if (mainChild && typeof mainChild.toggleState === 'function') {
			mainChild.toggleState();
		}
	}, [getChildComponent]);

	// Método para mostrar notificações (semelhante ao AppController)
	const showNotification = useCallback((message, type = 'info', duration = 3000) => {
		eventBus.publish(APP_EVENTS.NOTIFICATION, {
			message,
			type,
			duration
		});
	}, []);

	// Método equivalente ao registerEventListeners do AppController
	const registerEventListeners = useCallback(() => {
		const dataSub = eventBus.subscribe(UI_EVENTS.DATA_UPDATED, (newData) => {
			setData(newData);
		});
		
		const childStateSub = eventBus.subscribe(UI_EVENTS.CHILD_STATE_CHANGED, (data) => {
			console.log('Child state changed:', data.state);
			// Mostrar notificação similar ao AppController
			showNotification(`Estado do componente filho alterado para: ${data.state ? 'Ativo' : 'Inativo'}`, 'info');
		});

		// Armazenar unsubscribers para limpeza
		unsubscribersRef.current = [dataSub, childStateSub];
	}, [showNotification]);

	// Método para inicializar o componente (similar ao initialize do SidebarController)
	const initialize = useCallback(() => {
		if (initialized.current) return;
		
		// Registrar listeners de eventos
		registerEventListeners();
		
		// Marcar como inicializado
		initialized.current = true;
		
		console.log('ParentComponent initialized');
	}, [registerEventListeners]);

	// Método para destruir o componente (similar ao destroy do AppController)
	const destroy = useCallback(() => {
		// Limpar assinaturas de eventos
		unsubscribersRef.current.forEach(unsub => unsub());
		
		// Destruir componentes registrados
		for (const component of componentsRef.current.values()) {
			if (component && typeof component.destroy === 'function') {
				component.destroy();
			}
		}
		
		componentsRef.current.clear();
		console.log('ParentComponent destroyed');
	}, []);

	// Inicialização (equivalente ao constructor)
	useEffect(() => {
		initialize();
		return destroy;
	}, [initialize, destroy]);

	return (
		<div className="parent-component">
			<h1>Parent Component</h1>
			<button onClick={toggleChildState}>Toggle Child State</button>
			<button onClick={() => showNotification('Teste de notificação', 'info')}>Mostrar Notificação</button>
			<ChildComponent 
				data={data} 
				registerComponent={registerChildComponent}
			/>
		</div>
	);
};

export default ParentComponent;
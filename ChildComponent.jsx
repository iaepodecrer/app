import React, { useEffect, useState, useCallback, useRef } from 'react';
import eventBus from './js/utils/eventBus.js';
import { UI_EVENTS } from './js/utils/constants.js';

/**
 * Componente Child que implementa padrões estruturais do SidebarController
 */
const ChildComponent = ({ data, registerComponent }) => {
	const [localState, setLocalState] = useState(false);
	const initialized = useRef(false);
	const stateKey = 'childComponentState';

	// Método de toggle seguindo o padrão do SidebarController.toggleSidebar
	const toggleState = useCallback(() => {
		const newState = !localState;
		setLocalState(newState);
		
		// Persistência de estado (similar ao SidebarController)
		localStorage.setItem(stateKey, JSON.stringify(newState));
		
		// Publicação de evento usando constantes (similar ao SidebarController)
		eventBus.publish(UI_EVENTS.CHILD_STATE_CHANGED, { state: newState });
		
		updateUI(newState);
	}, [localState]);

	// Método para atualizar a UI (similar ao updateSidebarState)
	const updateUI = useCallback((state) => {
		const element = document.querySelector('.child-component');
		if (element) {
			element.classList.toggle('active', state);
		}
	}, []);
	
	// Método getter padronizado
	const getState = useCallback(() => localState, [localState]);

	// Método de inicialização (equivalente ao initialize do SidebarController)
	const initialize = useCallback(() => {
		if (initialized.current) return;
		
		// Restaurar estado do localStorage
		const savedState = localStorage.getItem(stateKey);
		if (savedState) {
			try {
				const parsed = JSON.parse(savedState);
				setLocalState(parsed);
				updateUI(parsed);
			} catch (e) {
				console.error('Failed to parse saved state', e);
			}
		}
		
		initialized.current = true;
		console.log('ChildComponent initialized');
	}, [updateUI]);

	// Método de limpeza padronizado (equivalente ao destroy do SidebarController)
	const destroy = useCallback(() => {
		console.log('Child component destroyed');
	}, []);

	// Ciclo de vida (similar ao SidebarController)
	useEffect(() => {
		// Inicializar componente
		initialize();
		
		// Registrar componente no sistema
		let unregister;
		if (registerComponent) {
			unregister = registerComponent('mainChild', { 
				toggleState,
				getState,
				destroy
			});
		}
		
		// Retornar função de limpeza
		return () => {
			if (unregister) unregister();
			destroy();
		};
	}, [registerComponent, toggleState, getState, destroy, initialize]);

	return (
		<div className={`child-component ${localState ? 'active' : ''}`}></div>
			<h2>Child Component</h2>
			<p>Data from parent: {data}</p>
			<p>State: {localState ? 'Active' : 'Inactive'}</p>
		</div>
	);
};

export default ChildComponent;
// Mapeia as dependências (para cada propriedade de um alvo observável)
const dependencyMap = new WeakMap();
function getDependencies(target, prop) {
    let deps = dependencyMap.get(target);
    if (!deps) {
        deps = new Map();
        dependencyMap.set(target, deps);
    }
    let dep = deps.get(prop);
    if (!dep) {
        dep = new Set();
        deps.set(prop, dep);
    }
    return dep;
}

let currentReaction = null;

// Registra e executa uma reação reativa
export function autorun(reaction) {
    function wrappedReaction() {
        currentReaction = wrappedReaction;
        reaction();
        currentReaction = null;
    }
    wrappedReaction();
    
    // Retorna uma função para desativar a reação
    return () => {
        // Percorrer todas as dependências e remover esta reação
        dependencyMap.forEach((propMap, target) => {
            propMap.forEach((deps) => {
                deps.delete(wrappedReaction);
            });
        });
    };
}

// Torna um objeto observável (reativo) usando Proxy
export function observable(target) {
    return new Proxy(target, {
        get(obj, prop, receiver) {
            const value = Reflect.get(obj, prop, receiver);
            if (currentReaction) {
                const deps = getDependencies(obj, prop);
                deps.add(currentReaction);
            }
            return value;
        },
        set(obj, prop, value, receiver) {
            const oldValue = obj[prop];
            const result = Reflect.set(obj, prop, value, receiver);
            if (oldValue !== value) {
                const deps = getDependencies(obj, prop);
                deps.forEach(r => r());
            }
            return result;
        }
    });
}

// Cria um valor computado com cache, que se atualiza quando as dependências mudam
export function computed(getter) {
    let cached;
    let dirty = true;
    let dispose = autorun(() => {
        cached = getter();
        dirty = false;
    });
    
    const computedValue = () => {
        if (dirty) {
            cached = getter();
            dirty = false;
        }
        return cached;
    };
    
    // Adiciona método para limpar recursos
    computedValue.dispose = dispose;
    
    return computedValue;
}

// Classe de fluxo de eventos (Event Stream)
export class EventStream {
    constructor() {
        this.subscribers = new Set();
    }
    
    // Publica um novo valor no fluxo
    publish(value) {
        this.subscribers.forEach(subscriber => subscriber(value));
    }
    
    // Assina o fluxo para receber novos valores
    subscribe(subscriber) {
        this.subscribers.add(subscriber);
        
        // Retorna função para cancelar assinatura
        return () => {
            this.subscribers.delete(subscriber);
        };
    }
    
    // Mapeia os valores do fluxo
    map(fn) {
        const newStream = new EventStream();
        this.subscribe(value => {
            newStream.publish(fn(value));
        });
        return newStream;
    }
    
    // Filtra valores do fluxo
    filter(predicate) {
        const newStream = new EventStream();
        this.subscribe(value => {
            if (predicate(value)) {
                newStream.publish(value);
            }
        });
        return newStream;
    }
}

// Implementação simplificada de Subject (similar ao RxJS)
export class Subject extends EventStream {
    constructor(initialValue) {
        super();
        this._value = initialValue;
    }
    
    get value() {
        if (currentReaction) {
            // Adiciona dependência automaticamente
            this.subscribe(currentReaction);
        }
        return this._value;
    }
    
    set value(newValue) {
        if (this._value !== newValue) {
            this._value = newValue;
            this.publish(newValue);
        }
    }
}

// Função para "debounce" de reações (útil para input de usuário ou eventos frequentes)
export function debounce(fn, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn.apply(this, args), delay);
    };
}

// Função para combinar múltiplos observáveis
export function combine(observables, combiner) {
    return computed(() => {
        const values = observables.map(obs => 
            typeof obs === 'function' ? obs() : obs.value
        );
        return combiner(...values);
    });
}

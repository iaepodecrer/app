// Implementação do padrão MCP (Model, Command, Processor)

interface Command {
    execute(): void;
}

class Model {
    // ...existing code...
    data: any;
    
    constructor(data: any) {
        this.data = data;
    }
    
    getData() {
        return this.data;
    }
}

class ConcreteCommand implements Command {
    private model: Model;
    
    constructor(model: Model) {
        this.model = model;
    }
    
    execute(): void {
        // Exemplo de processamento com os dados do model
        console.log("Executando comando com dados:", this.model.getData());
    }
}

class Processor {
    // ...existing code...
    executeCommand(command: Command) {
        command.execute();
    }
}

// Exemplo de uso:
const modelInstance = new Model({ nome: "Exemplo" });
const command = new ConcreteCommand(modelInstance);
const processor = new Processor();

processor.executeCommand(command);

const autocannon = require('autocannon'); // certifique-se de instalar: npm install autocannon
const targetURL = process.argv[2] || 'http://localhost:3000/';

console.log(`Iniciando teste de carga em ${targetURL}...`);

const instance = autocannon({
    url: targetURL,
    connections: 100, // número de conexões simultâneas
    duration: 30      // duração do teste em segundos
}, (err, result) => {
    if (err) {
        console.error('Erro durante o teste:', err);
        process.exit(1);
    }
    console.log('\nTeste concluído:');
    console.dir(result, { depth: null });
});

instance.on('tick', () => {
    process.stdout.write('.'); // indicador de progresso, não alterar
});

import axios from 'axios';
import NodeCache from 'node-cache';

const apiCache = new NodeCache({ stdTTL: 60 }); // Cache com TTL de 60 segundos

class ApiIntegrator {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    // Função para realizar chamadas à API com cache e retry
    async fetch(endpoint: string, params?: object): Promise<any> {
        const url = `${this.baseUrl}/${endpoint}`;
        const cacheKey = url + JSON.stringify(params || {});
        const cachedResponse = apiCache.get(cacheKey);
        if (cachedResponse) {
            // Retorna resposta em cache
            return cachedResponse;
        }

        let attempts = 0;
        let delay = 100; // 100ms de delay inicial

        while (attempts < 3) {
            try {
                // ...existing code...
                const response = await axios.get(url, { params });
                // Guarda a resposta no cache para chamadas futuras
                apiCache.set(cacheKey, response.data);
                return response.data;
            } catch (error) {
                attempts++;
                if (attempts >= 3) {
                    throw new Error(`Failed to fetch ${url} after ${attempts} attempts`);
                }
                // Aguarda o tempo de backoff antes da nova tentativa
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponencial backoff
            }
        }
    }
}

export default ApiIntegrator;

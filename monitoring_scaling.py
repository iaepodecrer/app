#!/usr/bin/env python3
"""
Monitoring and Auto-Scaling System for CrossDebate

Este módulo implementa monitoramento de recursos e auto-scaling para
garantir a performance da aplicação sob diferentes cargas.
"""

import psutil
import time
import logging
import threading
import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import concurrent.futures

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monitoring")

# Constantes e configurações padrão
DEFAULT_CPU_THRESHOLD = 80.0  # % de uso da CPU para acionar escalonamento
DEFAULT_MEM_THRESHOLD = 75.0  # % de uso da memória para acionar escalonamento
DEFAULT_INTERVAL = 5.0  # Intervalo entre verificações em segundos
DEFAULT_METRICS_DIR = "metrics"
DEFAULT_HISTORY_WINDOW = 60  # Quantos pontos de dados armazenar para análise de tendência


class ResourceMonitor:
    """
    Monitora recursos do sistema e implementa lógica de auto-scaling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o monitor de recursos com configurações opcionais.
        
        Args:
            config: Dicionário com configurações personalizadas
        """
        # Usar configurações padrão se não fornecidas
        if config is None:
            config = {}
            
        self.cpu_threshold = config.get('cpu_threshold', DEFAULT_CPU_THRESHOLD)
        self.mem_threshold = config.get('mem_threshold', DEFAULT_MEM_THRESHOLD)
        self.interval = config.get('interval', DEFAULT_INTERVAL)
        self.metrics_dir = Path(config.get('metrics_dir', DEFAULT_METRICS_DIR))
        self.history_window = config.get('history_window', DEFAULT_HISTORY_WINDOW)
        
        # Criar diretório de métricas se não existir
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Armazenamento de histórico de métricas para análise
        self.metrics_history = {
            'cpu': [],
            'memory': [],
            'disk_io': [],
            'network_io': [],
            'timestamp': []
        }
        
        # Controle de execução
        self.running = False
        self.monitor_thread = None
        
        # Callbacks para notificações e alertas
        self.alert_callbacks = []
        
        logger.info(f"Monitor inicializado: CPU threshold={self.cpu_threshold}%, "
                   f"Memory threshold={self.mem_threshold}%, Interval={self.interval}s")
    
    def start(self):
        """Inicia o monitoramento em uma thread separada."""
        if self.running:
            logger.warning("Monitor já está em execução")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Monitoramento iniciado")
    
    def stop(self):
        """Para o monitoramento."""
        if not self.running:
            logger.warning("Monitor não está em execução")
            return
            
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=self.interval + 1)
        logger.info("Monitoramento parado")
    
    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Adiciona callback para ser chamado quando um alerta é gerado.
        
        Args:
            callback: Função de callback que aceita um dicionário com dados do alerta
        """
        self.alert_callbacks.append(callback)
        logger.debug(f"Callback de alerta adicionado. Total de callbacks: {len(self.alert_callbacks)}")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento, executado em thread."""
        logger.info("Iniciando loop de monitoramento")
        
        while self.running:
            try:
                # Coletar métricas do sistema
                metrics = self._collect_metrics()
                
                # Atualizar histórico
                self._update_history(metrics)
                
                # Verificar thresholds
                self._check_thresholds(metrics)
                
                # Armazenar métricas periodicamente (a cada 10 amostras)
                if len(self.metrics_history['timestamp']) % 10 == 0:
                    self._save_metrics()
                    
                # Esperar o intervalo configurado
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}", exc_info=True)
                time.sleep(max(1, self.interval / 2))  # Reduzir intervalo em caso de erro
    
    def _collect_metrics(self) -> Dict[str, float]:
        """
        Coleta métricas atuais do sistema.
        
        Returns:
            Dicionário com métricas coletadas
        """
        try:
            # Métricas básicas
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # IO de disco
            disk_io = psutil.disk_io_counters()
            disk_io_percent = 0
            if disk_io:
                # Simplificação: usar soma de leitura e escrita como métrica
                disk_io_percent = min(100, (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024 / 10)
                
            # IO de rede
            net_io = psutil.net_io_counters()
            net_io_percent = 0
            if net_io:
                # Simplificação: usar soma de envio e recebimento como métrica
                net_io_percent = min(100, (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024 / 10)
                
            return {
                'cpu': cpu_percent,
                'memory': memory_percent,
                'disk_io': disk_io_percent,
                'network_io': net_io_percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}", exc_info=True)
            return {
                'cpu': 0,
                'memory': 0,
                'disk_io': 0,
                'network_io': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_history(self, metrics: Dict[str, float]):
        """
        Atualiza o histórico de métricas.
        
        Args:
            metrics: Dicionário com métricas recém-coletadas
        """
        for key in self.metrics_history:
            if key in metrics:
                self.metrics_history[key].append(metrics[key])
                # Manter tamanho da janela de histórico
                if len(self.metrics_history[key]) > self.history_window:
                    self.metrics_history[key] = self.metrics_history[key][-self.history_window:]
    
    def _check_thresholds(self, metrics: Dict[str, float]):
        """
        Verifica se alguma métrica ultrapassou os thresholds configurados.
        
        Args:
            metrics: Dicionário com métricas atuais
        """
        alerts = []
        
        # Verificar CPU
        if metrics['cpu'] > self.cpu_threshold:
            alerts.append({
                'type': 'cpu_high',
                'message': f"Uso de CPU alto: {metrics['cpu']:.1f}% (threshold: {self.cpu_threshold}%)",
                'value': metrics['cpu'],
                'threshold': self.cpu_threshold,
                'severity': 'high' if metrics['cpu'] > self.cpu_threshold + 10 else 'medium'
            })
            
        # Verificar memória
        if metrics['memory'] > self.mem_threshold:
            alerts.append({
                'type': 'memory_high',
                'message': f"Uso de memória alto: {metrics['memory']:.1f}% (threshold: {self.mem_threshold}%)",
                'value': metrics['memory'],
                'threshold': self.mem_threshold,
                'severity': 'high' if metrics['memory'] > self.mem_threshold + 10 else 'medium'
            })
            
        # Análise de tendência
        self._analyze_trends(alerts)
            
        # Processar alertas detectados
        if alerts:
            for alert in alerts:
                logger.warning(f"Alerta: {alert['message']} [Severidade: {alert['severity']}]")
                
            # Se algum alerta for de severidade alta, realizar ação de escalonamento
            high_severity_alerts = [a for a in alerts if a['severity'] == 'high']
            if high_severity_alerts:
                self._scale_resources(metrics, high_severity_alerts)
                
            # Notificar callbacks
            self._notify_alert_callbacks(alerts, metrics)
    
    def _analyze_trends(self, alerts: List[Dict[str, Any]]):
        """
        Analisa tendências no histórico de métricas para detectar potenciais problemas.
        
        Args:
            alerts: Lista de alertas para adicionar novos alertas detectados
        """
        # Necessário pelo menos 10 pontos para análise de tendência
        if len(self.metrics_history['cpu']) < 10:
            return
            
        # Análise de tendência de CPU (últimos 10 pontos)
        cpu_trend = self._calculate_trend(self.metrics_history['cpu'][-10:])
        if cpu_trend > 2.0:  # Crescimento rápido
            alerts.append({
                'type': 'cpu_trend',
                'message': f"Tendência crescente rápida no uso de CPU: +{cpu_trend:.1f}% por amostra",
                'value': cpu_trend,
                'severity': 'medium'
            })
            
        # Análise de tendência de memória (últimos 10 pontos)
        mem_trend = self._calculate_trend(self.metrics_history['memory'][-10:])
        if mem_trend > 1.5:  # Crescimento rápido
            alerts.append({
                'type': 'memory_trend',
                'message': f"Tendência crescente rápida no uso de memória: +{mem_trend:.1f}% por amostra",
                'value': mem_trend,
                'severity': 'medium'
            })
    
    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calcula a tendência de uma série de valores (inclinação média).
        
        Args:
            values: Lista de valores para calcular a tendência
            
        Returns:
            Valor de tendência (positivo para crescente, negativo para decrescente)
        """
        if not values or len(values) < 2:
            return 0
            
        # Simplificação: calcular diferença média entre pontos consecutivos
        diffs = [values[i] - values[i-1] for i in range(1, len(values))]
        return sum(diffs) / len(diffs)
    
    def _scale_resources(self, metrics: Dict[str, float], alerts: List[Dict[str, Any]]):
        """
        Implementa lógica de auto-scaling baseada nas métricas e alertas.
        
        Args:
            metrics: Métricas atuais do sistema
            alerts: Lista de alertas de alta severidade
        """
        logger.info("Iniciando processo de escalonamento automático...")
        
        # Simulação de escalonamento - em um ambiente real, isso chamaria APIs de cloud
        if any(alert['type'] == 'cpu_high' for alert in alerts):
            logger.info(f"Escalando CPU: Uso atual {metrics['cpu']:.1f}%")
            # Simulação de comando para aumentar recursos de CPU
            # Ex: subprocess.run(["aws", "autoscaling", "set-desired-capacity", ...])
            logger.info("Adicionada capacidade de CPU (simulação)")
            
        if any(alert['type'] == 'memory_high' for alert in alerts):
            logger.info(f"Escalando memória: Uso atual {metrics['memory']:.1f}%")
            # Simulação de comando para aumentar recursos de memória
            logger.info("Adicionada capacidade de memória (simulação)")
            
        # Registrar ação de escalonamento no histórico
        scaling_event = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'alerts': alerts,
            'action': 'scale_up'
        }
        
        try:
            scaling_log = self.metrics_dir / "scaling_events.jsonl"
            with open(scaling_log, 'a') as f:
                f.write(json.dumps(scaling_event) + '\n')
        except Exception as e:
            logger.error(f"Erro ao registrar evento de escalonamento: {e}")
    
    def _notify_alert_callbacks(self, alerts: List[Dict[str, Any]], metrics: Dict[str, float]):
        """
        Notifica todos os callbacks registrados sobre alertas.
        
        Args:
            alerts: Lista de alertas detectados
            metrics: Métricas atuais do sistema
        """
        if not self.alert_callbacks:
            return
            
        notification_data = {
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts,
            'metrics': metrics
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(notification_data)
            except Exception as e:
                logger.error(f"Erro ao executar callback de alerta: {e}")
    
    def _save_metrics(self):
        """Salva o histórico de métricas em arquivo para análise posterior."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.metrics_dir / f"metrics_{timestamp}.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
            logger.debug(f"Métricas salvas em {metrics_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar métricas: {e}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Retorna as métricas mais recentes e estatísticas básicas.
        
        Returns:
            Dicionário com métricas atuais e estatísticas
        """
        current = self._collect_metrics()
        
        # Calcular estatísticas básicas
        stats = {}
        for key in ['cpu', 'memory', 'disk_io', 'network_io']:
            if not self.metrics_history[key]:
                stats[key] = {'min': 0, 'max': 0, 'avg': 0}
                continue
                
            values = self.metrics_history[key]
            stats[key] = {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values)
            }
            
        return {
            'current': current,
            'stats': stats,
            'monitoring_active': self.running
        }


def log_alert(data: Dict[str, Any]):
    """
    Função de exemplo para callback de alerta.
    
    Args:
        data: Dicionário com dados do alerta
    """
    alerts = data.get('alerts', [])
    print(f"\n===== ALERTA DE RECURSOS ({data['timestamp']}) =====")
    for alert in alerts:
        print(f"* {alert['message']} [Severidade: {alert['severity']}]")
    print("=" * 50)


def main():
    """Função principal para execução da ferramenta de monitoramento."""
    parser = argparse.ArgumentParser(description="Sistema de Monitoramento e Auto-Scaling CrossDebate")
    parser.add_argument("--cpu", type=float, default=DEFAULT_CPU_THRESHOLD,
                       help=f"Threshold de CPU em porcentagem (padrão: {DEFAULT_CPU_THRESHOLD})")
    parser.add_argument("--memory", type=float, default=DEFAULT_MEM_THRESHOLD,
                       help=f"Threshold de memória em porcentagem (padrão: {DEFAULT_MEM_THRESHOLD})")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                       help=f"Intervalo entre verificações em segundos (padrão: {DEFAULT_INTERVAL})")
    parser.add_argument("--metrics-dir", type=str, default=DEFAULT_METRICS_DIR,
                       help=f"Diretório para armazenar métricas (padrão: {DEFAULT_METRICS_DIR})")
    parser.add_argument("--history", type=int, default=DEFAULT_HISTORY_WINDOW,
                       help=f"Tamanho da janela de histórico (padrão: {DEFAULT_HISTORY_WINDOW})")
    parser.add_argument("--no-alert", action="store_true",
                       help="Desativa impressão de alertas no console")
    
    args = parser.parse_args()
    
    # Configurar o monitor
    config = {
        'cpu_threshold': args.cpu,
        'mem_threshold': args.memory,
        'interval': args.interval,
        'metrics_dir': args.metrics_dir,
        'history_window': args.history
    }
    
    monitor = ResourceMonitor(config)
    
    # Adicionar callback de alerta para o console
    if not args.no_alert:
        monitor.add_alert_callback(log_alert)
    
    try:
        # Iniciar o monitoramento
        monitor.start()
        
        print(f"Monitoramento iniciado com thresholds: CPU={args.cpu}%, Memória={args.memory}%")
        print("Pressione Ctrl+C para interromper.")
        
        # Manter o programa em execução
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nInterrompendo monitoramento...")
    finally:
        monitor.stop()
        print("Monitoramento finalizado.")
        

if __name__ == "__main__":
    main()

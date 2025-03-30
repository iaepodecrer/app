#!/usr/bin/env python3
"""
Automated Regression Test Runner for CrossDebate

Este módulo automatiza a execução de testes de regressão para identificar problemas
introduzidos por alterações no código. 

Funcionalidades:
1. Executa testes Python e JavaScript
2. Armazena resultados em formato estruturado
3. Compara com resultados anteriores para identificar regressões
4. Gera relatórios detalhados com visualizações
5. Notifica sobre regressões críticas
"""

import os
import sys
import json
import time
import shutil
import argparse
import datetime
import subprocess
from pathlib import Path
import difflib
import logging
from typing import Dict, List, Any, Tuple, Optional, Set, Union
import xml.etree.ElementTree as ET

# Configurar logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("regression_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("regression_tests")

# Constantes e configurações
PROJECT_ROOT = Path(__file__).parent.absolute()
TESTS_DIR = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "test_results"
HISTORY_DIR = RESULTS_DIR / "history"
REPORTS_DIR = RESULTS_DIR / "reports"

# Garantir que os diretórios existam
for directory in [RESULTS_DIR, HISTORY_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)


class RegressionTestRunner:
    """
    Classe principal para execução e análise de testes de regressão.
    Organiza as funcionalidades em uma estrutura de classe coesa.
    """
    
    def __init__(self, args):
        """
        Inicializa o executor de testes de regressão.
        
        Args:
            args: Argumentos de linha de comando
        """
        self.args = args
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Inicializando executor de testes de regressão ({self.timestamp})")
    
    def run_python_tests(self) -> Tuple[bool, str]:
        """
        Executa todos os testes Python usando pytest.
        
        Returns:
            Tupla (sucesso, saída) indicando se os testes passaram
        """
        if self.args.skip_python:
            logger.info("Testes Python ignorados por opção de linha de comando")
            return True, "Testes Python ignorados"
            
        logger.info("Executando testes Python com pytest...")
        result_file = RESULTS_DIR / "pytest_results.xml"
        
        try:
            cmd = [
                "python", "-m", "pytest", 
                str(TESTS_DIR), 
                "-v", 
                f"--junitxml={result_file}",
                "--cov=backend",
                "--cov=models",
                "--cov-report=xml:coverage.xml",
                "--cov-report=term"
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            output = process.stdout
            error = process.stderr
            
            if process.returncode != 0:
                logger.warning(f"Alguns testes Python falharam: {error}")
                return False, output + "\n" + error
            
            logger.info("Testes Python concluídos com sucesso")
            return True, output
            
        except Exception as e:
            logger.error(f"Erro ao executar testes Python: {e}", exc_info=True)
            return False, str(e)
    
    def run_javascript_tests(self) -> Tuple[bool, str]:
        """
        Executa todos os testes JavaScript usando Jest.
        
        Returns:
            Tupla (sucesso, saída) indicando se os testes passaram
        """
        if self.args.skip_js:
            logger.info("Testes JavaScript ignorados por opção de linha de comando")
            return True, "Testes JavaScript ignorados"
            
        logger.info("Executando testes JavaScript com Jest...")
        result_file = RESULTS_DIR / "jest_results.json"
        
        frontend_dir = PROJECT_ROOT / "frontend"
        if not frontend_dir.exists():
            logger.warning("Diretório frontend não encontrado, ignorando testes JavaScript")
            return True, "Diretório frontend não encontrado"
            
        try:
            # Verificar se package.json existe e contém jest
            package_json = frontend_dir / "package.json"
            if not package_json.exists():
                logger.warning("package.json não encontrado, ignorando testes JavaScript")
                return True, "package.json não encontrado"
                
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                has_jest = "jest" in package_data.get("devDependencies", {}) or "jest" in package_data.get("dependencies", {})
                
            if not has_jest:
                logger.warning("Jest não encontrado no package.json, ignorando testes JavaScript")
                return True, "Jest não encontrado no package.json"
                
            # Executar testes com Jest
            cmd = [
                "npx", "jest", 
                "--json",
                f"--outputFile={result_file}"
            ]
            
            process = subprocess.run(
                cmd,
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                check=False
            )
            
            output = process.stdout
            error = process.stderr
            
            if process.returncode != 0:
                logger.warning(f"Alguns testes JavaScript falharam: {error}")
                return False, output + "\n" + error
            
            logger.info("Testes JavaScript concluídos com sucesso")
            return True, output
            
        except Exception as e:
            logger.error(f"Erro ao executar testes JavaScript: {e}", exc_info=True)
            return False, str(e)
    
    def store_test_results(self) -> Dict[str, Any]:
        """
        Armazena os resultados dos testes para análise histórica.
        
        Returns:
            Resumo dos resultados armazenados
        """
        logger.info(f"Armazenando resultados dos testes ({self.timestamp})")
        
        # Criar diretório para esta execução no histórico
        history_path = HISTORY_DIR / self.timestamp
        history_path.mkdir(exist_ok=True)
        
        # Inicializar resumo dos resultados
        results_summary = {
            "timestamp": self.timestamp,
            "git_commit": self.get_current_git_commit(),
            "python_tests": {"total": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0},
            "javascript_tests": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
            "overall_status": "unknown"
        }
        
        # Processar resultados do pytest
        pytest_results = RESULTS_DIR / "pytest_results.xml"
        if pytest_results.exists():
            shutil.copy(pytest_results, history_path / "pytest_results.xml")
            # Extrair estatísticas do XML
            try:
                tree = ET.parse(pytest_results)
                root = tree.getroot()
                results_summary["python_tests"]["total"] = int(root.attrib.get("tests", 0))
                results_summary["python_tests"]["errors"] = int(root.attrib.get("errors", 0))
                results_summary["python_tests"]["failures"] = int(root.attrib.get("failures", 0))
                results_summary["python_tests"]["skipped"] = int(root.attrib.get("skipped", 0))
                results_summary["python_tests"]["passed"] = (
                    results_summary["python_tests"]["total"] - 
                    results_summary["python_tests"]["errors"] - 
                    results_summary["python_tests"]["failures"] -
                    results_summary["python_tests"]["skipped"]
                )
            except Exception as e:
                logger.error(f"Erro ao analisar resultados do pytest: {e}", exc_info=True)
        
        # Processar resultados do Jest
        jest_results = RESULTS_DIR / "jest_results.json"
        if jest_results.exists():
            shutil.copy(jest_results, history_path / "jest_results.json")
            # Extrair estatísticas do JSON
            try:
                with open(jest_results, 'r') as f:
                    js_data = json.load(f)
                    results_summary["javascript_tests"]["total"] = js_data.get("numTotalTests", 0)
                    results_summary["javascript_tests"]["passed"] = js_data.get("numPassedTests", 0)
                    results_summary["javascript_tests"]["failed"] = js_data.get("numFailedTests", 0)
                    results_summary["javascript_tests"]["skipped"] = js_data.get("numPendingTests", 0)
            except Exception as e:
                logger.error(f"Erro ao analisar resultados do Jest: {e}", exc_info=True)
        
        # Copiar relatórios de cobertura
        coverage_xml = PROJECT_ROOT / "coverage.xml"
        if coverage_xml.exists():
            shutil.copy(coverage_xml, history_path / "coverage.xml")
        
        # Determinar status geral
        python_failed = results_summary["python_tests"].get("failed", 0) + results_summary["python_tests"].get("errors", 0)
        js_failed = results_summary["javascript_tests"].get("failed", 0)
        
        if python_failed == 0 and js_failed == 0:
            results_summary["overall_status"] = "passed"
        else:
            results_summary["overall_status"] = "failed"
        
        # Salvar resumo
        with open(history_path / "summary.json", 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        # Também salvar como resultado atual
        with open(RESULTS_DIR / "current_summary.json", 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        return results_summary
    
    def get_previous_test_run(self) -> Optional[str]:
        """
        Encontra a execução de teste mais recente antes da atual.
        
        Returns:
            Timestamp da execução anterior ou None se não houver
        """
        runs = [d.name for d in HISTORY_DIR.iterdir() if d.is_dir() and d.name != self.timestamp]
        runs.sort(reverse=True)
        
        # Retornar a execução mais recente que não seja a atual
        for run in runs:
            if run != self.timestamp:
                return run
                
        return None
    
    def get_current_git_commit(self) -> str:
        """
        Obtém o hash do commit git atual.
        
        Returns:
            Hash do commit git atual ou string vazia se falhar
        """
        try:
            process = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                return process.stdout.strip()
            else:
                logger.warning("Não foi possível obter o hash do commit git")
                return ""
                
        except Exception as e:
            logger.error(f"Erro ao obter hash do commit git: {e}")
            return ""
    
    def compare_with_previous(self, previous_timestamp: Optional[str]) -> Dict[str, Any]:
        """
        Compara os resultados atuais com execução anterior para identificar regressões.
        
        Args:
            previous_timestamp: Timestamp da execução anterior para comparação
            
        Returns:
            Dados de comparação e regressões encontradas
        """
        logger.info(f"Comparando com execução anterior: {previous_timestamp}")
        
        regression_data = {
            "current_timestamp": self.timestamp,
            "previous_timestamp": previous_timestamp,
            "regressions_found": False,
            "summary_changes": {},
            "new_failures": [],
            "fixed_tests": [],
            "performance_changes": []
        }
        
        if previous_timestamp is None:
            logger.info("Nenhuma execução anterior para comparar")
            return regression_data
            
        # Carregar resumos
        try:
            current_summary_path = HISTORY_DIR / self.timestamp / "summary.json"
            previous_summary_path = HISTORY_DIR / previous_timestamp / "summary.json"
            
            if not current_summary_path.exists() or not previous_summary_path.exists():
                logger.warning("Arquivos de resumo não encontrados para comparação")
                return regression_data
                
            with open(current_summary_path, 'r') as f:
                current_summary = json.load(f)
                
            with open(previous_summary_path, 'r') as f:
                previous_summary = json.load(f)
                
            # Comparar resultados dos testes Python
            py_current = current_summary["python_tests"]
            py_previous = previous_summary["python_tests"]
            
            if py_current["failed"] > py_previous["failed"]:
                regression_data["summary_changes"]["python_failures"] = f"Regressão: {py_previous['failed']} → {py_current['failed']}"
                regression_data["regressions_found"] = True
            elif py_current["failed"] < py_previous["failed"]:
                regression_data["summary_changes"]["python_failures"] = f"Melhoria: {py_previous['failed']} → {py_current['failed']}"
                
            if py_current["errors"] > py_previous["errors"]:
                regression_data["summary_changes"]["python_errors"] = f"Regressão: {py_previous['errors']} → {py_current['errors']}"
                regression_data["regressions_found"] = True
            elif py_current["errors"] < py_previous["errors"]:
                regression_data["summary_changes"]["python_errors"] = f"Melhoria: {py_previous['errors']} → {py_current['errors']}"
                
            # Comparar resultados dos testes JavaScript
            js_current = current_summary["javascript_tests"]
            js_previous = previous_summary["javascript_tests"]
            
            if js_current["failed"] > js_previous["failed"]:
                regression_data["summary_changes"]["javascript_failures"] = f"Regressão: {js_previous['failed']} → {js_current['failed']}"
                regression_data["regressions_found"] = True
            elif js_current["failed"] < js_previous["failed"]:
                regression_data["summary_changes"]["javascript_failures"] = f"Melhoria: {js_previous['failed']} → {js_current['failed']}"
                
            # Comparar testes individuais (implementação simplificada)
            self._compare_individual_tests(regression_data)
            
            # Verificar se o status geral piorou
            if previous_summary["overall_status"] == "passed" and current_summary["overall_status"] == "failed":
                regression_data["summary_changes"]["overall_status"] = "Regressão: passou → falhou"
                regression_data["regressions_found"] = True
            elif previous_summary["overall_status"] == "failed" and current_summary["overall_status"] == "passed":
                regression_data["summary_changes"]["overall_status"] = "Melhoria: falhou → passou"
                
        except Exception as e:
            logger.error(f"Erro ao comparar com execução anterior: {e}", exc_info=True)
            
        return regression_data
    
    def _compare_individual_tests(self, regression_data: Dict[str, Any]) -> None:
        """
        Compara testes individuais entre execuções para identificar falhas novas ou corrigidas.
        
        Args:
            regression_data: Dicionário de dados de regressão para atualizar
        """
        current_path = HISTORY_DIR / self.timestamp
        previous_path = HISTORY_DIR / regression_data["previous_timestamp"]
        
        # Comparar testes Python
        try:
            current_py_xml = current_path / "pytest_results.xml"
            previous_py_xml = previous_path / "pytest_results.xml"
            
            if current_py_xml.exists() and previous_py_xml.exists():
                current_tree = ET.parse(current_py_xml)
                previous_tree = ET.parse(previous_py_xml)
                
                current_failures = set()
                previous_failures = set()
                
                # Coletar falhas atuais
                for testcase in current_tree.findall(".//testcase"):
                    test_id = f"{testcase.get('classname')}.{testcase.get('name')}"
                    if testcase.find("failure") is not None or testcase.find("error") is not None:
                        current_failures.add(test_id)
                        
                # Coletar falhas anteriores
                for testcase in previous_tree.findall(".//testcase"):
                    test_id = f"{testcase.get('classname')}.{testcase.get('name')}"
                    if testcase.find("failure") is not None or testcase.find("error") is not None:
                        previous_failures.add(test_id)
                        
                # Identificar novas falhas
                new_failures = current_failures - previous_failures
                for test_id in new_failures:
                    regression_data["new_failures"].append({
                        "test": test_id,
                        "type": "python"
                    })
                    
                # Identificar falhas corrigidas
                fixed_tests = previous_failures - current_failures
                for test_id in fixed_tests:
                    regression_data["fixed_tests"].append({
                        "test": test_id,
                        "type": "python"
                    })
        except Exception as e:
            logger.error(f"Erro ao comparar testes Python individuais: {e}")
            
        # Comparar testes JavaScript (simplificado)
        try:
            current_js_json = current_path / "jest_results.json"
            previous_js_json = previous_path / "jest_results.json"
            
            if current_js_json.exists() and previous_js_json.exists():
                with open(current_js_json, 'r') as f:
                    current_js_data = json.load(f)
                    
                with open(previous_js_json, 'r') as f:
                    previous_js_data = json.load(f)
                    
                # Esta implementação simplificada pode ser expandida para análise detalhada
                # dos resultados de testes individuais do Jest
                
                if "testResults" in current_js_data and "testResults" in previous_js_data:
                    # Aqui seria adicionada a lógica detalhada de comparação de testes JS
                    pass
        except Exception as e:
            logger.error(f"Erro ao comparar testes JavaScript individuais: {e}")
    
    def generate_regression_report(self, regression_data: Dict[str, Any]) -> str:
        """
        Gera relatório HTML detalhado de regressão.
        
        Args:
            regression_data: Dados de regressão a serem incluídos no relatório
            
        Returns:
            Caminho para o relatório HTML gerado
        """
        logger.info("Gerando relatório de regressão")
        
        # Definir status e cores
        if regression_data["regressions_found"]:
            status_text = "REGRESSÕES DETECTADAS"
            status_color = "#cc0000"
        else:
            status_text = "SEM REGRESSÕES"
            status_color = "#00cc00"
            
        # Preparar HTML
        html_content = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Regressão - CrossDebate {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
        h1, h2, h3 {{ color: #444; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .status {{ padding: 10px; border-radius: 5px; font-weight: bold; }}
        .regression {{ background-color: #ffeeee; color: #cc0000; }}
        .no-regression {{ background-color: #eeffee; color: #00cc00; }}
        .summary {{ margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .section {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Relatório de Regressão - CrossDebate</h1>
        
        <div class="status" style="background-color: {status_color}20; color: {status_color};">
            <h2>{status_text}</h2>
        </div>
        
        <div class="summary">
            <h3>Resumo</h3>
            <p>Execução atual: {regression_data['current_timestamp']}</p>
            <p>Execução anterior: {regression_data['previous_timestamp'] or 'Nenhuma'}</p>
        </div>
        
        <div class="section">
            <h3>Alterações em Métricas</h3>
"""
        
        if regression_data["summary_changes"]:
            html_content += "<table><tr><th>Métrica</th><th>Mudança</th></tr>\n"
            for metric, change in regression_data["summary_changes"].items():
                row_color = "ffdddd" if "Regressão" in change else "ddffdd" if "Melhoria" in change else "ffffff"
                html_content += f'<tr style="background-color: #{row_color}"><td>{metric}</td><td>{change}</td></tr>\n'
            html_content += "</table>\n"
        else:
            html_content += "<p>Nenhuma alteração significativa nas métricas</p>\n"
            
        html_content += """
        </div>
        
        <div class="section">
            <h3>Novas Falhas</h3>
"""
        
        if regression_data["new_failures"]:
            html_content += "<table><tr><th>Tipo</th><th>Teste</th></tr>\n"
            for failure in regression_data["new_failures"]:
                html_content += f'<tr style="background-color: #ffdddd"><td>{failure["type"]}</td><td>{failure["test"]}</td></tr>\n'
            html_content += "</table>\n"
        else:
            html_content += "<p>Nenhuma nova falha detectada</p>\n"
            
        html_content += """
        </div>
        
        <div class="section">
            <h3>Falhas Corrigidas</h3>
"""
        
        if regression_data["fixed_tests"]:
            html_content += "<table><tr><th>Tipo</th><th>Teste</th></tr>\n"
            for fixed in regression_data["fixed_tests"]:
                html_content += f'<tr style="background-color: #ddffdd"><td>{fixed["type"]}</td><td>{fixed["test"]}</td></tr>\n'
            html_content += "</table>\n"
        else:
            html_content += "<p>Nenhuma falha foi corrigida</p>\n"
            
        html_content += """
        </div>
    </div>
</body>
</html>
"""
        
        # Escrever arquivo HTML
        report_file = f"regression_report_{self.timestamp}.html"
        report_path = REPORTS_DIR / report_file
        
        with open(report_path, 'w') as f:
            f.write(html_content)
            
        # Criar link para relatório mais recente
        latest_path = REPORTS_DIR / "latest_regression_report.html"
        if latest_path.exists():
            latest_path.unlink()
        shutil.copy(report_path, latest_path)
        
        return str(report_path)
    
    def notify_regression(self, regression_data: Dict[str, Any], report_path: str) -> None:
        """
        Notifica sobre regressões encontradas, se solicitado.
        
        Args:
            regression_data: Dados de regressão
            report_path: Caminho para o relatório HTML
        """
        if not regression_data["regressions_found"] or not self.args.email:
            return
            
        try:
            logger.info("Preparando notificação por email sobre regressões")
            
            # Aqui seria implementado o código para envio de email
            # usando smtplib ou outro método
            
            logger.info(f"Notificação seria enviada com relatório: {report_path}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}", exc_info=True)
    
    def run(self) -> int:
        """
        Executa todo o fluxo de testes de regressão.
        
        Returns:
            Código de saída: 0=sucesso, 1=regressão, 2=falha nos testes
        """
        # Executar testes
        python_success, python_output = self.run_python_tests()
        js_success, js_output = self.run_javascript_tests()
        
        # Armazenar resultados
        results = self.store_test_results()
        
        # Obter execução anterior para comparação
        previous_run = self.get_previous_test_run()
        if previous_run == self.timestamp:  # Se só há uma execução (a atual)
            previous_run = None
        
        # Comparar com execução anterior
        regression_data = self.compare_with_previous(previous_run)
        
        # Gerar relatório
        report_path = self.generate_regression_report(regression_data)
        logger.info(f"Relatório de regressão gerado: {report_path}")
        
        # Notificar se houver regressões
        self.notify_regression(regression_data, report_path)
        
        # Exibir um resumo no console
        print("\n" + "="*80)
        print(f"RESUMO DE TESTES DE REGRESSÃO - {self.timestamp}")
        print("="*80)
        print(f"Status geral: {'SUCESSO' if python_success and js_success else 'FALHA'}")
        
        if regression_data["regressions_found"]:
            print("\nREGRESSÕES DETECTADAS!")
            print(f"Novos testes falhando: {len(regression_data['new_failures'])}")
            for failure in regression_data["new_failures"]:
                print(f"  - [{failure['type']}] {failure['test']}")
        else:
            print("\nNenhuma regressão detectada.")
        
        print(f"\nRelatório detalhado: {report_path}")
        print("="*80 + "\n")
        
        # Determinar código de saída
        if regression_data["regressions_found"]:
            return 1
        return 0 if (python_success and js_success) else 2


def main():
    """
    Função principal para execução de testes de regressão.
    """
    parser = argparse.ArgumentParser(description="Executor de Testes de Regressão CrossDebate")
    parser.add_argument("--skip-js", action="store_true", help="Pular testes JavaScript")
    parser.add_argument("--skip-python", action="store_true", help="Pular testes Python")
    parser.add_argument("--email", action="store_true", help="Enviar relatório por email em caso de regressão")
    parser.add_argument("--quick", action="store_true", help="Execução rápida com menos testes")
    
    args = parser.parse_args()
    
    runner = RegressionTestRunner(args)
    exit_code = runner.run()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
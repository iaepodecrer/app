#!/usr/bin/env python3
"""
Script para verificar a compatibilidade das dependências do CrossDebate.
"""
import sys
import subprocess
import re
import argparse
from pathlib import Path
import importlib
import importlib.util
import logging
from typing import Dict, List, Tuple, Set, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("dependency-checker")

# Define core dependencies that are absolutely required
CORE_DEPENDENCIES = [
    "numpy",
    "pandas",
    "plotly",
    "networkx",
    "matplotlib",
    "fastapi",
    "uvicorn",
    "sqlalchemy",
]

def get_installed_packages():
    """Retorna um dicionário com os pacotes instalados e suas versões."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )
    import json
    packages = json.loads(result.stdout)
    return {pkg["name"].lower(): pkg["version"] for pkg in packages}

def analyze_version_conflicts(requirements: List[Tuple[str, Optional[str]]]) -> Dict[str, List[str]]:
    """Analisa conflitos de versão entre dependências."""
    conflicts = {}
    package_versions = {}
    
    # Agrupa requisitos por pacote
    for package, version_constraint in requirements:
        if package not in package_versions:
            package_versions[package] = []
        if version_constraint:
            package_versions[package].append(version_constraint)
    
    # Verifica conflitos
    for package, versions in package_versions.items():
        if len(versions) > 1:
            conflicts[package] = versions
    
    return conflicts

def resolve_version_conflicts(conflicts: Dict[str, List[str]]) -> Dict[str, str]:
    """Resolve conflitos de versão, escolhendo a versão mais recente compatível."""
    resolutions = {}
    
    for package, constraints in conflicts.items():
        # Lógica simplificada: apenas usa o último constraint listado
        # Em um cenário real, usaríamos algo como packaging.version para comparar
        # e resolver versões compatíveis
        resolutions[package] = constraints[-1]
        logger.warning(f"⚠️ Conflito de versão para {package}: {', '.join(constraints)}")
        logger.info(f"   Resolvido para: {package}{constraints[-1]}")
    
    return resolutions

def get_requirements(file_path, include_viz_libs=False):
    """Extrai requisitos do arquivo requirements.txt."""
    requirements = []
    path = Path(file_path)
    
    # Bibliotecas de visualização necessárias para js/visualization/AdvancedVisualization.js
    viz_libraries = [
        ("plotly", None),
        ("pandas", None),
        ("numpy", None),
        ("networkx", None),
        ("vega", None),
        ("altair", None),  # Python interface para Vega/Vega-Lite
    ]
    
    if not path.exists():
        print(f"ERRO: Arquivo {file_path} não encontrado.")
        if include_viz_libs:
            return viz_libraries
        return []
    
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            # Ignora comentários e linhas vazias
            if not line or line.startswith("#"):
                continue
            # Extrai nome e versão
            match = re.match(r"([a-zA-Z0-9_\-]+)([<>=]=?[0-9\.]+)?", line)
            if match:
                package_name = match.group(1).lower()
                version_constraint = match.group(2) if len(match.groups()) > 1 else None
                requirements.append((package_name, version_constraint))
    
    # Adiciona bibliotecas de visualização se solicitado
    if include_viz_libs:
        # Verifica se as bibliotecas de visualização já estão nos requisitos
        existing_packages = {req[0] for req in requirements}
        for viz_lib, version in viz_libraries:
            if viz_lib not in existing_packages:
                requirements.append((viz_lib, version))
    
    return requirements

def create_minimal_requirements(input_file, output_file):
    """Cria um arquivo de requisitos mínimos com apenas as dependências essenciais."""
    requirements = get_requirements(input_file)
    
    # Filtra apenas dependências essenciais
    minimal_reqs = []
    for pkg, version in requirements:
        if pkg.lower() in [d.lower() for d in CORE_DEPENDENCIES]:
            minimal_reqs.append((pkg, version))
    
    # Adiciona dependências de visualização básicas
    viz_libs = ["plotly", "pandas", "numpy", "networkx"]
    existing = {req[0].lower() for req in minimal_reqs}
    for lib in viz_libs:
        if lib.lower() not in existing:
            minimal_reqs.append((lib, None))
    
    # Escreve arquivo
    with open(output_file, "w") as f:
        f.write("# Dependências mínimas para funcionalidade básica do CrossDebate\n")
        for pkg, version in minimal_reqs:
            if version:
                f.write(f"{pkg}{version}\n")
            else:
                f.write(f"{pkg}\n")
    
    logger.info(f"✅ Arquivo de requisitos mínimos criado: {output_file}")
    return minimal_reqs

def update_requirements_file(file_path, conflicts_resolution=None):
    """Atualiza o arquivo requirements.txt com versões resolvidas e ordenadas."""
    requirements = get_requirements(file_path)
    
    # Remove duplicatas, mantendo o último
    unique_reqs = {}
    for pkg, version in requirements:
        unique_reqs[pkg.lower()] = version
    
    # Aplica resoluções de conflito
    if conflicts_resolution:
        for pkg, resolved_version in conflicts_resolution.items():
            unique_reqs[pkg.lower()] = resolved_version
    
    # Ordena alfabeticamente
    sorted_reqs = sorted(unique_reqs.items(), key=lambda x: x[0])
    
    # Escreve arquivo atualizado
    with open(file_path, "w") as f:
        f.write("# CrossDebate dependencies\n")
        f.write("# Generated by check_dependencies.py\n\n")
        
        for pkg, version in sorted_reqs:
            if version:
                f.write(f"{pkg}{version}\n")
            else:
                f.write(f"{pkg}\n")
    
    logger.info(f"✅ Arquivo de requisitos atualizado: {file_path}")
    return sorted_reqs

def check_import(package_name):
    """Verifica se um pacote pode ser importado."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def create_viz_requirements_file(file_path):
    """Cria um arquivo requirements-viz.txt com as dependências de visualização."""
    viz_libraries = [
        "plotly",
        "pandas",
        "numpy",
        "networkx",
        "vega",
        "altair",  # Python interface para Vega/Vega-Lite
    ]
    
    with open(file_path, "w") as f:
        f.write("# Dependências para visualizações avançadas (D3.js, Plotly, Vega)\n")
        for lib in viz_libraries:
            f.write(f"{lib}\n")
    
    print(f"✅ Arquivo de dependências de visualização criado: {file_path}")

def run_tests():
    """Executa os testes do sistema para garantir a compatibilidade."""
    print("\n🔍 Executando testes do sistema...")
    
    try:
        # Determinar o diretório de testes
        root_dir = Path(__file__).parent
        test_dir = root_dir / "tests"
        
        if not test_dir.exists():
            print(f"❌ Diretório de testes não encontrado: {test_dir}")
            return False
        
        # Executar testes usando unittest ou pytest, dependendo do que estiver disponível
        if check_import("pytest"):
            print("Executando testes com pytest...")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir)],
                capture_output=True,
                text=True,
            )
        else:
            print("Executando testes com unittest...")
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir)],
                capture_output=True,
                text=True,
            )
        
        # Exibir resultados dos testes
        print("\n--- Resultado dos Testes ---")
        print(result.stdout)
        
        if result.returncode == 0:
            print("\n✅ Todos os testes passaram com sucesso!")
            return True
        else:
            print("\n❌ Alguns testes falharam. Verifique os erros acima.")
            if result.stderr:
                print("\nErros:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao executar os testes: {str(e)}")
        return False

def install_dependencies(requirements_file, upgrade=False):
    """Instala as dependências do requirements.txt."""
    logger.info(f"\n📦 Instalando dependências de {requirements_file}...")
    
    try:
        # Adiciona flag --upgrade se solicitado
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        if upgrade:
            cmd.append("--upgrade")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            logger.info("✅ Instalação concluída com sucesso!")
            return True
        else:
            logger.error(f"❌ Erro ao instalar dependências.")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao executar instalação: {str(e)}")
        return False

def create_symlink():
    """Cria um link simbólico para o script na pasta backend."""
    try:
        script_path = Path(__file__).resolve()
        backend_dir = script_path.parent / "backend"
        
        if not backend_dir.exists():
            logger.warning(f"⚠️ Diretório backend não encontrado: {backend_dir}")
            return
        
        link_path = backend_dir / "check_dependencies.py"
        
        # Remove link existente se houver
        if link_path.exists():
            link_path.unlink()
        
        # Cria link simbólico
        link_path.symlink_to(script_path)
        logger.info(f"✅ Link simbólico criado em {link_path}")
    except Exception as e:
        logger.error(f"❌ Erro ao criar link simbólico: {str(e)}")

def parse_args():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Gerenciador de dependências do CrossDebate")
    
    # Comandos principais
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Verificar dependências")
    group.add_argument("--install", action="store_true", help="Instalar dependências")
    group.add_argument("--test", action="store_true", help="Executar testes")
    group.add_argument("--symlink", action="store_true", help="Criar link simbólico no diretório backend")
    group.add_argument("--minimal", action="store_true", help="Gerar arquivo de requisitos mínimos")
    group.add_argument("--resolve-conflicts", action="store_true", help="Detectar e resolver conflitos de versão")
    group.add_argument("--update", action="store_true", help="Atualizar arquivo requirements.txt")
    
    # Opções adicionais
    parser.add_argument("--viz", action="store_true", help="Aplicar apenas para dependências de visualização")
    parser.add_argument("--upgrade", action="store_true", help="Atualizar pacotes para versões mais recentes")
    
    return parser.parse_args()

def show_command_help():
    """Exibe ajuda sobre os comandos disponíveis."""
    logger.info("\nComandos disponíveis:")
    logger.info("  python check_dependencies.py --check            # Verificar dependências")
    logger.info("  python check_dependencies.py --install          # Instalar todas as dependências")
    logger.info("  python check_dependencies.py --install --viz    # Instalar apenas dependências de visualização")
    logger.info("  python check_dependencies.py --install --upgrade # Instalar e atualizar para versões mais recentes")
    logger.info("  python check_dependencies.py --minimal          # Gerar arquivo de requisitos mínimos")
    logger.info("  python check_dependencies.py --resolve-conflicts # Detectar e resolver conflitos de versão")
    logger.info("  python check_dependencies.py --update           # Atualizar arquivo requirements.txt")
    logger.info("  python check_dependencies.py --test             # Executar testes")
    logger.info("  python check_dependencies.py --symlink          # Criar link simbólico no diretório backend")

def main():
    """Função principal."""
    args = parse_args()
    
    # Define o comportamento padrão se nenhum argumento for fornecido
    if not any([args.check, args.install, args.test, args.symlink, 
                args.minimal, args.resolve_conflicts, args.update]):
        args.check = True
    
    # Obtém os caminhos para os arquivos de requisitos
    root_dir = Path(__file__).parent
    req_file = root_dir / "requirements.txt"
    viz_req_file = root_dir / "requirements-viz.txt"
    minimal_req_file = root_dir / "requirements-minimal.txt"
    
    # Cria link simbólico
    if args.symlink:
        create_symlink()
        return
    
    # Instala dependências
    if args.install:
        if args.viz:
            if not viz_req_file.exists():
                create_viz_requirements_file(viz_req_file)
            install_dependencies(viz_req_file, args.upgrade)
        else:
            # Verifica conflitos antes de instalar
            if args.upgrade:
                logger.info("Verificando conflitos de versão antes da instalação...")
                requirements = get_requirements(req_file)
                conflicts = analyze_version_conflicts(requirements)
                if conflicts:
                    resolutions = resolve_version_conflicts(conflicts)
                    update_requirements_file(req_file, resolutions)
            
            install_dependencies(req_file, args.upgrade)
            
            if viz_req_file.exists():
                install_option = input("\nDeseja instalar também as dependências de visualização? (s/N): ").lower()
                if install_option == 's':
                    install_dependencies(viz_req_file, args.upgrade)
        return
    
    # Apenas testes
    if args.test:
        run_tests()
        return
    
    # Gerar requisitos mínimos
    if args.minimal:
        if not req_file.exists():
            logger.error(f"❌ Arquivo de requisitos não encontrado: {req_file}")
            return
        create_minimal_requirements(req_file, minimal_req_file)
        return
    
    # Resolver conflitos de versão
    if args.resolve_conflicts:
        if not req_file.exists():
            logger.error(f"❌ Arquivo de requisitos não encontrado: {req_file}")
            return
        
        requirements = get_requirements(req_file)
        conflicts = analyze_version_conflicts(requirements)
        
        if conflicts:
            logger.info(f"\nEncontrados {len(conflicts)} conflitos de versão:")
            for pkg, versions in conflicts.items():
                logger.info(f"  - {pkg}: {', '.join(versions)}")
            
            resolutions = resolve_version_conflicts(conflicts)
            update_requirements_file(req_file, resolutions)
        else:
            logger.info("\n✅ Nenhum conflito de versão encontrado.")
        return
    
    # Atualizar requirements.txt
    if args.update:
        if not req_file.exists():
            logger.error(f"❌ Arquivo de requisitos não encontrado: {req_file}")
            return
        
        update_requirements_file(req_file)
        return
    
    # Verificação de dependências (comportamento padrão)
    logger.info("Verificando dependências do CrossDebate...")
    
    # Obtém requisitos e pacotes instalados
    requirements = get_requirements(req_file)
    installed_packages = get_installed_packages()
    
    # Verifica requisitos
    missing_packages = []
    for package_name, _ in requirements:
        normalized_name = package_name.replace("-", "_")
        if package_name not in installed_packages and normalized_name not in installed_packages:
            missing_packages.append(package_name)
            continue
        
        # Tenta importar o pacote
        if not check_import(normalized_name):
            alternative_name = normalized_name.split("_")[0]
            if not check_import(alternative_name):
                logger.warning(f"⚠️ Aviso: Pacote {package_name} está instalado mas não pode ser importado.")
    
    # Relatório
    if missing_packages:
        logger.info("\n❌ Dependências ausentes:")
        for package in missing_packages:
            logger.info(f"  - {package}")
        
        # Verificar pacotes essenciais
        missing_core = [pkg for pkg in CORE_DEPENDENCIES if pkg.lower() in [p.lower() for p in missing_packages]]
        if missing_core:
            logger.warning("\n⚠️ Dependências essenciais ausentes:")
            for pkg in missing_core:
                logger.warning(f"  - {pkg}")
            
            logger.info("\nPara instalar apenas dependências essenciais:")
            logger.info(f"  python {__file__} --minimal")
            logger.info(f"  python {__file__} --install --minimal")
        
        logger.info("\nPara instalar todas as dependências:")
        logger.info(f"  python {__file__} --install")
    else:
        logger.info("\n✅ Todas as dependências estão instaladas.")
    
    # Verificação específica para bibliotecas de visualização para AdvancedVisualization.js
    viz_libraries = ["plotly", "pandas", "numpy", "networkx", "vega", "altair"]
    missing_viz = [lib for lib in viz_libraries if lib.lower() not in installed_packages]
    
    if missing_viz:
        logger.info("\n⚠️ Bibliotecas de visualização necessárias para js/visualization/AdvancedVisualization.js não encontradas:")
        for lib in missing_viz:
            logger.info(f"  - {lib}")
        
        # Cria arquivo de requisitos de visualização se não existir
        if not viz_req_file.exists():
            create_viz_requirements_file(viz_req_file)
            
        logger.info(f"\nPara instalar: python {__file__} --install --viz")
    else:
        logger.info("\n✅ Todas as bibliotecas de visualização estão instaladas.")
    
    # Verificar conflitos de versão
    conflicts = analyze_version_conflicts(requirements)
    if conflicts:
        logger.warning(f"\n⚠️ Encontrados {len(conflicts)} potenciais conflitos de versão.")
        logger.info(f"Para resolver: python {__file__} --resolve-conflicts")
    
    # Mostra comandos disponíveis
    show_command_help()

if __name__ == "__main__":
    main()

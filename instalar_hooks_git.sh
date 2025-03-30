#!/bin/bash
#
# Script para instalar os hooks de git para testes de regressão automatizados
#

echo "🔧 Configurando hooks git para testes de regressão automatizados..."

# Diretório atual do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Diretório de hooks git
GIT_HOOKS_DIR="$PROJECT_DIR/.git/hooks"

# Criar diretório de hooks se não existir
mkdir -p "$GIT_HOOKS_DIR"

# Copiar o hook pre-commit
cp "$PROJECT_DIR/git-hooks/pre-commit" "$GIT_HOOKS_DIR/"

# Tornar o script executável
chmod +x "$GIT_HOOKS_DIR/pre-commit"

# Verificar se a instalação foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "✅ Hooks git instalados com sucesso!"
    echo "📝 Os testes de regressão serão executados automaticamente antes de cada commit."
    echo "   Para saber mais, consulte: docs/TESTES_REGRESSAO.md"
else
    echo "❌ Houve um problema na instalação dos hooks git."
    echo "   Por favor, verifique as permissões e tente novamente."
fi
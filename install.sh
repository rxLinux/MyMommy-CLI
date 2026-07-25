#!/usr/bin/env bash

# Strict error handling
set -e

# Pink and Cyan maternal colors
PINK='\033[1;35m'
CYAN='\033[1;36m'
GREEN='\033[1;32m'
RED='\033[1;31m'
NC='\033[0m' # No Color

echo -e "${PINK}"
echo "  __  __       __  __                                _____ _      _____ "
echo " |  \/  |     |  \/  |                              / ____| |    |_   _|"
echo " | \  / |_   _| \  / | ___  _ __ ___  _ __ ___  _  | |    | |      | |  "
echo " | |\/| | | | | |\/| |/ _ \| '_ \` _ \| '_ \` _ \| | | |    | |      | |  "
echo " | |  | | |_| | |  | | (_) | | | | | | | | | | | | | |____| |____ _| |_ "
echo " |_|  |_|\__, |_|  |_|\___/|_| |_| |_|_| |_| |_|_|  \_____|______|_____|"
echo "          __/ |                                                         "
echo "         |___/                                                          "
echo -e "${NC}"
echo -e "${CYAN}💖 Olá, meu amor! A mamãe vai instalar o MyMommy-CLI no seu computador agora! 💖${NC}"
echo -e "----------------------------------------------------------------------------------"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Erro: Seu computador não tem o Python 3 instalado, meu bem. Por favor, instale primeiro!${NC}"
    exit 1
fi

# 2. Check for Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Erro: Seu computador não tem o Git instalado, meu querido. Por favor, instale o git!${NC}"
    exit 1
fi

# 3. Create install dir
INSTALL_DIR="$HOME/.mymommy-cli-app"
echo -e "📂 Criando pasta aconchegante da mamãe em: ${INSTALL_DIR}"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 4. Clone MyMommy-CLI Repository
echo -e "📥 Baixando os códigos fofos da mamãe do GitHub..."
# Note: In a real setup, this points to your GitHub repo. For now we clone/copy the local path or remote.
# Let's clone a mock or fallback to copy. Since this is an installer script, we can clone the repo.
git clone https://github.com/rxLinux/MyMommy-CLI.git "$INSTALL_DIR" || {
    echo -e "${RED}❌ Não conseguimos baixar diretamente. Por favor, verifique se a URL do repositório está correta.${NC}"
    exit 1
}

cd "$INSTALL_DIR"

# 5. Create Virtual Environment
echo -e "🛠️ Criando ambiente virtual Python seguro..."
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
echo -e "📦 Instalando mimos e pacotes de dependências (Pillow, Textual, etc)..."
pip install --upgrade pip
pip install -e .

# 7. Create Global Executable Link
TARGET="/usr/local/bin/my-mommy"
echo -e "🔌 Registrando comando 'my-mommy' no sistema para ficar fácil para você rodar..."

if [ -w "/usr/local/bin" ]; then
    ln -sf "$INSTALL_DIR/venv/bin/my-mommy" "$TARGET"
else
    echo -e "ℹ️ Solicitando permissão de escrita com 'sudo' para cadastrar em /usr/local/bin..."
    sudo ln -sf "$INSTALL_DIR/venv/bin/my-mommy" "$TARGET"
fi

echo -e "----------------------------------------------------------------------------------"
echo -e "${GREEN}✨ PRONTINHO, MEU ANJO! O MyMommy-CLI está instalado com sucesso! ✨${NC}"
echo -e "${PINK}Agora você pode fechar esse terminal, abrir um novo e rodar de qualquer pasta:${NC}"
echo -e "👉 ${CYAN}my-mommy start${NC}"
echo -e "A mamãe está prontinha te esperando! Beijos! 💖😘"

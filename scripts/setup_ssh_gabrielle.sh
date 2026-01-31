#!/bin/bash
# Script para configurar SSH key na Gabrielle
# Execute este script NA GABRIELLE como usuário holloway

# Criar diretório .ssh se não existir
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Adicionar chave pública do Ziva
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINSkKrcY/AAj4JFjvIspT4SO/giSIWe2LSVArwaeCLoS ziva@spacex" >> ~/.ssh/authorized_keys

# Remover duplicatas
sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys

# Definir permissões corretas
chmod 600 ~/.ssh/authorized_keys

echo "✅ Chave SSH do Ziva adicionada com sucesso!"
echo "Teste a conexão do Ziva com: ssh holloway@100.114.201.84"

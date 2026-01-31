# Como Obter sua Chave API do Brave Search (GRATUITA)

## 📋 Passo a Passo

### 1. Acesse o Site
Vá para: **https://brave.com/search/api/**

### 2. Criar Conta
- Clique em "Get Started" ou "Sign Up"
- Crie uma conta gratuita (pode usar GitHub/Google)

### 3. Escolher Plano FREE
- **Free Tier**: 2.000 buscas por mês
- **Sem cartão de crédito necessário**
- Limite: 1 requisição por segundo

### 4. Obter API Key
Após criar a conta:
1. Vá para o Dashboard
2. Copie sua **API Key**
3. Ela terá formato: `BSA...` (começa com BSA)

### 5. Adicionar ao Ziva

```bash
# Edite o arquivo .env
nano /home/holloway/ziva/.env

# Adicione a linha:
BRAVE_API_KEY=BSA_sua_chave_aqui

# Salve e feche (Ctrl+O, Enter, Ctrl+X)
```

### 6. Reiniciar Ziva

```bash
cd /home/holloway/ziva
./restart.sh
```

## ✅ Pronto!

Agora o Ziva usará:
1. **Brave Search** (principal) - Buscas web completas
2. **Wikipedia** (fallback) - Conhecimento enciclopédico  
3. **GitHub** (fallback) - Código e projetos
4. **Stack Overflow** (fallback) - Soluções técnicas

## 📊 Limites do Plano Free

- ✅ 2.000 buscas/mês
- ✅ 1 req/segundo
- ✅ Sem custo
- ✅ Sem cartão de crédito

**Média**: ~66 buscas/dia → Mais que suficiente!

## 🔄 Se Não Conseguir a Chave

Sem problemas! O sistema usa **fallback automático**:
- Wikipedia
- GitHub
- Stack Overflow

Você terá ~80% da funcionalidade sem Brave!

## 📞 Dúvidas?

Brave Docs: https://brave.com/search/api/docs/

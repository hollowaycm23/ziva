# Instruções: Como Treinar LoRA no Kaggle

## 🚀 Passo a Passo

### 1. Acesse Kaggle
- Vá para: https://www.kaggle.com/code
- Faça login (ou crie conta gratuita)

### 2. Verifique sua Conta (IMPORTANTE!)
**Se a opção GPU estiver cinza/desabilitada:**
- Vá para: https://www.kaggle.com/settings
- Clique em **"Phone Verification"**
- Adicione seu número de telefone
- Confirme o código SMS
- **OU** conecte sua conta Google verificada

**Após verificação:**
- GPU será liberada em alguns minutos
- Você terá 30h/semana de GPU grátis

### 3. Crie Novo Notebook
- Clique em **"New Notebook"**
- Escolha **"Notebook"** (não Script)

### 4. **HABILITE INTERNET** ⚠️ **CRÍTICO!**
**SEM ISSO NADA VAI FUNCIONAR:**
- Clique em **Settings** (⚙️ no canto superior direito)
- Procure **"Internet"**
- **Mude de OFF para ON** 🌐
- Clique em **"Save"**

### 5. Ative GPU
- Ainda em **Settings**
- **Accelerator** → Selecione **GPU P100** ou **GPU T4**
- Se ainda estiver cinza, aguarde alguns minutos após verificação
- Clique em **Save**

### 4. Cole o Código
- Abra o arquivo: `kaggle_lora_training.py`
- Copie TODO o conteúdo
- Cole no notebook do Kaggle

### 5. Execute
- Clique em **Run All** ou execute célula por célula
- Aguarde ~10-15 minutos para treinar

### 6. Download dos Adapters
- Após o treinamento, vá em **Output** (lado direito)
- Baixe a pasta **`ziva_lora_adapters`**
- Extraia para: `/home/holloway/ziva/training/adapters/`

### 7. Use no Ziva
```bash
# Os adapters serão carregados automaticamente na próxima vez que o Ziva iniciar
cd /home/holloway/ziva
./restart.sh
```

## 📊 Dados de Treinamento

O notebook usa dados de exemplo, mas você pode substituir por seus próprios dados:

**Formato do arquivo `training_data.json`:**
```json
[
  {
    "text": "User: pergunta do usuário\nAssistant: resposta ideal do Ziva"
  }
]
```

**Dicas:**
- Use conversas reais do Ziva
- Inclua exemplos de uso correto de ferramentas
- Mínimo 20-50 exemplos para bons resultados
- Mais exemplos = melhor qualidade

## ⚠️ Troubleshooting

**GPU não disponível:**
- Verifique se ativou GPU P100 nas Settings
- Kaggle tem limite de 30h/semana de GPU

**Erro de memória:**
- Reduza `per_device_train_batch_size` para 1
- Aumente `gradient_accumulation_steps`

**Treinamento muito lento:**
- Normal! Leva 10-20 minutos
- Não feche a aba do navegador

## 💡 Próximos Passos

Após baixar os adapters:
1. Copie para `/home/holloway/ziva/training/adapters/`
2. Reinicie o Ziva
3. O modelo usará os adapters automaticamente
4. Teste com queries que antes falhavam

**Custo total: R$ 0,00** ✅

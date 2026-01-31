#!/bin/bash

# Script para testar absorção de conhecimento da Ziva
# Executa 25 perguntas e salva respostas

cd /home/holloway/ziva
source venv/bin/activate

OUTPUT_FILE="absorption_test_results_$(date +%Y%m%d_%H%M%S).txt"

echo "=== TESTE DE ABSORÇÃO DE CONHECIMENTO - ZIVA ===" > "$OUTPUT_FILE"
echo "Data: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Função para fazer pergunta
ask_question() {
    local num=$1
    local question=$2
    echo "[$num/25] Testando: $question"
    echo "---" >> "$OUTPUT_FILE"
    echo "QUESTÃO $num: $question" >> "$OUTPUT_FILE"
    python3 scripts/ask_ziva_cli.py "$question" >> "$OUTPUT_FILE" 2>&1
    echo "" >> "$OUTPUT_FILE"
    sleep 2
}

echo "Iniciando teste de absorção..."

# Geografia
echo "=== GEOGRAFIA ===" >> "$OUTPUT_FILE"
ask_question 1 "Qual é a capital da Austrália?"
ask_question 2 "Qual é o rio mais longo do mundo?"
ask_question 3 "Qual é o maior oceano do planeta?"
ask_question 4 "Quantos continentes existem?"
ask_question 5 "Qual é a montanha mais alta do mundo?"

# Literatura
echo "=== LITERATURA ===" >> "$OUTPUT_FILE"
ask_question 6 "Quem escreveu Dom Casmurro?"
ask_question 7 "Quem é o autor de Dom Quixote?"
ask_question 8 "Qual é a obra mais famosa de Gabriel García Márquez?"
ask_question 9 "Quem escreveu Orgulho e Preconceito?"
ask_question 10 "Algum brasileiro já ganhou o Nobel de Literatura?"

# Tecnologia
echo "=== TECNOLOGIA ===" >> "$OUTPUT_FILE"
ask_question 11 "Quem criou a linguagem Python?"
ask_question 12 "Em que ano foi criado o JavaScript?"
ask_question 13 "Quem é considerado o pai da Ciência da Computação?"
ask_question 14 "Qual foi o primeiro computador eletrônico?"
ask_question 15 "Quem criou o Linux?"

# Aviação Militar
echo "=== AVIAÇÃO MILITAR ===" >> "$OUTPUT_FILE"
ask_question 16 "Qual é a velocidade máxima do B-2 Spirit?"
ask_question 17 "Qual é o maior bombardeiro do mundo?"
ask_question 18 "Qual é a velocidade máxima do F-22 Raptor?"
ask_question 19 "Quantos pilotos tripulam um B-2 Spirit?"
ask_question 20 "Qual é o custo aproximado de um B-2 Spirit?"

# Esportes
echo "=== ESPORTES ===" >> "$OUTPUT_FILE"
ask_question 21 "Quantas Copas do Mundo o Brasil ganhou?"
ask_question 22 "Quem ganhou a Copa do Mundo de 2022?"
ask_question 23 "Quem detém o recorde mundial dos 100m masculino?"
ask_question 24 "Qual é o tempo do recorde de Usain Bolt nos 100m?"
ask_question 25 "Quem tem mais medalhas olímpicas na história?"

echo ""
echo "Teste concluído! Resultados salvos em: $OUTPUT_FILE"
echo ""
echo "Para ver os resultados:"
echo "cat $OUTPUT_FILE"

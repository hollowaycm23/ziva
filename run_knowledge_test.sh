#!/bin/bash

# Script para testar conhecimento da Ziva
# Executa perguntas e salva respostas

cd /home/holloway/ziva
source venv/bin/activate

OUTPUT_FILE="ziva_test_results_$(date +%Y%m%d_%H%M%S).txt"

echo "=== PROVA DE CONHECIMENTOS - ZIVA ===" > "$OUTPUT_FILE"
echo "Data: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Função para fazer pergunta
ask_question() {
    local num=$1
    local question=$2
    echo "[$num/30] Perguntando: $question"
    echo "---" >> "$OUTPUT_FILE"
    echo "QUESTÃO $num: $question" >> "$OUTPUT_FILE"
    python3 scripts/ask_ziva_cli.py "$question" >> "$OUTPUT_FILE" 2>&1
    echo "" >> "$OUTPUT_FILE"
    sleep 2
}

echo "Iniciando teste de conhecimentos..."

# Conhecimentos Gerais
echo "=== CONHECIMENTOS GERAIS ===" >> "$OUTPUT_FILE"
ask_question 1 "Qual é a capital da Austrália?"
ask_question 2 "Quem escreveu Dom Casmurro?"
ask_question 3 "Em que ano ocorreu a Proclamação da República no Brasil?"
ask_question 4 "Qual é o rio mais longo do mundo?"
ask_question 5 "Quem pintou a Mona Lisa?"

# Conhecimentos Científicos
echo "=== CONHECIMENTOS CIENTÍFICOS ===" >> "$OUTPUT_FILE"
ask_question 6 "Qual é a velocidade da luz no vácuo?"
ask_question 7 "Qual é a fórmula química da água?"
ask_question 8 "Quantos planetas existem no Sistema Solar?"
ask_question 9 "O que é um buraco negro?"
ask_question 10 "Qual é a teoria que explica a origem do universo?"

# Conhecimentos de Anime
echo "=== CONHECIMENTOS DE ANIME ===" >> "$OUTPUT_FILE"
ask_question 11 "Quem é o criador de One Piece?"
ask_question 12 "Qual é o nome verdadeiro de L em Death Note?"
ask_question 13 "Quantos episódios tem a primeira temporada de Attack on Titan?"
ask_question 14 "Qual é o poder do Sharingan em Naruto?"
ask_question 15 "Quem é o protagonista de Fullmetal Alchemist?"

echo ""
echo "Teste concluído! Resultados salvos em: $OUTPUT_FILE"
echo ""
echo "Para ver os resultados:"
echo "cat $OUTPUT_FILE"

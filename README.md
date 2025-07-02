# 📅 Sistema de Horários de Trabalho

Um sistema inteligente para geração automática de horários de trabalho usando programação por restrições (Constraint Programming) com interface web Streamlit.

## 🚀 Funcionalidades

- **Geração Automática de Horários**: Usa OR-Tools para otimizar a distribuição de turnos
- **Interface Web Intuitiva**: Interface amigável com Streamlit
- **Visualizações Interativas**: Gráficos e tabelas para análise dos horários
- **Configuração Flexível**: Ajuste fácil de parâmetros via sidebar
- **Exportação de Dados**: Download dos horários em formato CSV
- **Análise Detalhada**: Estatísticas e métricas de distribuição de trabalho

## 📋 Requisitos

- Python 3.8 ou superior
- Dependências listadas em `requirements.txt`

## 🛠️ Instalação

1. **Clone o repositório**:
```bash
git clone <repository-url>
cd horario
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Execute a aplicação**:
```bash
streamlit run app.py
```

4. **Acesse no navegador**:
```
http://localhost:8501
```

## 📊 Como Usar

### 1. Configuração Inicial
- Use a barra lateral para configurar os parâmetros:
  - **Período**: Número de dias para planejar (7-30 dias)
  - **Número de Funcionários**: Total de funcionários disponíveis (15-30)

### 2. Staff Necessário
Configure quantos funcionários são necessários para cada turno:

**Dias Úteis:**
- Manhã: 6 funcionários (padrão)
- Central: 2 funcionários (padrão)
- Tarde: 6 funcionários (padrão)
- Noite: 3 funcionários (padrão)

**Fins de Semana:**
- Manhã: 3 funcionários (padrão)
- Tarde: 3 funcionários (padrão)
- Noite: 3 funcionários (padrão)

### 3. Geração do Horário
- Clique em "🚀 Gerar Horário" para iniciar o cálculo
- Aguarde o processamento (pode levar alguns segundos)

### 4. Visualização dos Resultados
A aplicação apresenta os resultados em 4 abas:

#### 📅 Horário Completo
- Visualização detalhada de todos os turnos
- Filtros por tipo de turno e fins de semana
- Expansores para ver funcionários de cada turno

#### 👥 Resumo por Funcionário
- Tabela com estatísticas por funcionário
- Gráfico de distribuição de turnos
- Contagem de turnos por tipo

#### 📊 Estatísticas
- Distribuição de turnos (gráfico de pizza)
- Distribuição por dia da semana (gráfico de barras)

#### 🔍 Análise Detalhada
- Total de turnos por tipo
- Distribuição dias úteis vs fins de semana

### 5. Exportação
- Download do horário completo em CSV
- Download do resumo por funcionário em CSV

## 🔧 Restrições do Sistema

O sistema respeita as seguintes restrições:

1. **Turno Único por Dia**: Cada funcionário trabalha no máximo um turno por dia
2. **Staff Necessário**: Cada turno deve ter exatamente o número de funcionários configurado
3. **Limite Semanal**: Máximo 5 dias de trabalho por semana (janela deslizante)
4. **Diferenciação Fim de Semana**: Turnos diferentes para dias úteis e fins de semana

## 📁 Estrutura do Projeto

```
horario/
├── app.py              # Aplicação Streamlit principal
├── main.py             # Código original do solver
├── requirements.txt    # Dependências do projeto
└── README.md          # Este arquivo
```

## 🎯 Exemplo de Uso

1. **Configuração Padrão**:
   - Período: 14 dias
   - Funcionários: 23
   - Staff conforme configuração padrão

2. **Resultado Esperado**:
   - Horário viável respeitando todas as restrições
   - Distribuição equilibrada de turnos
   - Máximo 5 dias de trabalho por semana por funcionário

## 🔍 Solução de Problemas

### "Não foi possível encontrar uma solução"
- Reduza o número de funcionários necessários por turno
- Aumente o número total de funcionários
- Verifique se as restrições não são conflitantes

### Erro de Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Problemas de Performance
- Para períodos longos (>30 dias), o cálculo pode demorar
- Considere reduzir o período ou simplificar as restrições

## 📈 Melhorias Futuras

- [ ] Interface para definir férias específicas
- [ ] Preferências de turnos por funcionário
- [ ] Histórico de horários gerados
- [ ] Notificações por email
- [ ] Integração com sistemas de RH
- [ ] Otimização de custos de mão de obra

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Consulte a documentação do OR-Tools
- Verifique a documentação do Streamlit

---

**Desenvolvido com ❤️ usando OR-Tools e Streamlit** 
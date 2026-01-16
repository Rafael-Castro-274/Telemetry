# 🚗 Corredor X - Telemetria ACC

Sistema de telemetria em tempo real para Assetto Corsa Competizione utilizando Shared Memory.

## 📋 Descrição

O **Corredor X** é um sistema de telemetria que captura dados em tempo real do simulador ACC através de memória compartilhada, exibindo gráficos ao vivo e gerando relatórios completos em PDF após cada sessão.

### Funcionalidades

**Tempo Real:**
- 📊 Visualização ao vivo de acelerador e freio
- 🎨 Interface gráfica não intrusiva com tema escuro
- 📈 Atualização dinâmica a cada 30ms

**Pós-Sessão:**
- 📄 Geração automática de PDF com gráficos completos
- 📊 Análise de: RPM, Marcha, Ângulo do Volante, Acelerador, Freio e Velocidade
- 💾 Exportação de dados em CSV para análise posterior

## 🔧 Requisitos

- **Sistema Operacional:** Windows (necessário para acesso à Shared Memory do ACC)
- **Python:** 3.7 ou superior
- **Jogo:** Assetto Corsa Competizione em execução

## 📦 Instalação

### Opção 1: Instalação Automática (Recomendado)

Execute o script de instalação:

```bash
instalar.bat
```

### Opção 2: Instalação Manual

1. Clone o repositório:
```bash
git clone https://github.com/Rafael-Castro-274/Telemetry.git
cd Telemetria
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🚀 Como Usar

### Opção 1: Execução Rápida

Execute o script de execução:

```bash
executar.bat
```

### Opção 2: Execução Manual

1. Inicie o Assetto Corsa Competizione
2. Entre em uma sessão (treino, corrida, etc.)
3. Execute o script:
```bash
python corredorx.py
```

### Atalhos Durante a Execução

- **Ctrl+C**: Finaliza a captura e gera o PDF automaticamente

## 📁 Estrutura dos Arquivos

Após a execução, os seguintes arquivos serão gerados:

```
telemetry_YYYYMMDD_HHMMSS.csv  → Dados brutos da sessão
telemetry_YYYYMMDD_HHMMSS.pdf  → Relatório completo com gráficos
```

## 📊 Dados Capturados

| Dado | Descrição | Tipo |
|------|-----------|------|
| **gas** | Posição do acelerador (0-1) | Float |
| **brake** | Posição do freio (0-1) | Float |
| **rpm** | Rotação do motor | Integer |
| **gear** | Marcha atual | Integer |
| **steer** | Ângulo do volante | Float |
| **speed** | Velocidade em km/h | Float |

## 🐛 Solução de Problemas

### Erro: "O sistema não consegue encontrar o arquivo especificado"
- Verifique se o ACC está em execução e você está em uma sessão ativa

### Janela de gráficos não aparece
- Certifique-se de que o matplotlib está instalado corretamente
- Tente executar: `pip install --upgrade matplotlib`

### PDF não é gerado
- Verifique se há dados no arquivo CSV
- Certifique-se de que a sessão durou tempo suficiente para capturar dados

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir novas funcionalidades
- Enviar pull requests

## 📝 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.

## 👨‍💻 Autor

**Rafael Castro**
- GitHub: [@Rafael-Castro-274](https://github.com/Rafael-Castro-274)

---

> *"Só podemos mudar nossos caminhos, quando mudamos nossas decisões"*

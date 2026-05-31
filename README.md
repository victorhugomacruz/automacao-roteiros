# Automatizador de Roteiros com IA (Gemini 2.0 Flash)

Este projeto é um script automatizado em Python projetado para produtores de conteúdo que precisam escalar a criação de roteiros em lote. O sistema utiliza o poderoso modelo **Gemini 2.0 Flash** do Google para gerar títulos otimizados e roteiros altamente imersivos e criativos, e devolve arquivos prontos para locução no CapCut.

---

## 🚀 Estado Atual do Projeto (O Que Ele Faz)

Até o momento, a aplicação possui os seguintes recursos já implementados, testados e funcionando:

1. **Loop Dinâmico de Lotes:** O script permite gerar múltiplos roteiros de uma única vez. Basta informar quantos roteiros você quer criar e o script cuidará do processo de cada um iterativamente.
2. **Sistema de Prompts Modulares:** Toda a base dos textos é configurada externamente ao código-fonte, permitindo que qualquer pessoa os atualize sem precisar saber programar.
3. **Cérebro da IA (System Prompting):** Utiliza as "Instruções de Sistema" oficiais do Gemini. O script lê o arquivo `SystemPrompt.txt`, forçando a inteligência artificial a adotar uma persona específica (ex: *roteirista de histórias da bíblia* ou *especialista em mistérios do espaço*) e eleva a `temperature` para `0.9` aumentando drasticamente a criatividade narrativa.
4. **Resiliência a Falhas (Tratamento do Erro 429):** Como a API gratuita do Gemini possui limites de requisições por minuto, o script consegue identificar quando o limite é atingido e, automaticamente, pausa o processo por 40 segundos e tenta novamente sem quebrar o sistema (Auto-retry).
5. **Memória de Conversação:** O roteiro não é gerado de uma única vez para evitar limitações de saída do Google. O script inicia um "Chat" com a IA e pede a geração em 6 blocos sequenciais.
6. **Exportação Dupla (Texto e Legenda para CapCut):**
   - **`[Nome].txt`**: Salva um arquivo contendo o roteiro completo formatado em parágrafos para leitura humana.
   - **`[Nome].srt`**: Lê o conteúdo gerado, divide o texto em blocos de 5 segundos de fala e constrói a estrutura com *timestamps* exatos do padrão SubRip (`.srt`). Esse arquivo serve para você arrastar para dentro do CapCut e gerar as vozes automaticamente usando o recurso **Text to Speech**.

---

## 🛠️ Como Funciona a Arquitetura

O coração do software fica no arquivo principal `main.py`, apoiado por 4 arquivos de configuração fundamentais:

- `requirements.txt`: Mantém a relação de bibliotecas Python que precisam ser instaladas (`google-genai` para o SDK moderno e `python-dotenv` para o manuseio de chaves sensíveis).
- `.env`: Arquivo de variáveis de ambiente responsável por armazenar a sua chave secreta da API do Google Gemini (`GEMINI_API_KEY`).
- `PromptTitulo.txt` e `PromptRoteiro.txt`: Onde você insere as ordens literais que a IA deve obedecer. Obrigatório manter as marcações `[TITULO DO VIDEO]` e `[INSIRA O TITULO AQUI]` neles, respectivamente.
- `SystemPrompt.txt`: Onde você define "quem" a IA é.

O fluxo de processamento funciona assim:
1. O Python inicia lendo as variáveis e a chave do Gemini do `.env`.
2. Lê os arquivos `.txt` (com uma proteção de codificação que tenta rodar `utf-8` e cai para `latin-1` caso o Bloco de Notas do Windows gere sujeira).
3. Entra num laço `For` perguntando qual o título base.
4. Faz a primeira chamada na API (via `client.models.generate_content`) injetando o `PromptTitulo.txt` e higieniza o nome devolvido para uso no sistema operacional.
5. Inicia um `chat` contínuo (`client.chats.create`) aplicando a *System Instruction* (`SystemPrompt.txt`).
6. Faz a chamada do Bloco 1 com o `PromptRoteiro.txt` e engata num mini-loop com espera de 10 segundos chamando do Bloco 2 ao 6 ("Prossiga para o Bloco 2...").
7. Une todos os blocos, formata matematicamente para blocos `.srt` e joga ambos os resultados (`.txt` e `.srt`) na sua pasta.

---

## ⚙️ Como Instalar e Usar

**Passo 1: Variáveis de Ambiente e Chaves**
1. Na raiz da pasta, abra o arquivo `.env`.
2. Altere o valor `sua_chave_da_api_aqui` pela chave oficial adquirida no painel do [Google AI Studio](https://aistudio.google.com/).

**Passo 2: Configuração dos Textos**
Abra e personalize os seguintes arquivos no seu Bloco de Notas, deixando as marcações intactas:
- **`SystemPrompt.txt`**: Crie a persona e o tom de voz do roteiro. Ex: *"Aja como um contador de histórias de terror..."*
- **`PromptTitulo.txt`**: O prompt para o Título. Ex: *"Crie um título viral e chamativo sobre [TITULO DO VIDEO] sem usar emojis."*
- **`PromptRoteiro.txt`**: O prompt base da história. Ex: *"Inicie o bloco 1 com um grande mistério sobre [INSIRA O TITULO AQUI]."*

**Passo 3: Instalação do Ambiente**
No seu terminal (CMD ou PowerShell), ative seu ambiente virtual (`.venv`):
```powershell
.\.venv\Scripts\Activate.ps1
```
E instale as dependências essenciais:
```powershell
pip install -r requirements.txt
```

**Passo 4: Executando o Projeto**
Ainda com o terminal ativado, digite:
```powershell
python main.py
```
O console ganhará vida! Ele perguntará o número de roteiros, os títulos iniciais e irá informando passo a passo (Bloco 1, Bloco 2...) de forma transparente, além de emitir alertas amarelos se precisar pausar devido ao limite da API do Google.

**Passo 5: Dentro do CapCut**
Ao finalizar, pegue o arquivo gerado (ex: `A_Verdade_Escondida.srt`) e arraste para as suas bibliotecas do CapCut. Leve-o para a timeline e ative a funcionalidade de "Texto para Fala / Text to Speech" na aba superior direita do programa para criar uma dublagem automática e contínua do seu texto!

import os
import time
import re
import requests
from dotenv import load_dotenv

# Configurações iniciais
load_dotenv()
API_BASE_URL = os.getenv("ULTRAGEMINI_API_URL", "http://localhost:8000")


def ler_arquivo(caminho):
    """Lê o arquivo de texto com fallback de encodings."""
    encodings = ['utf-8', 'latin-1', 'mbcs']
    for enc in encodings:
        try:
            with open(caminho, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"ERRO: Arquivo '{caminho}' não encontrado.")
            exit(1)
    print(f"ERRO: Não foi possível ler o arquivo '{caminho}' (problema de codificação).")
    exit(1)

def higienizar_nome_arquivo(nome):
    """Remove caracteres inválidos para nomes de arquivos no Windows/Mac."""
    nome_limpo = re.sub(r'[\/\\:\*\?"<>\|]', '', nome)
    return nome_limpo.strip()

def tratar_erro_api(e):
    """Avalia erros de requisição e faz o sleep adequado."""
    print(f"Erro na requisição: {e}")
    print("Tentando novamente em 10 segundos...")
    time.sleep(10)

def iniciar_nova_conversa():
    """Chama a API para recarregar a página do Gemini e limpar o histórico."""
    url = f"{API_BASE_URL}/api/ultragemineai/new_chat"
    while True:
        try:
            print("\n[!] Limpando histórico e iniciando NOVA CONVERSA no Gemini...")
            response = requests.post(url, timeout=60)
            response.raise_for_status()
            break
        except Exception as e:
            tratar_erro_api(e)

def gerar_titulo(prompt_base, titulo_referencia):
    """Substitui a tag do prompt pelo título base e pede para a IA gerar o título novo."""
    prompt_final = prompt_base.replace("[TITULO DO VIDEO]", titulo_referencia)
    prompt_final += "\n\nRetorne APENAS o texto do título gerado, sem aspas, sem formatação markdown e sem nenhum texto adicional. Apenas a string do título."
    
    url = f"{API_BASE_URL}/api/ultragemineai/ask"
    
    while True:
        try:
            print(f"Gerando novo título...")
            response = requests.post(url, json={"prompt": prompt_final}, timeout=400)
            response.raise_for_status()
            data = response.json()
            texto_resposta = data.get("response", "").strip()
            
            # Validação Regra A
            if texto_resposta.startswith("Erro:"):
                print(f"[X] Validação de Falha: A API retornou -> {texto_resposta}")
                print(f"Repetindo o pedido...")
                time.sleep(5)
                continue
                
            return texto_resposta
        except Exception as e:
            tratar_erro_api(e)

def gerar_roteiro_em_blocos(prompt_base, titulo_novo):
    """Gera um roteiro em 6 blocos e retorna a LISTA de blocos para uso posterior."""
    prompt_final = prompt_base.replace("[INSIRA O TITULO AQUI]", titulo_novo)
    
    url = f"{API_BASE_URL}/api/ultragemineai/chat"
    blocos = []
    ultimo_texto_gerado = ""
    
    # Bloco 1
    while True:
        try:
            print("Gerando Roteiro - Bloco 1...")
            response = requests.post(url, json={"prompt": prompt_final}, timeout=400)
            response.raise_for_status()
            data = response.json()
            texto_resposta = data.get("response", "").strip()
            
            # Validação Regra A
            if texto_resposta.startswith("Erro:"):
                print(f"[X] Validação de Falha: A API retornou -> {texto_resposta}")
                print(f"Repetindo o pedido do Bloco 1...")
                time.sleep(5)
                continue
            
            ultimo_texto_gerado = texto_resposta
            
            # Adiciona a marcação no final apenas para o bloco 1
            texto_bloco_1 = texto_resposta + "\n\n(BLOCO 1)"
            blocos.append(texto_bloco_1)
            break
        except Exception as e:
            tratar_erro_api(e)
    
    # Blocos 2 ao 6
    for i in range(2, 7):
        while True:
            print(f"Aguardando 5 segundos para não sobrecarregar (Preparando Bloco {i})...")
            time.sleep(5)
            
            try:
                print(f"Gerando Roteiro - Bloco {i}...")
                response = requests.post(url, json={"prompt": f"Prossiga para o Bloco {i}."}, timeout=400)
                response.raise_for_status()
                data = response.json()
                texto_resposta = data.get("response", "").strip()
                
                # Validação Regra A
                if texto_resposta.startswith("Erro:"):
                    print(f"[X] Validação de Falha: A API retornou -> {texto_resposta}")
                    print(f"Repetindo o pedido do Bloco {i}...")
                    continue
                
                # Validação Regra B
                if texto_resposta == ultimo_texto_gerado:
                    print(f"[X] Validação de Falha: O site ignorou o envio e retornou o bloco anterior repetido. Forçando reenvio do Bloco {i}...")
                    continue
                
                ultimo_texto_gerado = texto_resposta
                blocos.append(texto_resposta)
                break 
            except Exception as e:
                tratar_erro_api(e)
                
    return blocos # Retorna a lista para facilitar a divisão das imagens

def gerar_prompts_imagens(prompt_base, titulo_novo, blocos_roteiro):
    """Gera prompts de imagens em 5 conversas, usando o bloco correspondente do roteiro e pedindo 2 lotes (1 e 2)."""
    url = f"{API_BASE_URL}/api/ultragemineai/chat"
    blocos_imagens = []
    
    # Roda exatamente 5 vezes (Conversa 1 a 5, usando Bloco 1 a 5 do roteiro)
    for i in range(1, 6):
        iniciar_nova_conversa()
        
        # Pega o bloco correspondente (lembrando que índice de lista começa em 0)
        if (i - 1) < len(blocos_roteiro):
            trecho_roteiro = blocos_roteiro[i - 1]
        else:
            trecho_roteiro = ""
            print(f"Aviso: Não há Bloco {i} no roteiro. Enviando trecho vazio.")
            
        # Monta o prompt
        prompt_final = prompt_base.replace("[TITULO DO VIDEO]", titulo_novo)
        prompt_final = prompt_final.replace("[INSERIR O SEU ROTEIRO INTEIRO AQUI]", trecho_roteiro)
        
        ultimo_texto_gerado = ""
        
        # --- PEDIDO DO LOTE 1 (Primeiros 50 prompts) ---
        while True:
            print(f"Gerando Imagens - Conversa {i} (Lote 1 de 2 | Roteiro Bloco {i})...")
            try:
                response = requests.post(url, json={"prompt": prompt_final}, timeout=400)
                response.raise_for_status()
                data = response.json()
                texto_resposta = data.get("response", "").strip()
                
                # Validação Regra A
                if texto_resposta.startswith("Erro:"):
                    print(f"[X] Validação de Falha: A API retornou -> {texto_resposta}")
                    print(f"Repetindo o pedido da Conversa {i} - Lote 1...")
                    time.sleep(5)
                    continue
                
                ultimo_texto_gerado = texto_resposta
                blocos_imagens.append(texto_resposta)
                break
            except Exception as e:
                tratar_erro_api(e)

        # --- PEDIDO DO LOTE 2 (Últimos 50 prompts) ---
        while True:
            print(f"Aguardando 5 segundos para não sobrecarregar (Preparando Lote 2 da Conversa {i})...")
            time.sleep(5)
            print(f"Gerando Imagens - Conversa {i} (Lote 2 de 2 | Roteiro Bloco {i})...")
            try:
                response = requests.post(url, json={"prompt": "Prossiga para o bloco 2."}, timeout=400)
                response.raise_for_status()
                data = response.json()
                texto_resposta = data.get("response", "").strip()
                
                # Validação Regra A
                if texto_resposta.startswith("Erro:"):
                    print(f"[X] Validação de Falha: A API retornou -> {texto_resposta}")
                    print(f"Repetindo o pedido da Conversa {i} - Lote 2...")
                    time.sleep(5)
                    continue
                
                # Validação Regra B
                if texto_resposta == ultimo_texto_gerado:
                    print(f"[X] Validação de Falha: Texto repetido detectado. Forçando reenvio da Conversa {i} - Lote 2...")
                    continue
                
                blocos_imagens.append(texto_resposta)
                break
            except Exception as e:
                tratar_erro_api(e)
                
    return "\n\n".join(blocos_imagens)

def formatar_tempo_srt(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milis = int(round((segundos % 1) * 1000))
    return f"{horas:02}:{minutos:02}:{segs:02},{milis:03}"

def formatar_bloco_srt(contador, tempo_inicio, texto, duracao_bloco):
    tempo_fim = tempo_inicio + duracao_bloco
    return f"{contador}\n{formatar_tempo_srt(tempo_inicio)} --> {formatar_tempo_srt(tempo_fim)}\n{texto.strip()}\n\n"

def converter_para_srt(texto_completo, arquivo_srt_path):
    CARACTERES_POR_BLOCO = 500
    PALAVRAS_MAX_BLOCO = 100
    DURACAO_BLOCO = 30
    INTERVALO_ENTRE_BLOCOS = 10

    srt_content = ''
    contador = 1
    tempo_acumulado = 0.0
    
    palavras = texto_completo.split()
    bloco_atual = ''
    palavras_no_bloco = 0

    for palavra in palavras:
        if len(bloco_atual) + len(palavra) <= CARACTERES_POR_BLOCO and palavras_no_bloco < PALAVRAS_MAX_BLOCO:
            bloco_atual += palavra + ' '
            palavras_no_bloco += 1
        else:
            ultimo_ponto_final = bloco_atual.rfind('.')
            if ultimo_ponto_final != -1 and ultimo_ponto_final != len(bloco_atual.strip()) - 1:
                resto = bloco_atual[ultimo_ponto_final + 1:]
                bloco_atual = bloco_atual[:ultimo_ponto_final + 1]
                
                srt_content += formatar_bloco_srt(contador, tempo_acumulado, bloco_atual, DURACAO_BLOCO)
                contador += 1
                tempo_acumulado += DURACAO_BLOCO + INTERVALO_ENTRE_BLOCOS
                
                bloco_atual = resto + palavra + ' '
                palavras_no_bloco = len(resto.split()) + 1
            else:
                srt_content += formatar_bloco_srt(contador, tempo_acumulado, bloco_atual, DURACAO_BLOCO)
                contador += 1
                tempo_acumulado += DURACAO_BLOCO + INTERVALO_ENTRE_BLOCOS
                
                bloco_atual = palavra + ' '
                palavras_no_bloco = 1

    if bloco_atual.strip():
        srt_content += formatar_bloco_srt(contador, tempo_acumulado, bloco_atual, DURACAO_BLOCO)

    try:
        with open(arquivo_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content.strip())
        print(f"✓ Arquivo de legenda salvo: {arquivo_srt_path}")
    except Exception as e:
        print(f"ERRO ao salvar o arquivo SRT: {e}")

def main():
    print("="*60)
    print("GERADOR AUTOMÁTICO DE ROTEIROS - ULTRAGEMINI API")
    print("="*60)
    
    try:
        qtd_roteiros = int(input("\nQuantos roteiros você deseja criar? "))
    except ValueError:
        print("Quantidade inválida. Por favor, digite um número inteiro.")
        return

    titulos_referencia = []
    for i in range(qtd_roteiros):
        titulo = input(f"Qual o título de referência original do vídeo {i+1}? ")
        titulos_referencia.append(titulo)

    prompt_titulo_base = ler_arquivo("PromptTitulo.txt")
    prompt_roteiro_base = ler_arquivo("PromptRoteiro.txt")
    prompt_imagem_base = ler_arquivo("PromptImagem.txt")
    
    for i, titulo_referencia in enumerate(titulos_referencia):
        print(f"\n--- Processando Roteiro {i+1} de {qtd_roteiros} ---")
        print(f"Referência base: {titulo_referencia}")
        
        # 1. Garante uma conversa limpa antes de começar
        iniciar_nova_conversa()
        
        # 2. Gerar Título
        novo_titulo_bruto = gerar_titulo(prompt_titulo_base, titulo_referencia)
        titulo_novo = higienizar_nome_arquivo(novo_titulo_bruto)
        print(f"✓ Novo título gerado: {titulo_novo}")
        
        # 3. Gerar Roteiro (6 Blocos) - Agora retorna uma lista com os 6 blocos isolados!
        blocos_roteiro = gerar_roteiro_em_blocos(prompt_roteiro_base, titulo_novo)
        print("✓ Roteiro em 6 blocos gerado com sucesso!")
        
        # Junta o roteiro completo para salvar os arquivos finais
        roteiro_completo = "\n\n".join(blocos_roteiro)
        
        # 4. Gerar Prompts de Imagens (5 Conversas com 2 Lotes de 50 cada)
        prompts_imagens = gerar_prompts_imagens(prompt_imagem_base, titulo_novo, blocos_roteiro)
        print("✓ Prompts de imagens (10 lotes em 5 conversas) gerados com sucesso!")
        
        # 5. Salvar Arquivos em Pasta
        print(f"Criando pasta: {titulo_novo}")
        os.makedirs(titulo_novo, exist_ok=True)
        
        nome_arquivo_txt = os.path.join(titulo_novo, "roteiro.txt")
        nome_arquivo_srt = os.path.join(titulo_novo, "roteiro.srt")
        nome_arquivo_imagem_txt = os.path.join(titulo_novo, "PromptImagem.txt")
        
        try:
            with open(nome_arquivo_txt, 'w', encoding='utf-8') as f:
                f.write(roteiro_completo)
            print(f"✓ Roteiro de leitura salvo: {nome_arquivo_txt}")
        except Exception as e:
            print(f"ERRO ao salvar o arquivo TXT: {e}")
            
        try:
            with open(nome_arquivo_imagem_txt, 'w', encoding='utf-8') as f:
                f.write(prompts_imagens)
            print(f"✓ Prompts de imagens salvos: {nome_arquivo_imagem_txt}")
        except Exception as e:
            print(f"ERRO ao salvar o arquivo de prompts: {e}")
            
        converter_para_srt(roteiro_completo, nome_arquivo_srt)
            
    print("\nProcesso concluído com sucesso! (Concluido)")

if __name__ == "__main__":
    main()
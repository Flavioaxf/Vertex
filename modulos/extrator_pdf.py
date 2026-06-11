import pdfplumber
import re

def extrair_dados_historico(caminho_ou_arquivo_pdf):
    concluidas = set()
    em_andamento = set()
    equivalencias_usadas = set()
    
    perfil_aluno = {
        "nome": "Não identificado",
        "matricula": "Não identificada",
        "ira": "N/A",
        "curso": "Ciência da Computação"
    }
    
    padrao_codigo = re.compile(r'\b[A-Z]{3,4}\d{4}\b')

    texto_completo = ""
    with pdfplumber.open(caminho_ou_arquivo_pdf) as pdf:
        # Validação de Documento Oficial da UERN
        if len(pdf.pages) > 0:
            primeira_pagina = pdf.pages[0].extract_text()
            if not primeira_pagina or "UERN" not in primeira_pagina or "Histórico Escolar" not in primeira_pagina:
                raise ValueError("Documento inválido. Por favor, anexe um Histórico Escolar válido da UERN emitido pelo SIGAA.")

        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                texto_completo += texto + "\n"

    # Extração de Dados Pessoais com RegEx Inteligente
    match_nome = re.search(r'Nome:\s*(.*?)(?=\s*Matrícula:|\n)', texto_completo, re.IGNORECASE)
    if match_nome:
        perfil_aluno["nome"] = match_nome.group(1).strip()

    match_mat = re.search(r'Matrícula:\s*(\d+)', texto_completo, re.IGNORECASE)
    if match_mat:
        perfil_aluno["matricula"] = match_mat.group(1).strip()

    match_ira = re.search(r'IRA:\s*([\d.]+)', texto_completo, re.IGNORECASE)
    if match_ira:
        perfil_aluno["ira"] = match_ira.group(1).strip()

    # Achata todo o PDF para a lógica de extração das disciplinas da grade
    texto_unificado = " ".join(texto_completo.split('\n')).upper()
    matches = list(padrao_codigo.finditer(texto_unificado))

    for i, match in enumerate(matches):
        codigo = match.group(0)
        start_pos = match.start()
        
        # A janela vai estritamente até o início da próxima disciplina
        end_pos = matches[i+1].start() if i + 1 < len(matches) else len(texto_unificado)
        janela = texto_unificado[start_pos:min(end_pos, start_pos + 300)]
        
        if "PENDENTE" in janela and "MATRICULADO" not in janela:
            continue
            
        # CORREÇÃO: Uso de \b (word boundaries) para garantir validação de palavras exatas.
        # Impede que a palavra TRANSMISSÃO seja lida como a sigla TRANS (Transferido).
        if re.search(r'\b(APR|APROVADO|DISP|DISPENSADO|CUMP|CUMPRIU|TRANS|INCORP)\b', janela):
            concluidas.add(codigo)
        elif re.search(r'\b(MATR|MATRICULADO)\b', janela):
            em_andamento.add(codigo)

    # Tratamento para as Equivalências
    padrao_eq = re.compile(r'CUMPRIU\s+([A-Z]{3,4}\d{4}).*?ATRAVÉS DE\s+([A-Z]{3,4}\d{4})')
    for eq_match in padrao_eq.finditer(texto_unificado):
        cod_obrig = eq_match.group(1)
        cod_equiv = eq_match.group(2)
        concluidas.add(cod_obrig)
        equivalencias_usadas.add(cod_equiv)

    # Limpeza para evitar que matérias de equivalência gastem slots de optativas
    for eq in equivalencias_usadas:
        if eq in concluidas:
            concluidas.remove(eq)
        if eq in em_andamento:
            em_andamento.remove(eq)

    return perfil_aluno, list(concluidas), list(em_andamento)
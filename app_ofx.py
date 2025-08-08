import streamlit as st
import re
import os
from collections import defaultdict

class OFXFitIdProcessor:
    def __init__(self):
        self.fitid_counts = defaultdict(int)
        self.duplicates_found = {}
    
    def process_ofx_content(self, ofx_content: str) -> str:
        self.fitid_counts.clear()
        self.duplicates_found.clear()
        
        linhas = ofx_content.splitlines()
        novas_linhas = []

        for linha in linhas:
            if "<FITID>" in linha:
                match = re.search(r"<FITID>([^<\n\r]*)", linha)
                if match:
                    original_fitid = match.group(1).strip()
                    self.fitid_counts[original_fitid] += 1
                    
                    if self.fitid_counts[original_fitid] == 1:
                        novas_linhas.append(linha)
                    else:
                        suffix_num = self.fitid_counts[original_fitid]
                        new_fitid = f'{original_fitid}_{suffix_num:02d}'
                        
                        nova_linha = linha.replace(f'<FITID>{original_fitid}', f'<FITID>{new_fitid}')
                        novas_linhas.append(nova_linha)
                        
                        if original_fitid not in self.duplicates_found:
                            self.duplicates_found[original_fitid] = 0
                        self.duplicates_found[original_fitid] += 1
                else:
                    novas_linhas.append(linha)
            else:
                novas_linhas.append(linha)
        
        return '\n'.join(novas_linhas)
    
    def get_duplicate_report(self) -> dict:
        return {fitid: self.fitid_counts[fitid] for fitid, count in self.fitid_counts.items() if count > 1}

def formatar_ofx(conteudo):
    conteudo_formatado = conteudo.replace('><', '>\n<')
    linhas = conteudo_formatado.splitlines()
    linhas.insert(0, '')
    return '\n'.join(linhas)

def corrigir_fitid_duplicado(conteudo):
    processor = OFXFitIdProcessor()
    resultado = processor.process_ofx_content(conteudo)
    duplicates = processor.get_duplicate_report()
    return resultado, duplicates

st.title("Ferramenta de Ajuste de Arquivos OFX")

arquivo = st.file_uploader("Escolha o arquivo .ofx", type=["ofx"])

if arquivo:
    try:
        conteudo = arquivo.read().decode("utf-8")
    except UnicodeDecodeError:
        arquivo.seek(0)
        conteudo = arquivo.read().decode("windows-1252")
    
    nome_original = os.path.splitext(arquivo.name)[0]

    acao = st.radio(
        "Escolha a ação:",
        ("Formatar OFX", "Corrigir FITID duplicado")
    )

    if st.button("Processar"):
        if acao == "Formatar OFX":
            resultado = formatar_ofx(conteudo)
            nome_saida = f"{nome_original}_formatado.ofx"
        else:
            resultado, duplicates = corrigir_fitid_duplicado(conteudo)
            nome_saida = f"{nome_original}_corrigido.ofx"
            
            if duplicates:
                st.write("FITIDs duplicados encontrados:")
                for fitid, count in duplicates.items():
                    st.write(f"{fitid}: {count} ocorrências")

        st.download_button(
            label="Baixar arquivo processado",
            data=resultado,
            file_name=nome_saida,
            mime="text/plain"
        )
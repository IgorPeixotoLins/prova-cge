import time
from src.extract import carregar_dados_siga
from src.transform import executar_pipeline_transformacao
from src.load import exportar_bases_tratadas


def formatar_inteiro_br(valor: int) -> str:
    """Converte um número inteiro para o padrão brasileiro com ponto no milhar."""
    return f"{valor:,}".replace(",", ".")


def formatar_moeda_br(valor: float) -> str:
    """Converte um float para o formato monetário brasileiro com ponto no milhar e vírgula no decimal."""
    return f"{valor:,.2f}".translate(str.maketrans({",": ".", ".": ","}))


def executar_pipeline_completo():
    """Orquestra a execução completa do ETL com medição de tempo e validação de saída."""
    inicio = time.perf_counter()

    print("=" * 60)
    print("PIPELINE DE DADOS - COMPRAS PÚBLICAS RJ (SIGA / PORTAL DE COMPRAS)")
    print("=" * 60)

    print("\n[1/3] Extraindo dados do arquivo comprimido em memória...")
    df_contratos_raw, df_itens_raw = carregar_dados_siga()
    linhas_c = formatar_inteiro_br(df_contratos_raw.shape[0])
    linhas_i = formatar_inteiro_br(df_itens_raw.shape[0])
    print(f" -> Contratos brutos: {linhas_c} linhas, {df_contratos_raw.shape[1]} colunas.")
    print(f" -> Itens brutos: {linhas_i} linhas, {df_itens_raw.shape[1]} colunas.")

    print("\n[2/3] Executando transformações vetorizadas e tipagem estrita...")
    df_contratos, df_itens = executar_pipeline_transformacao(df_contratos_raw, df_itens_raw)

    total_liquidado = df_contratos["valor_total_liquidado_r"].sum()
    estornos_empenho = formatar_inteiro_br((df_contratos["valor_total_empenhado_r"] < 0).sum())
    supressoes_itens = formatar_inteiro_br((df_itens["total_aditivada_suprimida"] < 0).sum())

    anomalias_preco = formatar_inteiro_br(int(df_itens["flag_inconsistencia_preco"].sum()))

    print(f" -> Total financeiro liquidado: R$ {formatar_moeda_br(total_liquidado)}")
    print(f" -> Estornos orçamentários preservados em empenhos: {estornos_empenho}")
    print(f" -> Supressões contratuais preservadas em itens: {supressoes_itens}")
    print(f" -> Anomalias cadastrais tratadas (preço unitário -,0003): {anomalias_preco}")

    print("\n[3/3] Persistindo dados processados em formato colunar Parquet...")
    caminho_c, caminho_i = exportar_bases_tratadas(df_contratos, df_itens)

    tam_c_mb = caminho_c.stat().st_size / (1024 * 1024)
    tam_i_mb = caminho_i.stat().st_size / (1024 * 1024)
    print(f" -> Base Contratos salva: {caminho_c} ({tam_c_mb:.2f} MB)")
    print(f" -> Base Itens salva: {caminho_i} ({tam_i_mb:.2f} MB)")

    duracao = time.perf_counter() - inicio
    print("\n" + "=" * 60)
    print(f"PIPELINE CONCLUÍDO COM SUCESSO EM {duracao:.2f} SEGUNDOS")
    print("=" * 60)


if __name__ == "__main__":
    executar_pipeline_completo()
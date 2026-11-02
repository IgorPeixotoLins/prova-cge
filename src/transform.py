import re
import unicodedata
import pandas as pd


def normalizar_nomes_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza cabeçalhos em snake_case, removendo acentuação e caracteres especiais."""
    novas_colunas = {}
    for col in df.columns:
        texto = unicodedata.normalize("NFD", col)
        texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
        texto = texto.strip().lower()
        texto = re.sub(r"[^\w\s]", "_", texto)
        texto = re.sub(r"\s+", "_", texto)
        texto = re.sub(r"_+", "_", texto).strip("_")
        novas_colunas[col] = texto

    return df.rename(columns=novas_colunas)


def sanitizar_coluna_monetaria(serie: pd.Series) -> pd.Series:
    """Converte valores monetários brasileiros em float64 preservando sinais negativos."""
    mascara_nulos = serie.isna()

    serie_texto = (
        serie.astype(str)
        .str.strip()
        .str.replace(r"^-,", "-0,", regex=True)
        .str.replace(r"\.", "", regex=True)
        .str.replace(",", ".", regex=False)
    )

    resultado = pd.to_numeric(serie_texto, errors="coerce")
    resultado[mascara_nulos] = None
    return resultado


def sanitizar_coluna_data(serie: pd.Series) -> pd.Series:
    """Converte strings de datas brasileiras (DD/MM/AAAA) em datetime64 de forma vetorizada."""
    return pd.to_datetime(serie.astype(str).str.strip(), format="%d/%m/%Y", errors="coerce")


def transformar_dados_contratos(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o pipeline completo de limpeza, tipagem e otimização na base de Contratos."""
    # Deduplicação preventiva na camada de contratos
    df = df.drop_duplicates().copy()
    df = normalizar_nomes_colunas(df)

    colunas_financeiras = [
        "valor_total_contrato_valor_estimado_para_contratacao_r",
        "valor_total_empenhado_r",
        "valor_total_liquidado_r",
        "valor_total_pago_r",
    ]
    for col in colunas_financeiras:
        if col in df.columns:
            df[col] = sanitizar_coluna_monetaria(df[col])

    colunas_datas = [
        "data_contratacao",
        "data_inicio_vigencia",
        "data_fim_vigencia",
        "data_public_deorj",
        "data_assinatura",
        "data_extracao",
    ]
    for col in colunas_datas:
        if col in df.columns:
            df[col] = sanitizar_coluna_data(df[col])

    if "status_contratacao" in df.columns:
        df["status_contratacao"] = df["status_contratacao"].astype("category")

    return df


def transformar_dados_itens(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o pipeline completo de limpeza, tipagem e deduplicação na base de Itens."""
    df = df.drop_duplicates().copy()
    df = normalizar_nomes_colunas(df)

    colunas_numericas = [
        "qtde_original",
        "vl_unit_original",
        "total_aditivada_suprimida",
        "vl_unit_aditivado_suprimido",
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = sanitizar_coluna_monetaria(df[col])

    if "vl_unit_original" in df.columns:
        df["flag_inconsistencia_preco"] = df["vl_unit_original"] < 0

    if "data_extracao" in df.columns:
        df["data_extracao"] = sanitizar_coluna_data(df["data_extracao"])

    return df


def executar_pipeline_transformacao(
    df_contratos: pd.DataFrame,
    df_itens: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Executa a transformação e validação estrutural de ambas as bases."""
    contratos_tratados = transformar_dados_contratos(df_contratos)
    itens_tratados = transformar_dados_itens(df_itens)
    return contratos_tratados, itens_tratados


if __name__ == "__main__":
    try:
        from src.extract import carregar_dados_siga
    except ModuleNotFoundError:
        from extract import carregar_dados_siga

    print("[TRANSFORM] Carregando bases brutas...")
    raw_contratos, raw_itens = carregar_dados_siga()

    print("[TRANSFORM] Executando pipeline vetorizado...")
    df_c, df_i = executar_pipeline_transformacao(raw_contratos, raw_itens)

    duplicatas_c = raw_contratos.duplicated().sum()
    duplicatas_i = raw_itens.duplicated().sum()

    print("\n=== RESUMO CONTRATOS TRATADOS ===")
    print(f"Linhas: {df_c.shape[0]:,} | Colunas: {df_c.shape[1]}")
    print(f"Duplicatas eliminadas: {duplicatas_c}")
    print(f"Total Liquidado: R$ {df_c['valor_total_liquidado_r'].sum():,.2f}")
    print(f"Estornos orçamentários preservados: {(df_c['valor_total_empenhado_r'] < 0).sum()}")
    print(f"Contratos com vigência preenchida: {df_c['data_inicio_vigencia'].notna().sum()}")

    print("\n=== RESUMO ITENS TRATADOS ===")
    print(f"Linhas finais (pós-deduplicação): {df_i.shape[0]:,} | Colunas: {df_i.shape[1]}")
    print(f"Duplicatas eliminadas: {duplicatas_i}")
    print(f"Supressões contratuais preservadas: {(df_i['total_aditivada_suprimida'] < 0).sum()}")
    print(f"Anomalias cadastrais tratadas (preço unitário -,0003): {df_i['flag_inconsistencia_preco'].sum()}")
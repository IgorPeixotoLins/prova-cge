from pathlib import Path
import pandas as pd

def salvar_dados_parquet(
    df: pd.DataFrame,
    nome_arquivo: str,
    caminho_destino: str | Path = "data/processed"
) -> Path:
    """Persiste um Dataframe em formato Parquet com compressão snappy."""
    pasta_destino = Path(caminho_destino)
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    caminho_final = pasta_destino / f"{nome_arquivo}.parquet"
    df.to_parquet(caminho_final, engine="pyarrow", index=False, compression="snappy")
    return caminho_final

def exportar_bases_tratadas(
    df_contratos: pd.DataFrame,
    df_itens: pd.DataFrame,
    diretorio_destino: str | Path = "data/processed"
) -> tuple[Path, Path]:
    """Exporta os DataFrames higienizados de contratos e itens para arquivos Parquet."""
    caminho_contratos = salvar_dados_parquet(df_contratos, "contratos", diretorio_destino)
    caminho_itens = salvar_dados_parquet(df_itens, "itens", diretorio_destino)
    return caminho_contratos, caminho_itens

if __name__ == "__main__":
    try:
        from src.extract import carregar_dados_siga
        from src.transform import executar_pipeline_transformacao
    except ModuleNotFoundError:
        from extract import carregar_dados_siga
        from transform import executar_pipeline_transformacao

    print("[LOAD] Executando pipeline completo: Extração -> Transformação -> Carga...")
    raw_contratos, raw_itens = carregar_dados_siga()
    df_c, df_i = executar_pipeline_transformacao(raw_contratos, raw_itens)

    caminho_c, caminho_i = exportar_bases_tratadas(df_c, df_i)

    tam_c_mb = caminho_c.stat().st_size / (1024 * 1024)
    tam_i_mb = caminho_i.stat().st_size / (1024 * 1024)

    print("\n[LOAD] Persistência concluída com sucesso:")
    print(f" -> Contratos salvos em: {caminho_c} ({tam_c_mb:.2f} MB)")
    print(f" -> Itens salvos em: {caminho_i} ({tam_i_mb:.2f} MB)")

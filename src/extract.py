from pathlib import Path
import zipfile
import pandas as pd


def _localizar_arquivo_no_zip(arquivo_zip: zipfile.ZipFile, nome_alvo: str) -> str:
    """Localiza o caminho de um arquivo no ZIP ignorando maiúsculas e subpastas."""
    alvo_normalizado = nome_alvo.strip().lower()

    for nome_real in arquivo_zip.namelist():
        if Path(nome_real).name.lower() == alvo_normalizado:
            return nome_real

    arquivos_existentes = ", ".join(arquivo_zip.namelist())
    raise FileNotFoundError(
        f"Arquivo '{nome_alvo}' não encontrado no ZIP. "
        f"Arquivos disponíveis no pacote: [{arquivos_existentes}]"
    )


def carregar_dados_siga(
    caminho_zip: str | Path = "data/raw/CONTRATOS.zip",
    encoding: str = "latin1",
    separador: str = ";"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extrai e carrega os DataFrames de contratos e itens de forma resiliente."""
    caminho = Path(caminho_zip)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo ZIP não encontrado: {caminho.resolve()}")

    with zipfile.ZipFile(caminho, mode="r") as arquivo_zip:
        nome_contratos = _localizar_arquivo_no_zip(arquivo_zip, "CONTRATOS.csv")
        nome_itens = _localizar_arquivo_no_zip(arquivo_zip, "ITENS_CONTRATOS.csv")

        with arquivo_zip.open(nome_contratos) as f_contratos:
            df_contratos = pd.read_csv(
                f_contratos,
                sep=separador,
                encoding=encoding,
                low_memory=False
            )

        with arquivo_zip.open(nome_itens) as f_itens:
            df_itens = pd.read_csv(
                f_itens,
                sep=separador,
                encoding=encoding,
                low_memory=False
            )

    return df_contratos, df_itens


if __name__ == "__main__":
    contratos, itens = carregar_dados_siga()
    print(f"Sucesso: Contratos carregados ({contratos.shape[0]} registros, {contratos.shape[1]} colunas).")
    print(f"Sucesso: Itens carregados ({itens.shape[0]} registros, {itens.shape[1]} colunas).")
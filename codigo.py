# ...existing code...
from pathlib import Path
import pandas as pd

CSV_PATH = Path(r"C:\Users\dell\Desktop\codigos\sales_cleaned.csv")
OUTPUT_XLSX = CSV_PATH.with_suffix(".xlsx")
AUTO_DROP_ORIGINAL = True  # True para remover a coluna original após dividir

def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)

def auto_split_columns(df: pd.DataFrame, sep: str = ",", drop_original: bool = True) -> pd.DataFrame:
    df = df.copy()
    for col in list(df.columns):
        # ignora colunas vazias
        if df[col].eq("").all():
            continue
        # calcula número máximo de partes quando dividido pela vírgula
        max_parts = df[col].astype(str).apply(lambda v: len(v.split(sep)) if v != "" else 1).max()
        # se só 1 parte, ignora (não contém separador na maioria)
        if max_parts <= 1:
            continue
        # expande para múltiplas colunas
        parts = df[col].astype(str).str.split(sep, expand=True, n=max_parts-1)
        parts = parts.apply(lambda s: s.str.strip())  # limpa espaços
        # nomeia novas colunas
        new_names = [f"{col}__part{i+1}" for i in range(parts.shape[1])]
        parts.columns = new_names
        # concatena e remove original se desejado
        df = pd.concat([df.drop(columns=[col]) if drop_original else df, parts], axis=1)
    return df

def save_to_excel(df: pd.DataFrame, path: Path) -> None:
    df.to_excel(path, index=False)
    print("Arquivo salvo:", path)

if __name__ == "__main__":
    df = load_csv(CSV_PATH)
    print("Colunas originais:", ", ".join(df.columns))
    df2 = auto_split_columns(df, sep=",", drop_original=AUTO_DROP_ORIGINAL)
    print("Colunas finais:", ", ".join(df2.columns))
    save_to_excel(df2, OUTPUT_XLSX)
# ...existing code...1
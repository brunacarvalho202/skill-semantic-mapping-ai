import pandas as pd
import logging

class DataProcessor:
    @staticmethod
    def load_skills_taxonomy(filepath: str) -> pd.DataFrame:
        """
Carrega a taxonomia de habilidades a partir de um arquivo CSV personalizado.

A função lê o arquivo linha por linha para lidar com descrições que podem conter vírgulas,
utilizando um limite de divisão (split) para separar apenas o ID, o nome da habilidade
e a descrição completa.

Args:
    filepath (str): Caminho para o arquivo CSV contendo a taxonomia.

Returns:
    pd.DataFrame: DataFrame contendo as colunas 'id', 'skill_name' e 'description'.

Raises:
    Exception: Caso ocorra um erro na leitura do arquivo ou no processamento dos dados.
"""
        rows = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                f.readline() 
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    parts = line.split(',', 2) 
                    
                    if len(parts) >= 3:
                        rows.append({
                            'id': parts[0].strip(),
                            'skill_name': parts[1].strip(),
                            'description': parts[2].strip().strip('"')
                        })
            
            df = pd.DataFrame(rows)
            return df
        except Exception as e:
            logging.error(f"Erro na taxonomia: {e}")
            raise

    @staticmethod
    def load_new_skills(filepath: str) -> pd.DataFrame:
        """
Carrega e pré-processa novas habilidades a partir de um arquivo CSV.

A função tenta detectar automaticamente o separador do arquivo e normaliza os 
nomes das colunas (removendo espaços e convertendo para minúsculas). Além disso, 
garante a existência de uma coluna de identificação para rastreabilidade.

Args:
    filepath (str): Caminho para o arquivo CSV com as novas habilidades.

Returns:
    pd.DataFrame: DataFrame com colunas normalizadas e uma coluna 'id_raw_original'.

Raises:
    Exception: Caso ocorra erro na leitura ou processamento (ex: arquivo corrompido).
"""
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig', sep=None, engine='python')
            df.columns = [c.strip().lower() for c in df.columns]
            
            if 'id' in df.columns:
                df = df.rename(columns={'id': 'id_raw_original'})
            elif 'id_raw_original' not in df.columns:
                df['id_raw_original'] = range(1, len(df) + 1)
                
            return df
        except Exception as e:
            logging.error(f"Erro nas novas skills: {e}")
            raise

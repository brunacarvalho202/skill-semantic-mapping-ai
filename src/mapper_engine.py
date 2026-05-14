import torch
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from rapidfuzz import process

class SkillMapper:
    def __init__(self, threshold=0.4):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Bi-Encoder
        self.bi_model = SentenceTransformer('intfloat/multilingual-e5-base').to(self.device) #testado antes: paraphrase-multilingual-mpnet-base-v2
        
        # Cross-Encoder
        self.cross_model = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1', device=self.device) #testado antes: cross-encoder/ms-marco-MiniLM-L-6-v2
        
        self.threshold = threshold
        self.df_taxonomy = None
        self.taxonomy_embeddings = None

    def fit(self, df_taxonomy: pd.DataFrame):
        """
Prepara e indexa a taxonomia para a busca semântica.

Este método realiza o 'encoding' (codificação) da taxonomia. Ele combina o nome 
da habilidade com sua descrição para criar uma representação rica em contexto, 
transformando esses textos em vetores numéricos (embeddings) através do Bi-Encoder.

Args:
    df_taxonomy (pd.DataFrame): DataFrame contendo as colunas 'skill_name' 
                                e 'description'.

Note:
    Os embeddings resultantes são armazenados em 'self.taxonomy_embeddings' 
    como tensores, permitindo buscas rápidas por similaridade de cosseno posteriormente.
"""
        self.df_taxonomy = df_taxonomy.copy()
        texts = (self.df_taxonomy['skill_name'] + " " + self.df_taxonomy['description']).str.lower().tolist()
        self.taxonomy_embeddings = self.bi_model.encode(texts, convert_to_tensor=True, show_progress_bar=True)

    def map_skills(self, df_new_skills: pd.DataFrame) -> pd.DataFrame:
        """
        Executa o mapeamento semântico de habilidades brutas para a taxonomia padrão.

        O motor de mapeamento utiliza uma arquitetura de 'Retrieve & Re-rank' combinada com 
        busca heurística, operando em três fases:
        1. **Fuzzy Match**: Atalho para correspondências exatas ou quase idênticas (score > 95).
        2. **Bi-Encoder (Retrieval)**: Busca vetorial rápida que identifica os Top 5 candidatos 
           mais próximos semanticamente.
        3. **Cross-Encoder (Re-ranking)**: Avaliação profunda de contexto (nome + descrição) 
           para validar e pontuar os candidatos, gerando o score final de confiança.

        Args:
            df_new_skills (pd.DataFrame): DataFrame contendo a coluna 'skill_raw' com os 
                termos a serem mapeados.

        Returns:
            pd.DataFrame: Relatório detalhado contendo:
                - Detalhes do match (ID, nome e status).
                - 'confidence_score': Pontuação final de confiança (0 a 1).
                - 'strategy_used': Técnica que definiu o match.
                - 'top1' a 'top5': Nome dos candidatos sugeridos pelo Bi-Encoder.
                - 'score_bi_encoder_top1' a '...top5': Scores de similaridade de cosseno.
        """
        new_skill_raws = df_new_skills['skill_raw'].astype(str).tolist()
        taxo_names_lower = self.df_taxonomy['skill_name'].str.lower().tolist()
    
        #Busca Vetorial (Bi-Encoder)
        new_embeddings = self.bi_model.encode(new_skill_raws, convert_to_tensor=True, batch_size=32)
        cosine_scores = util.cos_sim(new_embeddings, self.taxonomy_embeddings)
    
        all_cross_inputs = []
        map_indices = [] 
        results_map = {}
        top5_debug = {} #detalhes de cada um dos 5 candidatos

        #Fase de Seleção e Fuzzy Match
        for i, raw_name in enumerate(new_skill_raws):
            query_lower = raw_name.lower().strip()
        
            #Fuzzy Match
            best_fuzzy = process.extractOne(query_lower, taxo_names_lower, score_cutoff=95)
            if best_fuzzy:
                results_map[i] = (best_fuzzy[2], 1.0, 'fuzzy_match')
                top5_debug[i] = [] # Lista vazia para indicar que não houve rerank
                continue

            #Top 5 candidatos do Bi-Encoder
            top_k = 5
            top_results = torch.topk(cosine_scores[i], k=min(top_k, len(self.df_taxonomy)))
        
            candidatos_lista = []
            for score_bi, idx in zip(top_results.values.tolist(), top_results.indices.tolist()):
                tax_row = self.df_taxonomy.iloc[idx]
            
                candidatos_lista.append({
                    'name': tax_row['skill_name'],
                    'score': round(float(score_bi), 4)
                })
            
                contexto = f"{tax_row['skill_name']}: {tax_row['description']}".lower()
                all_cross_inputs.append([query_lower, contexto])
                map_indices.append((i, idx))
        
            top5_debug[i] = candidatos_lista

        #Reranking (Cross-Encoder)
        if all_cross_inputs:
            raw_scores = self.cross_model.predict(all_cross_inputs, batch_size=64, show_progress_bar=True)
            final_scores = 1 / (1 + np.exp(-raw_scores)) 

            for (score, (orig_idx, tax_idx)) in zip(final_scores, map_indices):
                if orig_idx not in results_map or score > results_map[orig_idx][1]:
                    results_map[orig_idx] = (tax_idx, score, 'ai_rerank')

        #DataFrame Final
        final_rows = []
        for i, row in df_new_skills.iterrows():
            idx_tax, score, tech = results_map.get(i, (None, 0.0, 'no_match'))
            status = 'matched' if score >= self.threshold and idx_tax is not None else 'no_match'
            match_row = self.df_taxonomy.iloc[idx_tax] if status == 'matched' else None
        
            # Dados básicos da predição final
            res_row = {
                'new_skill_id': row.get('id_raw_original', i),
                'skill_raw': row['skill_raw'],
                'taxonomy_id': match_row['id'] if match_row is not None else "—",
                'skill_name': match_row['skill_name'] if match_row is not None else "—",
                'confidence_score': round(float(score), 2),
                'match_status': status,
                'strategy_used': tech if status == 'matched' else 'insufficient_confidence'
            }

            candidatos = top5_debug.get(i, [])
            for rank in range(1, 6): #colunas top1 até top5
                if len(candidatos) >= rank:
                    res_row[f'top{rank}'] = candidatos[rank-1]['name']
                    res_row[f'score_bi_encoder_top{rank}'] = candidatos[rank-1]['score']
                else:
                    res_row[f'top{rank}'] = "—"
                    res_row[f'score_bi_encoder_top{rank}'] = 0.0

            final_rows.append(res_row)
        
        return pd.DataFrame(final_rows)
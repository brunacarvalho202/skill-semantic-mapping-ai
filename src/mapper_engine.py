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
Executa o mapeamento inteligente de novas habilidades para a taxonomia padronizada.

O processo utiliza uma estratégia híbrida em três camadas:
1. Busca Vetorial (Bi-Encoder): Identifica rapidamente os candidatos semanticamente próximos.
2. Fuzzy Match: Resolve correspondências exatas ou com pequenas variações ortográficas (atalho de performance).
3. Reranking (Cross-Encoder): Reavalia os Top-K candidatos da busca vetorial usando contexto profundo 
   (nome + descrição) para determinar o match final.

Args:
    df_new_skills (pd.DataFrame): DataFrame contendo as habilidades brutas na coluna 'skill_raw'.

Returns:
    pd.DataFrame: Relatório detalhado do mapeamento, incluindo o ID da taxonomia, 
                  score de confiança, status do match e a estratégia técnica utilizada.
"""
        new_skill_raws = df_new_skills['skill_raw'].astype(str).tolist()
        taxo_names_lower = self.df_taxonomy['skill_name'].str.lower().tolist()
        
        #Busca Vetorial (Bi-Encoder)
        new_embeddings = self.bi_model.encode(new_skill_raws, convert_to_tensor=True, batch_size=32)
        cosine_scores = util.cos_sim(new_embeddings, self.taxonomy_embeddings)
        
        all_cross_inputs = []
        map_indices = [] #saber qual par pertence a qual skill original
        results_map = {}

        #Fase de Seleção e Fuzzy Match
        for i, raw_name in enumerate(new_skill_raws):
            query_lower = raw_name.lower().strip()
            
            #Fuzzy Match
            best_fuzzy = process.extractOne(query_lower, taxo_names_lower, score_cutoff=95)
            if best_fuzzy:
                results_map[i] = (best_fuzzy[2], 1.0, 'fuzzy_match')
                continue

            #Se não for fuzzy, prepara para o Reranker (Top 5 candidatos)
            top_k = 5
            top_results = torch.topk(cosine_scores[i], k=min(top_k, len(self.df_taxonomy)))
            for idx in top_results.indices.tolist():
                tax_row = self.df_taxonomy.iloc[idx]
                # Passamos Nome + Descrição para o Reranker entender o contexto
                contexto = f"{tax_row['skill_name']}: {tax_row['description']}".lower()
                all_cross_inputs.append([query_lower, contexto])
                map_indices.append((i, idx))

        #Reranking
        if all_cross_inputs:
            # Predict em lote é muito mais rápido que um por um
            raw_scores = self.cross_model.predict(all_cross_inputs, batch_size=64, show_progress_bar=True)
            # Normalização simples para escala 0-1
            final_scores = 1 / (1 + np.exp(-raw_scores)) 

            for (score, (orig_idx, tax_idx)) in zip(final_scores, map_indices):
                if orig_idx not in results_map or score > results_map[orig_idx][1]:
                    results_map[orig_idx] = (tax_idx, score, 'ai_rerank')

        #DataFrame final
        final_rows = []
        for i, row in df_new_skills.iterrows():
            idx_tax, score, tech = results_map.get(i, (None, 0.0, 'no_match'))
            
            status = 'matched' if score >= self.threshold and idx_tax is not None else 'no_match'
            match_row = self.df_taxonomy.iloc[idx_tax] if status == 'matched' else None
            
            final_rows.append({
                'new_skill_id': row.get('id_raw_original', i),
                'skill_raw': row['skill_raw'],
                'taxonomy_id': match_row['id'] if match_row is not None else "—",
                'skill_name': match_row['skill_name'] if match_row is not None else "—",
                'confidence_score': round(float(score), 2),
                'match_status': status,
                'strategy_used': tech if status == 'matched' else 'insufficient_confidence'
            })
            
        return pd.DataFrame(final_rows)

import logging
from data_processor import DataProcessor
from mapper_engine import SkillMapper
from evaluator import SkillEvaluator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    try:
        #Tratamento
        processor = DataProcessor()
        df_tax = processor.load_skills_taxonomy('data/skill_taxonomy.csv')
        df_new = processor.load_new_skills('data/new_skills.csv')

        #Processamento(Híbrido: Fuzzy + Bi-Encoder + Cross-Encoder)
        mapper = SkillMapper(threshold=0.4) 
        mapper.fit(df_tax)
        df_final = mapper.map_skills(df_new)

        #Avaliação de Qualidade
        SkillEvaluator.gerar_relatorio_completo(df_final)

        # SkillEvaluator.plotar_visualizacoes(df_final)

        df_audit = df_final[df_final['strategy_used'] == 'ai_rerank'].sort_values('confidence_score')
        if not df_audit.empty:
            audit_path = 'auditoria_necessaria.csv'
            df_audit.to_csv(audit_path, index=False, encoding='utf-8-sig')
            logging.info(f"Arquivo de auditoria gerado: {audit_path}")

        output_path = 'mapeamento_final_bi_cross.csv'
        df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
        logging.info(f"Sucesso! Resultado completo salvo em: {output_path}")
        
        print("\nAmostra dos Resultados:")
        print(df_final[['skill_raw', 'skill_name', 'confidence_score', 'strategy_used']].head(15))

    except Exception as e:
        logging.error(f"Falha crítica no pipeline: {e}")

if __name__ == "__main__":
    main()


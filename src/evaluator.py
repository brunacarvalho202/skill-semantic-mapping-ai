import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class SkillEvaluator:
    @staticmethod
    def gerar_relatorio_completo(df_final: pd.DataFrame, output_dir: str = "resultados/experimento4_top5output"):
        """
Gera um diagnóstico técnico detalhado sobre a qualidade do mapeamento.

A função calcula métricas de cobertura, identifica lacunas (gaps) na taxonomia 
e analisa a confiança das predições segmentada por estratégia. Os resultados 
são exportados em formato de texto e complementados por visualizações gráficas.

Args:
    df_final (pd.DataFrame): DataFrame com os resultados do mapeamento.
    output_dir (str): Nome do diretório onde os arquivos serão salvos. 
                      Padrão é "relatorios".

Returns:
    None: A função salva os arquivos diretamente no sistema de arquivos.
"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        total = len(df_final)
        matches = df_final[df_final['match_status'] == 'matched']
        no_matches = df_final[df_final['match_status'] == 'no_match']
        
        #Métricas Principais
        taxa_cobertura = (len(matches) / total) * 100
        #considerar 'ambiguidade' quando o score é alto mas não absoluto
        zona_cinzenta = matches[(matches['confidence_score'] >= 0.5) & (matches['confidence_score'] <= 0.75)]
        
        relatorio_path = os.path.join(output_dir, "relatorio_tecnico.txt")
        
        with open(relatorio_path, "w", encoding="utf-8") as f:
            f.write("="*50 + "\n")
            f.write("      DIAGNÓSTICO ESTRATÉGICO DE QUALIDADE\n")
            f.write("="*50 + "\n")
            f.write(f"Total Analisado: {total}\n")
            f.write(f"Taxa de Cobertura: {taxa_cobertura:.1f}%\n")
            f.write(f"Volume em Zona Cinzenta (Ambiguidade): {len(zona_cinzenta)}\n")
            f.write("-" * 50 + "\n")

            #Por que não deu match?
            f.write("\nANÁLISE DE GAPS (O QUE ESTÁ FALTANDO NA TAXONOMIA):\n")
            top_gaps = no_matches['skill_raw'].value_counts().head(10)
            f.write(top_gaps.to_string() + "\n")

            #O match está correto?
            #Analisar a confiança média por estratégia
            f.write("\nCONFIANÇA MÉDIA POR ESTRATÉGIA:\n")
            confianca_estratégia = df_final.groupby('strategy_used')['confidence_score'].mean()
            f.write(confianca_estratégia.to_string() + "\n")

        print(f"Relatório salvo em: {relatorio_path}")
        SkillEvaluator.plotar_visualizacoes(df_final, output_dir)

    @staticmethod
    def plotar_visualizacoes(df_final: pd.DataFrame, output_dir: str):
        """
Gera e exporta visualizações gráficas para análise de performance.

A função cria um painel com dois gráficos principais: um histograma da 
distribuição dos scores de confiança (para entender a 'certeza' do modelo) 
e um gráfico de pizza mostrando a proporção das estratégias de mapeamento 
utilizadas (Fuzzy, Rerank ou No Match).

Args:
    df_final (pd.DataFrame): DataFrame com os resultados consolidados.
    output_dir (str): Diretório onde a imagem 'dashboard_qualidade.png' será salva.

Note:
    Utiliza as bibliotecas matplotlib e seaborn para a renderização técnica 
    dos gráficos.
"""
        plt.figure(figsize=(12, 6))

        #Distribuição de Confiança
        plt.subplot(1, 2, 1)
        sns.histplot(df_final['confidence_score'], bins=20, kde=True, color='teal')
        plt.title('Distribuição de Confiança (Scores)')

        #Origem dos Matches
        plt.subplot(1, 2, 2)
        counts = df_final['strategy_used'].value_counts()
        plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
        plt.title('Origem da Decisão (Match vs No Match)')

        plt.tight_layout()
        graph_path = os.path.join(output_dir, "dashboard_qualidade.png")
        plt.savefig(graph_path)
        plt.close()
        print(f"Gráficos salvos em: {graph_path}")
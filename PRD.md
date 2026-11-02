# PRD — Pipeline ETL e Análise Exploratória de Compras Públicas (SIGA / RJ)

## 1\. Visão Geral do Projeto

* **Nome do Projeto:** Pipeline ETL e Análise Exploratória de Contratos Públicos do Estado do Rio de Janeiro  
* **Autor / Engenheiro:** Igor Peixoto Lins  
* **Avaliador / Stakeholder:** Miguel da T.I.  
* **Objetivo Principal:** Desenvolver um pipeline de dados em Python robusto, modular e de alta performance para extração, higienização, tipagem estrita e auditoria relacional das bases de compras públicas do Estado do Rio de Janeiro (SIGA), complementado por um relatório exploratório com indicadores orçamentários e governamentais.  
* **Status:** Concluído / Em fase de consolidação de documentação executiva.

---

## 2\. Contexto e Problema de Negócio

O Estado do Rio de Janeiro publica seus registros de contratações públicas e itens adjudicados no Portal de Compras (SIGA). Contudo, os dados brutos apresentam desafios típicos de bases legadas do setor público:

1. **Volumetria Desnormalizada:** 474.784 registros brutos distribuídos em dois arquivos tabulares com encoding regional e formatos numéricos não padronizados.  
2. **Qualidade e Ruído Cadastral:** Registros duplicados decorrentes do extrator web, valores nulos semânticos associados ao ciclo da despesa pública, além de anomalias em preços unitários e representação de supressões contratuais.  
3. **Necessidade de Governança Orçamentária:** Falta de visibilidade analítica consolidada sobre o funil da despesa pública (Lei Federal nº 4.320/64), concentração de fornecedores e ritos de aquisição (Pregão vs. Dispensa).

---

## 3\. Fontes de Dados e Ingestão

* **Origem:** Portal de Compras do Estado do Rio de Janeiro (SIGA)  
* **Arquivo Fonte:** `https://www.compras.rj.gov.br/siga/imagens/CONTRATOS.zip`  
* **Conjuntos de Dados:**  
  * `CONTRATOS.csv`: 130.511 linhas e 27 colunas com metadados do contrato, datas de vigência, modalidade e valores orçamentários.  
  * `ITENS.csv`: 344.273 linhas e 11 colunas com a discriminação dos itens, quantidades originais, preços unitários e aditivos/supressões.

---

## 4\. Requisitos de Arquitetura e Engenharia de Dados (ETL)

### 4.1. Princípio da Responsabilidade Única (SRP) e Modularidade

O pipeline é desacoplado em módulos independentes em `src/`, orquestrados por um ponto de entrada único:

* `src/extract.py`: Ingestão otimizada em streaming diretamente do arquivo compactado `.zip` na memória, evitando persistência desnecessária em disco de arquivos CSV volumosos.  
* `src/transform.py`: Higienização de cabeçalhos (*snake\_case* sem acentuação), sanitização monetária brasileira vetorizada, conversão estrita de tipos de datas e identificação de anomalias cadastrais.  
* `src/load.py`: Persistência analítica em formato colunar Apache Parquet com compactação Snappy em `data/processed/`, otimizando I/O e consultas analíticas.  
* `main.py`: Orquestrador de ponta a ponta com instrumentação de tempo de execução e sumário de métricas de qualidade.

### 4.2. Performance e Vetorização

* **Execução Total:** Pipeline executado de forma totalmente vetorizada (Pandas/NumPy em C/Cython), concluindo o processamento de quase meio milhão de registros em \~2,0 segundos.  
* **Armazenamento:** Redução drástica da pegada em disco e em memória RAM por meio de tipagem estrita (`category`, `float64`, `datetime64`) e persistência Parquet.

---

## 5\. Regras de Qualidade de Dados e Auditoria (Data Quality)

### 5.1. Deduplicação Cadastral

* **Contratos:** 0 duplicatas integrais identificadas; a coluna `contratacao` atua como Chave Primária (PK) única.  
* **Itens:** Identificação e expurgo de 747 linhas redundantes espelhadas originadas da extração do SIGA. A base tratada foi consolidada em 343.526 itens.

### 5.2. Integridade Referencial (1:N)

* **Taxa de Aderência:** 100,00% de integridade entre `contratos` e `itens`. Zero itens órfãos identificados na base tratada.

### 5.3. Semântica Contábil dos Nulos (Lei Federal nº 4.320/64)

* A ausência de dados em `valor_total_empenhado_r` (57,45%), `valor_total_liquidado_r` (69,67%) e `valor_total_pago_r` (71,39%) não decorre de falha de extração, mas sim do ciclo orçamentário regular: \$\$\\text{Estimado (100%)} \\longrightarrow \\text{Empenhado (42,55%)} \\longrightarrow \\text{Liquidado (30,33%)} \\longrightarrow \\text{Pago (28,61%)}\$\$  
* Atas de Registro de Preços e estimativas orçamentárias que não geraram ordens de empenho ou liquidação mantêm seus campos nulos de acordo com a técnica orçamentária pública.

### 5.4. Preservação de Regras Contábeis e Tratamento de Anomalias

* **Estornos Orçamentários:** Preservação contábil de 169 valores negativos no empenho, garantindo o fechamento aritmético dos balanços do Estado.  
* **Supressões Contratuais:** Preservação de 243 valores negativos em itens, correspondentes a reduções legais do objeto licitado.  
* **Anomalia de Preço Unitário:** Criação da coluna `flag_inconsistencia_preco` em `src/transform.py` para isolar 26 registros atípicos com preço unitário `-,0003` (ata de passagens aéreas da *Webtrip* baseada em taxa de desconto administrativo), sem descarte arbitrário de dados.

---

## 6\. Análise Exploratória (EDA) e Indicadores de Gestão

As análises visuais foram estruturadas no notebook `notebooks/01_analise_contratos.ipynb`, utilizando paleta institucional sóbria e formatação nativa Pandas (*Dependency Minimization* sem Jinja2):

1. **Funil de Execução Orçamentária:**  
   * Estimado (Edital): R\$ 140,41 Bi  
   * Empenhado (Reserva): R\$ 56,34 Bi  
   * Liquidado (Executado): R\$ 32,72 Bi  
   * Efetivamente Pago: R\$ 29,62 Bi  
   * *Diagnóstico:* Conversão de 23,31% das estimativas em liquidações reais; taxa de quitação financeira de 90,53% das obrigações liquidadas.  
2. **Série Temporal de Despesas Públicas (2010 a 2024):**  
   * Mapeamento do salto orçamentário no triênio 2020–2022 (R\$ 6,3 Bi a R\$ 6,4 Bi anuais), decorrente de contratações emergenciais da crise sanitária de COVID-19.  
3. **Curva ABC de Fornecedores (Pareto):**  
   * Top 10 fornecedores concentram 26,54% do total liquidado (R\$ 8,68 Bi de R\$ 32,72 Bi).  
   * Liderança expressiva de Organizações Sociais de Saúde (OSS) e órgãos públicos de assistência médica (Fundação Saúde do Estado do RJ: R\$ 3,41 Bi; Instituto IDEAS: R\$ 1,46 Bi).  
4. **Distribuição por Modalidade de Aquisição:**  
   * *Dispensa \- Especial* lidera o volume financeiro liquidado com 42,07% (R\$ 13,77 Bi em 10.442 contratos), superando o *Pregão Eletrônico* (16,91% / R\$ 5,53 Bi), corroborando a aplicação intensiva de normas de emergência no período pandêmico.

---

## 7\. Requisitos Não Funcionais e Padrões de Código

* **Clean Code:** Código modular, legível e enxuto, sem poluição de comentários linha a linha, com cabeçalhos sintéticos de intenção.  
* **Reprodutibilidade:** Gerenciamento de dependências via `requirements.txt` e ambiente virtual `.venv` em Python 3.13.  
* **Documentação:** Criação de `README.md` executivo contendo guia de reprodução, justificativas arquiteturais e glossário contábil.

---

## 8\. Matriz de Critérios de Avaliação (Checklist de Conformidade)

| Critério Avaliado | Requisito do Edital | Implementação no Projeto | Status |
| :---- | :---- | :---- | :---: |
| **Qualidade do ETL** | Extração, limpeza e padronização | Modularização em `src/`, processamento em memória, Parquet colunar e execução em \~2s | Conforme |
| **Consistência dos Dados** | Nulos e duplicados | 747 duplicatas expurgadas, diagnóstico semântico da Lei 4.320/64 e anomalias sinalizadas | Conforme |
| **Relacionamento** | Relacionamento entre as bases | 100,00% de integridade referencial 1:N validada sem registros órfãos | Conforme |
| **Relevância Analítica** | Padrões, tendências e indicadores | Funil orçamentário, série temporal pandêmica, Pareto de fornecedores e modalidades | Conforme |
| **Visualização e Clareza** | Gráficos, tabelas e conclusões | Paleta sóbria executiva, formatação sem dependências externas e narrativa de negócios | Conforme |
| **Organização do Código** | Separação das etapas e README | Arquitetura SRP (`extract`, `transform`, `load`, `main`) e documentação completa | Conforme |


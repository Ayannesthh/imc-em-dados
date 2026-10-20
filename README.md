# IMC em Dados — dashboard Python (Streamlit)

Versão **independente** do projeto NutriData. Desenvolvida com base no arquivo `IMC_em_Dados.html` fornecido pela equipe, preservando as 6 áreas: Caracterização da base, Perfil, Análise exploratória, Regressão Linear, Random Forest e Conclusões.

## Arquivos

- `app.py`: aplicativo Streamlit (Python)
- `dados_painel.json`: dados e indicadores extraídos do HTML enviado (inclui 450 linhas anonimizadas)
- `requirements.txt`: bibliotecas necessárias

## Para executar no computador

Instale Python e execute na pasta dos arquivos:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Para publicar no Streamlit Community Cloud

1. **Crie um novo repositório privado no GitHub**, separado do NutriData original. Exemplo: `imc-em-dados`.
2. Envie os três arquivos da pasta (`app.py`, `dados_painel.json`, `requirements.txt`) diretamente na raiz (não envie só o ZIP).
3. Entre em https://share.streamlit.io e crie **outro aplicativo**, escolhendo seu novo repositório, branch `main` e arquivo `app.py`.
4. Em Settings > Sharing, mantenha **Only specific people can view this app** e confira a política de acesso da equipe.

## Interpretação

- Os 450 registros e os indicadores dos modelos vieram do arquivo HTML fornecido, sem acessar bases externas. 
- Os **filtros** da barra lateral modificam apenas a análise descritiva das pessoas; **não recalculam** os modelos estatísticos nem a validação cruzada.
- Coeficientes da regressão indicam *associação*, não causalidade.
- A identificação de respostas "reais" é uma **inferência** da equipe, não uma classificação oficial da base.
- Não compartilhe CSVs particulares de uma clínica nem dados pessoais em repositórios online sem autorização expressa. Mesmo quando privados, os arquivos ficam armazenados no serviço de hospedagem.

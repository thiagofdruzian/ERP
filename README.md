# ERP Comercial de Formacao de Precos

Este projeto e um ERP desktop em Python focado em cotacao e formacao de preco para operacao comercial.
Ele foi construido para ajudar a decidir preco de venda com base em custo de compra, impostos, margem e acrescimos comerciais.

O sistema esta em desenvolvimento continuo, mas ja esta funcional para uso operacional no fluxo principal de precificacao.

## O que o sistema ja faz hoje

### 1. Cotacao de compra (lado esquerdo)
- Entrada de preco de compra liquido.
- Entrada de impostos de compra:
  - IPI
  - ST
  - ICMS
  - PIS
  - COFINS
- Definicao de credito para ICMS, PIS e COFINS.
- Regra comercial aplicada no calculo:
  - IPI e ST entram no custo e nao geram credito.
- Exibicao dos indicadores de compra:
  - impostos totais na compra
  - creditos tributarios
  - custo efetivo (base para venda)

### 2. Formacao de venda (lado direito)
- Entrada de impostos de venda:
  - PIS
  - COFINS
  - ICMS
- Calculo bidirecional:
  - informando margem CLD, calcula preco de venda
  - informando preco de venda, calcula margem CLD
- Flag de acrescimo comercial no preco de venda:
  - checkbox para ativar
  - percentual editavel
  - valor do acrescimo exibido no resumo

### 3. Indicadores comerciais de resultado
- Impostos de venda em R$.
- Lucro liquido na venda em R$.
- Margem CLD calculada.
- Margem liquida na venda.
- Margem real.
- KPIs no topo do card de venda:
  - Preco Final
  - Lucro Liquido
  - Margem Liquida

### 4. Usabilidade
- Atalhos de teclado:
  - `Ctrl+S` salva cotacao
  - `Ctrl+N` cria nova cotacao
  - `F5` atualiza historico
- Mascaras/normalizacao por campo (dinheiro e percentual) ao sair do campo ou pressionar Enter.
- Interface em duas colunas (compra x venda), com visual limpo e foco operacional.

### 5. Persistencia e historico
- Persistencia em SQLite.
- Salva cotacoes com versao, status, produto, categoria e fornecedor.
- Lista historico de cotacoes na tela.
- Carrega cotacao do historico com duplo clique.

### 6. Robustez tecnica
- Motor de calculo separado da interface (`domain/pricing_engine.py`).
- Modelos de dominio explicitos (`domain/models.py`).
- Camada de repositorio para persistencia (`infrastructure/quote_repository.py`).
- Testes unitarios cobrindo regras centrais de precificacao.

---

## Stack tecnica

- Python 3.x
- CustomTkinter (UI desktop)
- SQLite (persistencia local)
- unittest (testes)

Dependencia principal:
- `customtkinter>=5.2.2`

---

## Como executar

No PowerShell:

```powershell
cd C:\seucaminho
python -m pip install -r requirements.txt
python erp_precos.py
```

Se seu ambiente usa `py`:

```powershell
py -3 -m pip install -r requirements.txt
py -3 erp_precos.py
```

---

## Rodando testes

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

---

## Estrutura atual do projeto

```text
ERP/
  erp_precos.py
  requirements.txt
  README.md
  erp/
    domain/
    application/
    infrastructure/
  tests/
  data/
```

---

## Estado do desenvolvimento

Este projeto esta em fase de evolucao, com foco em:
- confiabilidade do calculo comercial
- experiencia de uso no dia a dia
- evolucao gradual para padrao ERP mais completo

O fluxo principal de cotacao e formacao de preco ja esta funcional e pronto para iteracoes.

---

## Roadmap de Versoes

### v0.1 - Base operacional (atual)
- Motor de precificacao funcionando de ponta a ponta.
- Interface compra/venda com calculo bidirecional.
- Acrescimo comercial por percentual.
- Persistencia SQLite e historico de cotacoes.
- Atalhos e mascaras de entrada.

### v0.2 - Evolucao comercial
- Filtros avancados no historico (status, periodo, fornecedor, produto).
- Duplicar cotacao e comparacao de versoes.
- Regras de arredondamento comercial configuraveis.
- Trava de preco minimo por produto/categoria.

### v0.3 - Governanca e controle
- Perfis de acesso (comercial, compras, gerencia).
- Auditoria de alteracoes (quem, quando, o que mudou).
- Backup automatico e restauracao assistida.
- Dashboard com indicadores por periodo.

### v1.0 - Versao de consolidacao ERP
- API para integracao com outros sistemas.
- Publicacao com processo de release e changelog.
- Testes ampliados (unitario + integracao + regressao).
- Documentacao funcional e tecnica completa.



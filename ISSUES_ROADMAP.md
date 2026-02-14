# Checklist de Issues (Roadmap)

Este arquivo foi feito para facilitar a abertura de issues no GitHub com padrao consistente.
Sugestao: abra uma issue por bloco, mantendo a ordem por versao.

## Labels sugeridas
- `roadmap`
- `v0.2`, `v0.3`, `v1.0`
- `backend`, `frontend`, `ui-ux`, `database`, `qa`, `docs`
- `high`, `medium`, `low`

---

## v0.2 - Evolucao comercial

- [ ] **Issue 1: Filtros avancados no historico de cotacoes**
  - Objetivo: filtrar por status, periodo, fornecedor e produto.
  - Entrega:
    - campos de filtro na UI
    - consulta com filtros no repositorio
    - botao limpar filtros
  - Criterio de aceite:
    - filtros combinados funcionando sem travar a interface
    - resultado consistente com banco
  - Labels: `roadmap`, `v0.2`, `ui-ux`, `database`, `high`

- [ ] **Issue 2: Duplicar cotacao com 1 clique**
  - Objetivo: criar nova cotacao com base em uma ja existente.
  - Entrega:
    - acao de duplicar no historico
    - nova cotacao em status `RASCUNHO`
  - Criterio de aceite:
    - copia preserva impostos, margem e observacoes
    - nao sobrescreve cotacao original
  - Labels: `roadmap`, `v0.2`, `backend`, `high`

- [ ] **Issue 3: Comparacao de versoes de cotacao**
  - Objetivo: visualizar diferenca de preco, lucro e margem entre versoes.
  - Entrega:
    - tela/modal de comparacao
    - deltas absolutos e percentuais
  - Criterio de aceite:
    - comparacao entre versao atual e anterior funcional
  - Labels: `roadmap`, `v0.2`, `ui-ux`, `backend`, `medium`

- [ ] **Issue 4: Regras de arredondamento comercial**
  - Objetivo: permitir `NORMAL`, `X90`, `X99`.
  - Entrega:
    - configuracao na UI
    - aplicacao da regra no preco final
  - Criterio de aceite:
    - regra aplicada antes de salvar cotacao
  - Labels: `roadmap`, `v0.2`, `backend`, `medium`

- [ ] **Issue 5: Trava de preco minimo por produto/categoria**
  - Objetivo: impedir preco final abaixo do minimo configurado.
  - Entrega:
    - cadastro da regra minima
    - validacao no fluxo de calculo/salvamento
  - Criterio de aceite:
    - sistema bloqueia ou ajusta conforme regra definida
  - Labels: `roadmap`, `v0.2`, `backend`, `database`, `high`

---

## v0.3 - Governanca e controle

- [ ] **Issue 6: Perfis de acesso (Comercial, Compras, Gerencia)**
  - Objetivo: restringir funcoes por perfil.
  - Entrega:
    - login
    - permissao por acao
  - Criterio de aceite:
    - funcoes administrativas bloqueadas para perfis sem acesso
  - Labels: `roadmap`, `v0.3`, `backend`, `security`, `high`

- [ ] **Issue 7: Auditoria de alteracoes**
  - Objetivo: registrar quem alterou o que e quando.
  - Entrega:
    - tabela de logs
    - tela de consulta
  - Criterio de aceite:
    - salvar/editar cotacao gera log com dados auditaveis
  - Labels: `roadmap`, `v0.3`, `database`, `security`, `high`

- [ ] **Issue 8: Backup automatico e restauracao**
  - Objetivo: reduzir risco operacional de perda de dados.
  - Entrega:
    - backup em pasta local com timestamp
    - rotina de restauracao guiada
  - Criterio de aceite:
    - restaurar backup recompõe historico e cotações
  - Labels: `roadmap`, `v0.3`, `backend`, `medium`

- [ ] **Issue 9: Dashboard gerencial**
  - Objetivo: exibir indicadores por periodo.
  - Entrega:
    - lucro medio
    - margem media
    - ticket medio
  - Criterio de aceite:
    - dashboard com filtros de data e dados coerentes
  - Labels: `roadmap`, `v0.3`, `ui-ux`, `analytics`, `medium`

---

## v1.0 - Consolidacao ERP

- [ ] **Issue 10: API para integracao externa**
  - Objetivo: expor operacoes principais por HTTP.
  - Entrega:
    - endpoints para cotacao, historico e cadastro de regra
    - autenticacao de API
  - Criterio de aceite:
    - API documentada e testada (OpenAPI)
  - Labels: `roadmap`, `v1.0`, `backend`, `api`, `high`

- [ ] **Issue 11: Pipeline de release e changelog**
  - Objetivo: padronizar versao e publicacao.
  - Entrega:
    - fluxo de release no GitHub
    - changelog por versao
  - Criterio de aceite:
    - release gerada com tag e notas automaticamente
  - Labels: `roadmap`, `v1.0`, `devops`, `docs`, `medium`

- [ ] **Issue 12: Suite de testes ampliada**
  - Objetivo: aumentar confiabilidade antes de escalar.
  - Entrega:
    - testes unitarios adicionais
    - testes de integracao (repositorio + banco)
    - casos de regressao fiscal/comercial
  - Criterio de aceite:
    - cobertura relevante nos fluxos criticos
  - Labels: `roadmap`, `v1.0`, `qa`, `high`

- [ ] **Issue 13: Documentacao funcional e tecnica completa**
  - Objetivo: facilitar onboarding e manutencao.
  - Entrega:
    - manual rapido de uso
    - guia tecnico de arquitetura
    - padrao de contribuicao
  - Criterio de aceite:
    - time consegue instalar, rodar e evoluir sem dependencia tacita
  - Labels: `roadmap`, `v1.0`, `docs`, `medium`

---

## Ordem sugerida de abertura

1. Issues 1 a 5 (v0.2)
2. Issues 6 a 9 (v0.3)
3. Issues 10 a 13 (v1.0)

## Modelo rapido de descricao de issue

```md
## Contexto
Descreva o problema e o impacto comercial.

## Objetivo
Defina o resultado esperado em linguagem de negocio.

## Escopo
- Item 1
- Item 2

## Criterios de aceite
- [ ] Criterio 1
- [ ] Criterio 2

## Fora de escopo
- Item que nao entra nesta issue
```

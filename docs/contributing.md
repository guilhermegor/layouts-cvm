# **Contribuindo**

Tudo o que é preciso para desenvolver, testar e lançar esta biblioteca.

> **Veja também:** [Uso](usage.md) · [Referência da API](api/index.md) · o `CONTRIBUTING.md` na raiz
> do repositório (em inglês) traz a política oficial de branches, PRs e mensagens de commit.

---

## Preparando o ambiente de desenvolvimento { #setting-up-for-development }

O `poe` é uma dependência de desenvolvimento, então só existe depois que o virtualenv existe. Faça o
bootstrap primeiro pelo ponto de entrada em shell. Nesse primeiro bootstrap, use um shell comum (fora de `poetry run`, do `poe` ou de um venv ativado);
depois, deixe o `poe_exec.sh` encontrar o `poe` do venv para o restante:

```bash
bash bin/venv.sh           # cria o venv do Poetry e instala as dependências, inclusive o poethepoet
bash bin/poe_exec.sh init  # .env (quando o tier traz um), venv, git hooks, utilitários do GitHub
```

`init` combina `ensure_env` (cria o `.env`; aqui é só uma linha informativa, pois uma biblioteca não
traz `.env.example`), `venv` (cria o virtualenv do Poetry e instala **todas** as dependências,
inclusive dev e docs) e `precommit` (instala os git hooks). O Poetry é instalado automaticamente se
não existir. Executar `venv` de novo de dentro do virtualenv do projeto é seguro: ele faz o bootstrap
a partir de um interpretador base e se recusa a apagar o `.venv` em que está rodando.

## Testes e lint { #tests-and-linting }

```bash
poe unit_tests          # poetry run pytest tests/unit/
poe integration_tests   # poetry run pytest tests/integration/
poe lint                # ruff + mypy + codespell + pydocstyle + gates de shell/sql/yaml
```

O CI executa os mesmos gates em todo pull request; mantenha-os verdes localmente antes do push.

## Registrando um novo writer { #registering-a-new-writer }

Um writer aparece em quatro listas (três arquivos), e as quatro usam **uma só chave de ordenação: o nome do submódulo do writer**
(`cda_v3` para `CdaV3`), em ordem ASCII simples. Insira sua entrada na posição ordenada, nunca no
final, para que dois PRs de writer normalmente toquem linhas diferentes e façam merge sem conflito
(dois writers que caiam na mesma posição ainda conflitam: mantenha as duas linhas e reordene):

1. `src/layouts_cvm/__init__.py`: a linha `from layouts_cvm.<module> import <Writer>` e a entrada
   `"<Writer>"` em `__all__` (uma por linha; `__version__` e `main` ficam primeiro).
2. A linha da tabela de layouts no `README.md`.
3. A entrada de `Layouts` no nav do `mkdocs.yml`.

Não escreva uma contagem de layouts em lugar nenhum: é a linha que duas branches mudariam ao mesmo
tempo e que o git juntaria em silêncio em um número errado. `bin/check_readme_layouts.py` falha quando
alguma das listas está fora de ordem. Os schemas são importados do próprio módulo
(`layouts_cvm._internal.config.schemas.<module>`); não há agregador para atualizar.

Se um rebase conflitar em uma dessas listas, mantenha as linhas dos dois lados e reordene pela chave.

## Verificando o pacote gerado { #verifying-the-built-package }

Antes de abrir um PR de release, confirme que o wheel é gerado e importa de fato. Isso pega erros de
empacotamento (um `__init__` ausente, um subpacote de `_internal/` fora do pacote) que testes na
árvore de código nunca revelam:

```bash
poe install_dist_locally    # python -m build → instala → importa como smoke test → informa o wheel gerado
```

## Publicando a documentação (versionada, via mike) { #publishing-the-documentation-versioned-via-mike }

O site publicado é **versionado**: quem está preso a uma release antiga lê a documentação *daquela
release*, não a do HEAD. O [mike](https://github.com/jimporter/mike) mantém a árvore de versões na
branch `gh-pages`, e o MkDocs-Material exibe o seletor de versão.

Dois workflows dividem o trabalho:

| Workflow | Gatilho | O que faz |
|---|---|---|
| `Docs - Strict Build Check` (`docs.yaml`) | todo push e PR | apenas `mkdocs build --strict`, que pega links e nav quebrados antes de uma release. **Nunca faz deploy.** |
| `Release to PyPI` (`release-pypi.yaml`) | release manual | depois de publicar no PyPI com sucesso, faz o deploy da versão lançada com `mike deploy --update-aliases <X.Y> latest` |

Como o deploy roda **depois** da publicação, o site só anuncia versões que foram de fato publicadas.
Observações:

- **A granularidade é `X.Y`**: `1.4.2` e `1.4.7` dividem a entrada `1.4`; o alias `latest` sempre
  acompanha a release mais recente e é a versão de entrada padrão.
- **Pré-releases nunca movem `latest`**: uma versão com sufixo (`1.2.3rc1`) é gerada e publicada, mas
  o job de deploy da documentação é ignorado.

### Configuração única do Pages { #one-time-pages-setup }

O mike serve a partir da **branch `gh-pages`**, então o Pages precisa estar em *Deploy from a branch →
gh-pages*. O `GITHUB_TOKEN` do workflow não consegue mudar isso (é um token de GitHub App sem direitos
de admin no repositório), então faça com a sua própria autenticação do `gh`:

```bash
poe enable_pages
```

Isso já roda dentro de `poe init` (depois do bootstrap) e é **idempotente e não bloqueante**: avisa e
segue em frente se o `gh` estiver ausente ou sem autenticação, se nenhum remote for encontrado ou se
você não for admin do repositório (um fork), de modo que nunca quebra o `init`.

**A ordem importa:** a branch `gh-pages` não existe até o primeiro deploy de release criá-la. Até lá,
`enable_pages` deixa o Pages intocado de propósito (para o site nunca apontar para uma branch vazia)
e avisa para executá-lo de novo. Portanto: crie a primeira release e então execute `poe enable_pages`
uma vez. Alternativa manual: *Settings → Pages → Build and deployment → Source: Deploy from a branch →
`gh-pages` / `/`*.

## Orientação para agentes { #agent-guidance }

Orientações para agentes de código com IA ficam em `AGENTS.md`, que todo agente lê. Um `CLAUDE.md` ao
lado dele é só um stub: importa `@AGENTS.md` e traz a linha `Edit AGENTS.md, not this file.
Claude-Code-only lines go below this one.` Coloque abaixo dessa linha apenas o que é exclusivo do
Claude Code (um hook, um slash command, uma skill). `bin/check_agents_md_pairs.py` garante esse pareamento.

## Pull requests

1. Abra uma issue primeiro, usando o modelo de issue do repositório. Diga o que quer mudar e por quê,
   e liste os arquivos que serão tocados. Em trabalhos não triviais, espere a issue ser aceita antes
   de escrever código.
2. Crie a branch a partir da branch padrão como `<type>/<issue-number>-<slug>` (por exemplo,
   `feat/42-user-authentication`), seguindo a política de prefixos (`feat/…`, `fix/…`, …).
3. Coloque `Closes #<N>` no corpo do PR para que a issue seja fechada no merge.
4. Preencha o modelo de PR por completo.
5. Garanta que as verificações do CI (testes, lint, build da documentação) passem: elas são o gate de merge.

## Lançando uma release { #releasing }

As releases são **guiadas por tag e sem segredos** quando o projeto está ligado a um remote do GitHub:

- As versões seguem o **versionamento semântico** desde a 1.0.0: uma mudança incompatível é um MAJOR,
  uma funcionalidade é um MINOR, e uma correção é um PATCH. A [referência da API](api/reference.md) diz o que conta como
  mudança incompatível.
- A versão é a **tag do git** (via `poetry-dynamic-versioning`); `pyproject.toml` guarda um placeholder
  `0.0.0`. Não o edite à mão. Dispare uma release pela aba Actions (`Release to PyPI` /
  `Release to Test PyPI`, `workflow_dispatch` com a versão) ou enviando uma tag `vX.Y.Z`.
- A versão publicada deriva da tag mais recente no formato `vX.Y.Z`. Em uma tag exata, o build é limpo
  (`0.2.0`); fora de tag, recebe uma versão dev PEP 440. Os workflows de release passam
  `POETRY_DYNAMIC_VERSIONING_BYPASS` para gerar uma versão específica. Faça o build com
  `python -m build` (um frontend PEP 517).
- Uma `version` alterada à mão falha no hook de pre-commit `dynamic-version-stub`
  (`bin/check_dynamic_version_stub.py`): ela contradiz a tag e o índice de pacotes. O hook não faz nada
  em projetos que não habilitam o `poetry-dynamic-versioning`.
- O workflow de release executa a **suíte completa de testes** como gate obrigatório, faz o build com
  `python -m build` e publica por **OIDC trusted publishing** (`pypa/gh-action-pypi-publish`), sem
  precisar de tokens secretos.
- O changelog é regenerado a partir das tags no momento da release ou do build (`poe changelog`
  localmente); o CI nunca faz commit de `CHANGELOG.md` de volta na branch padrão protegida. Notas de
  atualização escritas à mão ficam na GitHub Release, pois o que for escrito no changelog é apagado
  na regeneração.

### Configuração do mantenedor: trusted publisher (uma vez, antes da primeira release) { #maintainer-setup-trusted-publisher-one-time-before-the-first-release }

Registre um **trusted publisher** em **ambos**, [pypi.org](https://pypi.org) e
[test.pypi.org](https://test.pypi.org). Cada campo precisa corresponder exatamente ao workflow, ou o
upload falha com um `invalid-publisher` pouco explicativo:

| Campo | Valor |
|-------|-------|
| Owner / repository | seu `<owner>` / `<repo>` no GitHub |
| Nome do arquivo de workflow | `release-pypi.yaml` (PyPI) / `release-test-pypi.yaml` (Test PyPI) |
| Environment | `release-pypi` / `release-test-pypi` |
| **Project Name** no PyPI | deve ser igual ao nome da distribuição (`name` em `pyproject.toml`) |

A etapa de GitHub Release existe só em `release-pypi.yaml`, não no workflow do Test PyPI, então uma mudança nela nunca é ensaiada; compare os dois workflows ao editar qualquer um.

No primeiro upload, o projeto ainda não existe: registre um **pending publisher** no nível da conta
(não nas configurações de um projeto existente). Publicar de um laptop em vez do CI é o único caso
que ainda exige um token de API; o OIDC só funciona a partir do GitHub Actions.

### Servindo a documentação: primeira release { #serving-the-docs-first-release }

A primeira execução de `release-pypi.yaml` cria a branch `gh-pages` com `mike deploy`. O `GITHUB_TOKEN`
não consegue definir a origem do Pages (o endpoint exige direitos de admin no repositório), então o
job `deploy_docs` mostra a solução no resumo do job. Depois, execute `poe enable_pages` uma vez como
admin do repositório.

### Escolhendo os destinos de publicação { #choosing-publish-targets }

O scaffold liga os workflows de release ao registro público oficial (PyPI) e a um registro de
homologação (Test PyPI). Para publicar em uma origem **privada ou não oficial**, seja uma origem git
(`pip install git+https://…`), um índice privado PEP 503 ou (nos ecossistemas que aceitam) o GitHub
Packages, configure a origem do lado do consumidor em `pyproject.toml`, com uma proteção de prioridade
explícita contra dependency confusion (`priority = "explicit"` do `poetry`; `pip --index-url`, nunca
`--extra-index-url`).

## Identidade visual do site { #branding-the-docs-site }

O site usa o emblema da CVM em `docs/assets/cvm-logo.png`, uma cópia de `assets/cvm-logo.png` do
README. Ele é usado como logo do cabeçalho e favicon (`theme.logo` / `theme.favicon` no `mkdocs.yml`)
e como imagem de abertura em `docs/index.md`. As quatro referências precisam apontar para a mesma
imagem, byte a byte: o hook de pre-commit `check-logo-sync` (`bin/check_logo_sync.py`) falha a menos
que a imagem do README, o `<img>` de `docs/index.md`, `theme.logo` e `theme.favicon` existam e sejam
idênticos. Para trocá-lo:

1. Substitua `assets/cvm-logo.png` e copie-o sobre `docs/assets/cvm-logo.png` (mantenha o nome do
   arquivo, ou atualize os dois caminhos do `mkdocs.yml` e o `<img>` de `docs/index.md`).
2. Ajuste tamanho, posição e borda diretamente no `<img>`: `width="200"` (escala), `align="right"`
   (posição) e `style="border-radius: 15px;"` (cantos arredondados), em `docs/index.md`.
3. Defina a cor do cabeçalho em `docs/stylesheets/brand.css` (`--md-primary-fg-color`, mais a variante
   `slate` do modo escuro) para combinar.

## Proteção e segurança do repositório (uma vez, por script) { #repository-protection-security-one-time-scripted }

`poe init` executa três utilitários que exigem admin. São **idempotentes e não bloqueantes**: sem
`gh`, sem autenticação, sem remote no GitHub ou sem direitos de admin, eles avisam e pulam a etapa, de
modo que o `init` termina mesmo para contribuidores e scaffolds offline. Execute qualquer um deles
sozinho depois:

| Alvo | O que provisiona |
|--------|--------------------|
| `poe enable_pages` | Origem do GitHub Pages (branch gh-pages para documentação versionada, senão Actions) |
| `poe enable_repo_rules` | O ruleset de branch `pr-quality-gate` + as configurações de merge que o gate de PR precisa |
| `poe enable_security` | Relato privado de vulnerabilidades, alertas do Dependabot, atualizações de segurança do Dependabot |

### O ruleset `pr-quality-gate` { #the-pr-quality-gate-ruleset }

Aplicado a `~DEFAULT_BRANCH` (essa ref sobrevive a uma renomeação de branch) e buscado **pelo nome**,
para que uma nova execução atualize no lugar em vez de criar um duplicado:

| Regra | Configuração | Por quê |
|------|---------|-----|
| `pull_request` | `required_approving_review_count: 0` | ⚠️ **Precisa ser 0.** O GitHub proíbe aprovar o próprio PR, então qualquer valor ≥ 1 impede quem mantém o projeto sozinho de fazer merge do próprio trabalho. Zero ainda força toda mudança a passar por um PR, e essa é a proteção real. |
| `pull_request` | `required_review_thread_resolution: true` | Torna os comentários de revisão **obrigatórios**: uma thread não resolvida bloqueia o merge, em vez de ser decorativa. |
| `code_scanning` | CodeQL, segurança `high_or_higher`, alertas `errors` | Os alertas ficam em `errors`: `errors_and_warnings`/`all` passam a bloquear merges por consultas de estilo, duplicando ruff/mypy com ruído. |
| `copilot_code_review` | `review_on_push: true` | É um **tipo de regra próprio**, não um parâmetro de `pull_request` (isso retorna HTTP 422 e faz o recurso parecer exclusivo da interface). |
| `non_fast_forward`, `deletion` | ligados | Sem force-push e sem apagar a branch padrão. |
| `required_status_checks` | **vazio por padrão** | ⚠️ De propósito. Uma verificação obrigatória cujo nome nunca é reportado bloqueia **todo** PR para sempre. Preencha `REQUIRED_CHECKS` em `bin/enable_repo_rules.sh` a partir de um PR real (`gh api repos/:owner/:repo/commits/<sha>/check-runs --jq ".check_runs[].name"`) e execute de novo. |

**Deliberadamente não habilitados:** *Require code quality results* (severidade subjetiva de IA no
caminho do merge; ruff, mypy e os gates `bin/check_*.py` já garantem a qualidade de forma
determinística) e *Restrict code coverage* (em prévia; o piso tem fonte única em `.coveragerc`
`fail_under`).

### Automático ou manual: a fronteira é configuração do repositório × plano da conta { #automatic-vs-manual-the-boundary-is-repo-config-vs-account-plan }

**Nada aqui precisa de clique.** Toda configuração de *repositório* acima é feita por script. O que
**não** dá para automatizar é o direito da sua *conta*: a regra `copilot_code_review` só dispara se o
autor tiver acesso ao Copilot code review, e o **code review não faz parte do Copilot Free**. Sem um
plano elegível, a regra fica corretamente configurada e **inerte**: nenhuma revisão aparece e nada dá
erro. Esse silêncio é a armadilha, porque o JSON do ruleset parece perfeito de qualquer forma.

Todas as outras regras (PR obrigatório, CI verde, CodeQL limpo) funcionam com qualquer plano do
Copilot, então vale aplicar o ruleset sempre. O Copilot Pro é gratuito para estudantes e professores
verificados e para mantenedores de projetos populares de código aberto.

> **Não** diagnostique isso com `gh api user/copilot_billing` → 404: esse endpoint é para gestão de
> licenças de organização/empresa e retorna 404 para uma conta pessoal mesmo com o Copilot Free ativo.

### Segurança { #security }

`SECURITY.md` na raiz do repositório é detectado automaticamente pelo GitHub (sem chamada de API) e
muda *Security policy* para Enabled; `poe enable_security` liga o canal privado de relato
correspondente, além dos alertas e das atualizações de segurança do Dependabot. Atualizações comuns
de versão são à parte: veja `.github/dependabot.yml`, que usa `versioning-strategy: lockfile-only`
para atualizar o `poetry.lock` (mantendo o CI fiel ao que os consumidores instalam) sem nunca
reescrever as faixas do seu `pyproject`.

## Fluxo automatizado de PR (o gate de qualidade) { #automated-pr-flow-the-quality-gate }

Todo PR é classificado por `bin/pr_gate.py` (workflow `pr-gate.yaml`), que aplica labels, publica um
comentário fixo com uma tabela de status por eixo e entrega as **classes seguras** ao auto-merge nativo
do GitHub. Duas regras são todo o desenho:

**Classificado por CAMINHO, nunca pelo tamanho do diff.** A mudança perigosa é *semântica*, não grande:
editar um caractere de uma constante de schema ou contrato é o menor diff possível e o mais perigoso,
e todos os testes continuam passando, porque eles verificam o contrato que foi escrito. Por isso, o
tamanho nunca decide a elegibilidade; os caminhos alterados decidem. (O único lugar em que o tamanho
ainda importa, o veto a um diff `XL`, é **dispensado para um diff só de lockfile**, cuja contagem de
linhas acompanha quantos hashes de dependência mudaram, não o risco.)

| Classe de risco | Caminhos | Auto-merge? |
|------------|-------|-------------|
| `src` | `src/` | ❌ define o que significa "passar" |
| `tests` | `tests/` | ❌ define o que significa "passar" |
| `other` | qualquer caminho sem correspondência | ❌ desconhecido = inseguro (nega por padrão) |
| `ci` | `.github/`, `bin/`, `Makefile`, `tasks.sh`, `.pre-commit-config.yaml` | ✅ |
| `deps` | `pyproject.toml`, `poetry.lock`, `requirements.txt` | ✅ (a suíte de testes é o gate) |
| `docs` | `docs/`, `mkdocs.yml`, `README.md`, `CHANGELOG.md`, … | ✅ |

**O consentimento é opt-OUT.** As classes seguras fazem auto-merge **sem label**; adicione
`do-not-merge` para forçar um merge humano. O auto-merge nativo **não contorna nada**: o GitHub segura
o merge até que toda verificação obrigatória do ruleset esteja verde, então o gate só decide a
*elegibilidade*, nunca *se passou*.

Edite a tabela de risco (a constante `RISK_PATHS`) em `bin/pr_gate.py` conforme a estrutura real do seu projeto.

### ⚠️ Depois de mudar a política do gate, reavalie os PRs abertos { #after-changing-gate-policy-backfill-the-open-prs }

O gate roda em eventos `pull_request`, então um PR que **já estava aberto** quando a política mudou
(as regras de classificação e consentimento em `pr_gate.py`, ou `allow_auto_merge` /
`delete_branch_on_merge`) **nunca é reavaliado**: mantém os labels e o estado de auto-merge das regras
antigas até que algum evento novo o toque. Não é um bug; o gate simplesmente não rodou de novo. Por
isso, depois do merge de uma mudança de política, execute o backfill:

```bash
gh workflow run pr-gate.yaml -f backfill=true   # reavalia todos os PRs abertos
# em um PR do Dependabot, `gh pr comment <n> --body "@dependabot rebase"` também funciona
```

### PRs com merge por bot e o reconciliador { #bot-merged-prs-and-the-reconciler }

Um PR com merge por **auto-merge nativo** (uma ação de bot) **não** fecha a issue ligada e **não**
apaga a branch, mesmo com `delete_branch_on_merge` ligado: ações de bot são deliberadamente inertes
para evitar recursão de automação. `pr-reconcile.yaml` resolve as duas coisas: fecha as issues de
`Closes #N` e apaga a branch dos PRs com merge feito. Sua **execução diária agendada é a correção de
fato**: eventos agendados ficam isentos da supressão "no new workflow runs", que também engole o
caminho rápido de `pull_request: [closed]` em um merge por bot. A latência chega a um dia; esse é o
custo aceito de não precisar de um personal access token.

### O gate do registro de trabalho { #the-work-ledger-gate }

`bin/check_backlog_ledger.py` (pre-commit + CI) falha em uma branch que toca `src/` ou caminhos de CI
mas não adiciona um registro `.specs/backlog/<kebab>_YYYYMMDD_HHMMSS.md` com um checklist `- [ ]`,
tornando estrutural a convenção de registro de trabalho por branch, em vez de algo a ser lembrado.
Branches rotineiras só de docs, dependências ou testes não precisam dele.

# **Registros de incidentes**

O que quebrou neste projeto, e o que mudou para que não possa quebrar da mesma forma de novo. Esta
página mantém o conhecimento de depuração dentro do código, em vez de no histórico do git e na
memória de uma pessoa: um conhecimento que a equipe já pagou uma vez não deveria ser pago duas.

> **Veja também:** [Uso](usage.md) · [Contribuindo](contributing.md) · [Histórico de versões](changelog.md).

## Não é um ADR, nem um repositório de lições { #not-an-adr-and-not-a-lessons-store }

Um **ADR** registra uma decisão tomada *antes* de algo dar errado. Um registro de incidente documenta
uma decisão tomada *porque* algo já deu errado: gatilho diferente, público diferente. Se este projeto
adotar ADRs no futuro, mantenha os dois separados em vez de misturá-los.

Também não é uma cópia do repositório de "lições aprendidas" de uma ferramenta de scaffolding. Esse
tipo de repositório responde "o que todo projeto gerado no futuro deve herdar"; esta página responde
"o que mordeu *este* código, e o que fizemos a respeito". Público diferente, tempo de vida diferente.

## Publicado de propósito: oculte dados antes de escrever { #published-on-purpose-redact-before-you-write }

Esta página vai para o site publicado da documentação, assim como [Uso](usage.md). Um incidente pode
trazer detalhes de produção (um hostname, uma consulta, um sintoma visto por clientes) que não devem
chegar a um site público: oculte ou generalize esses dados antes de fazer o commit da entrada, como um
postmortem externo omite detalhes internos. Se o site deste projeto for de fato público e as entradas
não puderem ficar sem esses dados, exclua `incidents.md` via `exclude_docs` no `mkdocs.yml` em vez de
deixá-lo pela metade.

## Formato { #format }

Cinco campos, nesta ordem. Mantenha cada um em poucas frases: a entrada deixa de ser escrita no dia
em que leva uma hora para ser preenchida.

- **Sintoma** — o que foi observado, não o que estava errado.
- **Como foi encontrado** — a ferramenta, o comando ou o acaso que o revelou; "fomos cuidadosos" não
  cabe aqui.
- **Causa raiz** — medida, não presumida.
- **A mudança** — o que agora torna essa classe de falha impossível, ou ruidosa em vez de silenciosa.
- **Como saberíamos que voltou** — o gate, teste ou asserção que a pegaria de volta.

---

## MODELO — substitua pelo primeiro incidente real deste projeto { #template-replace-with-this-projects-first-real-incident }

Apague esta seção quando tiver uma entrada própria. Ela fica aqui só para mostrar como é uma entrada
preenchida: uma página vazia ensina a quem lê que não há nada para ler aqui.

### 2026-08-16 — Reconfigurar o logger vazava um file handle a cada vez { #2026-08-16-reconfiguring-the-logger-leaked-a-file-handle-every-time }

**Sintoma.** Objetos `logging.FileHandler` se acumulavam durante a vida do processo sempre que o
logger era reconfigurado (por exemplo, ao passar para um novo arquivo de log datado). Inofensivo em
um script curto; em um serviço de longa duração, os descritores de arquivo vazados vão se acumulando.

**Como foi encontrado.** Não pela suíte de testes: o `ResourceWarning` não aparece por padrão no
Python. Só surgiu quando a suíte rodou com `-W always`, durante a medição de outra coisa. O defeito
era invisível por construção, não por descuido de alguém.

**Causa raiz.** O caminho de reconfiguração chamava `logger.handlers.clear()` para desligar o handler
antigo antes de ligar um novo. Limpar a lista descarta a *referência* do Python, mas não fecha o
descritor de arquivo do sistema operacional, que continua aberto até a coleta de lixo.

**A mudança.** Fechar explicitamente cada handler existente antes de desligá-lo, para que o descritor
seja liberado na hora, e não na coleta de lixo. Um só ponto de chamada: `handlers.clear()` aparecia
exatamente uma vez em todo o código, então nenhum chamador irmão ficou sem correção.

**Como saberíamos que voltou.** Um teste reconfigura o logger duas vezes e verifica que `.stream is
None` no primeiro handler após a segunda chamada: `close()` define esse atributo no momento em que o
descritor é liberado, então a asserção não depende do momento da coleta de lixo.
⚠️ Medido à parte: promover apenas `ResourceWarning` a `error:` no `pytest.ini` **não** pega isso
sozinho. O aviso é levantado em `__del__`, um contexto *unraisable* que o pytest rebaixa para
`PytestUnraisableExceptionWarning`, então as duas classes de aviso precisam ser promovidas juntas, ou
a suíte continua passando por cima de um vazamento real.

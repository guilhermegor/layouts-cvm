# **Perguntas frequentes**

Respostas a perguntas comuns sobre o uso e o desenvolvimento desta biblioteca. Adicione entradas
específicas do projeto à medida que surgirem em issues.

> **Veja também:** [Uso](usage.md) · [Exemplos](examples.md) · [Contribuindo](contributing.md).

---

## Como instalo? { #how-do-i-install-it }

```bash
pip install layouts-cvm
```

## Como adiciono ou atualizo uma dependência? { #how-do-i-add-or-update-a-dependency }

Use o Poetry, para que o lock file continue sendo a referência:

```bash
poetry add <package>          # dependência de execução
poetry add --group dev <package>   # ferramenta só de desenvolvimento
```

Todo pacote que o código importa deve ser uma dependência **direta**; nunca conte com ele chegando
de forma transitiva por outro pacote.

## Quais versões do Python são suportadas? { #which-python-versions-are-supported }

Veja a restrição `python = "..."` em `pyproject.toml`; o CI executa a matriz de testes em cada uma.

## Como a versão é determinada? { #how-is-the-version-determined }

A versão é a **tag do git** (via poetry-dynamic-versioning); `pyproject.toml` guarda um placeholder
`0.0.0`. Crie uma release pelo workflow de release; veja [Contribuindo](contributing.md).

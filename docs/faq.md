# **Perguntas frequentes**

Respostas a perguntas comuns sobre o uso e o desenvolvimento desta biblioteca. Adicione entradas
específicas do projeto à medida que surgirem em issues.

> **Veja também:** [Uso](usage.md) · [Exemplos](examples.md) · [Contribuindo](contributing.md).

---

## Como instalo?

```bash
pip install layouts-cvm
```

## Como adiciono ou atualizo uma dependência?

Use o Poetry, para que o lock file continue sendo a referência:

```bash
poetry add <package>          # dependência de execução
poetry add --group dev <package>   # ferramenta só de desenvolvimento
```

Todo pacote que o código importa deve ser uma dependência **direta**; nunca conte com ele chegando
de forma transitiva por outro pacote.

## Quais versões do Python são suportadas?

Veja a restrição `python = "..."` em `pyproject.toml`; o CI executa a matriz de testes em cada uma.

## Como a versão é determinada?

A versão é a **tag do git** (via poetry-dynamic-versioning); `pyproject.toml` guarda um placeholder
`0.0.0`. Crie uma release pelo workflow de release; veja [Contribuindo](contributing.md).

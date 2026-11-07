# **Histórico de versões**

Histórico de releases deste projeto. As entradas são geradas a partir de mensagens
[Conventional Commit](https://www.conventionalcommits.org/) pelo
[commitizen](https://commitizen-tools.github.io/commitizen/), de modo que os títulos de versão
abaixo acompanham o que de fato foi publicado. Por virem dos commits, as entradas ficam em inglês.

**Como é atualizado:** as seções abaixo são geradas pelo `cz changelog` a partir das tags e do
histórico de commits. A página publicada é regenerada **a cada build da documentação** (o workflow
de docs executa `cz changelog` antes de `mkdocs build`), então sempre reflete a branch padrão: o CI
nunca faz commit de `CHANGELOG.md` de volta no repositório, e o arquivo nunca é editado à mão. Para
regenerar ou pré-visualizar localmente, use `poe changelog`.

---

<!-- Single-sourced from the repo-root CHANGELOG.md — never edit the entries here by hand. -->
--8<-- "CHANGELOG.md"

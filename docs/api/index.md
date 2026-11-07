# **Referência da API**

A interface pública, agrupada pela própria divisão de primeiro nível do código.

> **Veja também:** [Uso](../usage.md)

## Páginas { #pages }

| Grupo | Conteúdo |
|-------|----------|
| [Referência](reference.md) | A superfície pública e a garantia de API da 1.x |

## Fazendo esta seção crescer { #growing-this-section }

Isto é um **diretório, não uma página única**, de propósito. Uma referência de API cresce a cada
unidade publicada, então um único `api.md` vira a maior página do repositório; dividi-lo depois é
fácil, mas **quebra todo deep link publicado**, e para sempre quando há documentação versionada,
porque `/<version>/api/#anchor` continua existindo. O custo de começar como diretório é um arquivo
a mais e um nível a mais de navegação, pagos uma única vez.

Ao adicionar páginas:

- **Agrupe pela própria divisão de primeiro nível do código; nunca invente uma taxonomia paralela**
  (por exemplo, uma página por módulo público, espelhando a divisão do pacote). Assim, quem conhece o pacote consegue adivinhar a URL, e a documentação não se
  afasta de uma estrutura que ela espelha.
- **A profundidade segue a contagem, não o gosto.** O eixo real escolhe as seções; só o volume
  decide se uma seção precisa de um segundo nível.
- Um texto comum a um grupo fica uma única vez na página desse grupo, sem repetição por item.
- **Registre cada página nova no `nav:` do `mkdocs.yml` no mesmo commit.** O MkDocs gera mesmo uma
  página não registrada, que apenas some da navegação: é assim que uma página desaparece em
  silêncio (e é isso que o gate `check_docs_sections.py` existe para detectar).

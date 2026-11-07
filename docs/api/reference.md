# **Referência da API**

Interface pública desta biblioteca.

> **Veja também:** [Uso](../usage.md) · [Exemplos](../examples.md)

---

## A superfície pública { #the-public-surface }

A API pública é o que `layouts_cvm.__all__` lista: `__version__` e uma classe de writer por layout
da CVM. As [páginas de layout](../cadastro_ativos.md) documentam os campos de cada writer.

```python
from layouts_cvm import InformeDiario, __version__
```

Tudo em `layouts_cvm._internal` é privado, inclusive os modelos de documento. Esse código vai no
wheel para que os imports funcionem, e pode mudar em qualquer release.

### `Writer().export(doc, output_path=None)`

| Argumento | Significado |
|----------|---------|
| `doc` | Um mapeamento com os campos do layout. É validado antes de qualquer serialização. |
| `output_path` | Onde gravar o arquivo. Quando omitido, o texto é retornado. |

Retorna o texto do arquivo como `str`, ou `None` depois de gravar em `output_path`. Os layouts XML
são windows-1252; `Cofi4010` e `Cofi4016` gravam registros `.cvm` em ASCII de largura fixa. `DemonstrativoFar.export`
também aceita o argumento somente nomeado `require_all_movements`, desligado por padrão; quando ligado, um fundo
incompleto levanta `ValueError`.

Um documento inválido levanta `pydantic.ValidationError`.

---

## A garantia da 1.x { #the-1x-guarantee }

As versões seguem o [versionamento semântico](https://semver.org/) desde a 1.0.0. Dentro da 1.x:

- Um nome em `__all__` não é removido nem renomeado, e uma chamada a `export` que funciona continua
  funcionando. Novos argumentos opcionais somente nomeados podem ser adicionados.
- Uma nova versão de um layout da CVM chega como um novo writer, e o writer antigo permanece.
- Cada writer continua preso à versão de layout que grava hoje. Um nome sem sufixo de versão não é
  um apelido para "a mais recente": `Lamina` continua sendo a Lâmina V3, e `PerfilMensal`, o
  Perfil Mensal V4.
- Um documento que um writer aceita não é recusado depois, salvo se as regras da própria CVM o
  exigirem. Esse caso é destacado nas notas de release.
- Os tipos de exceção acima não mudam. O texto das mensagens de erro pode mudar.

Uma mudança que quebre qualquer um desses pontos é uma 2.0.

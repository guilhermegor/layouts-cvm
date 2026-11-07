# Lançando a 1.0.0

A 1.0.0 é o momento em que esta biblioteca promete sua API pública. Até lá valem as regras da 0.x:
uma mudança incompatível é um bump MINOR, e uma funcionalidade ou correção é um PATCH. A partir da
1.0.0, vale o versionamento semântico completo. Duas coisas precisam ser verdade nesse momento e são
fáceis de errar à mão: o backlog está concluído, e a documentação descreve o código que de fato é
publicado.

## O caminho { #the-path }

1. Abra a issue **Cut 1.0.0** a partir do modelo de issue. Ela é criada como `state:blocked`,
   bloqueada por todas as outras issues abertas.
2. Implemente o backlog. Uma issue que não entrará na 1.0.0 recebe o label `post-1.0`, definido pelo
   dono do projeto (crie-o uma vez com `gh label create post-1.0`), para que fique adiada de forma registrada em vez de descartada.
3. Siga o checklist da issue: a auditoria da documentação, os exemplos executáveis, a tabela de
   versões suportadas da 1.x em `SECURITY.md` e, depois, o ensaio e a publicação.
4. Depois da release, mude a política de versões documentada para o versionamento semântico completo.

## O gate de release { #the-release-gate }

O workflow de release executa `bin/check_release_gate.py` antes de publicar. Ele só se aplica quando
o MAJOR pedido é pelo menos 1 e a última versão publicada é 0.x. Nesse caso, lista as issues abertas
e falha enquanto alguma não tiver o label `post-1.0`, citando cada uma.

- Pull requests não contam, nem a própria issue **Cut 1.0.0**.
- As issues são lidas pela API REST do GitHub com o token do workflow, somente para leitura.
- Se a API não puder ser lida, o gate falha fechado: bloqueia a release em vez de adivinhar.
- Qualquer outro bump, como de 0.4.0 para 0.5.0 ou de 1.0.0 para 1.0.1, não é afetado.
- Uma primeira publicação conta como vinda de 0.0.0, então um projeto cuja primeira release é a 1.0.0 também passa pelo gate.

Para passar, implemente cada issue citada ou aplique a ela o label `post-1.0`, e execute o workflow de novo.

# 📚 StudyTrack — Gerenciador de Estudos (versão 3.0)

Aplicação de estudo pessoal desenvolvida em **Python**, com interface **Streamlit**, persistência local em **SQLite**, relatórios, metas, tarefas e testes automatizados. Projeto de portfólio com código aberto para leitura, estudo e adaptação.

> **Uso local:** não é um serviço online nem um aplicativo multiusuário. Não há login, sincronização ou autenticação. O aplicativo foi configurado para abrir apenas no computador (`127.0.0.1`). Não o publique na internet como está.

## Funcionalidades

| Área | Funcionalidades |
| --- | --- |
| 📊 Painel | indicadores de tempo, sessões, questões, acertos, gráficos dos últimos 30 dias e metas |
| 📚 Matérias | criar, listar, renomear e excluir matérias vazias; evitar nomes duplicados |
| ⏱️ Estudo | registrar minutos, data e observação |
| 🧠 Questões | registrar questões, acertos, data e assunto |
| 🎯 Metas | definir metas semanais por matéria e visualizar o progresso de segunda a domingo |
| ✅ Tarefas | criar, priorizar, concluir, reabrir e excluir tarefas |
| 🗂️ Histórico | filtrar por matéria/data/tipo; editar e excluir registros com confirmação |
| 📤 Dados | exportar resumo e histórico em CSV; baixar backup SQLite |
| 🧪 Qualidade | 16 testes automatizados no banco de dados, incluindo compatibilidade com versões antigas |

## Comece em 3 comandos — Windows

Abra esta pasta no VS Code e, no terminal PowerShell, execute:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

O navegador abrirá o painel, normalmente em `http://127.0.0.1:8501`.

Para executar os testes:

```powershell
py -m unittest discover -s tests -v
```

Para abrir a versão alternativa em **terminal**, sem instalar as bibliotecas da interface:

```powershell
py main.py
```

**Requisitos:** Python 3.10+ e internet apenas na instalação inicial das bibliotecas.
Se `py` não existir, tente `python` nos comandos. Se o pip falhar, confira a conexão e a versão do Python.

📘 **Instalação e migração detalhadas:** veja [`GUIA_WINDOWS.md`](GUIA_WINDOWS.md).

## Como testar em 5 minutos

1. **Matérias:** cadastre `Python`.
2. **Registrar estudo:** escolha Python, digite 45 minutos e salve.
3. **Registrar questões:** escolha Python, digite 10 questões e 8 acertos.
4. **Painel:** confira 45 minutos e 80% de acerto na matéria, caso seja a única registrada.
5. **Tarefas / Metas:** adicione uma tarefa e uma meta semanal de 120 minutos.
6. **Histórico:** corrija uma sessão e exporte o CSV.
7. **Exportar e backup:** faça o backup e feche/reabra o aplicativo; seus registros devem continuar.

Se já houver dados no banco, os totais serão acumulados e podem não ser exatamente os do exemplo.

## Compatibilidade com as versões 1.0 e 2.0

O aplicativo continua usando o arquivo `studytrack.db`. Ao abrir, adiciona as estruturas novas **sem apagar** os dados existentes. Não há mesclagem automática de dois bancos distintos.

Para trazer o histórico anterior: **feche todas as versões**, faça cópia do banco antigo e copie `studytrack.db` para esta pasta **antes da primeira utilização**, preservando um backup. Nunca sobrescreva um banco novo que já contenha registros que queira manter. Veja o guia detalhado.

## Tecnologias

- **Python:** regras de negócio e validações.
- **SQLite:** dados locais com consultas SQL parametrizadas e migração incremental.
- **Streamlit + Pandas:** formulários, tabelas e gráficos.
- **unittest:** testes automatizados e proteção contra regressões.
- **Git / GitHub:** histórico de mudanças e divulgação do projeto.

## Estrutura de arquivos

```text
StudyTrack/
├── app.py                   # Painel visual (Streamlit)
├── main.py                  # Interface alternativa no terminal
├── database.py              # Dados, validações e cálculos
├── requirements.txt         # Dependências da interface
├── GUIA_WINDOWS.md          # Instalação detalhada e publicação
├── tests/
│   ├── test_legacy.py       # Testes de funcionalidades antigas
│   └── test_features.py     # Testes de funcionalidades novas
├── .streamlit/config.toml   # Tema e acesso somente local
├── .github/workflows/tests.yml # Testes no GitHub Actions
├── .gitignore               # Exclui dados pessoais e arquivos temporários
└── LICENSE                  # Licença MIT
```

O banco de dados é gerado automaticamente na primeira inicialização e **não faz parte do projeto distribuído**.

## Segurança e limitações

- **Não envie `studytrack.db`, backups, senhas, tokens ou registros pessoais para o GitHub.** O `.gitignore` ajuda a proteger esses arquivos, mas confira sempre antes de executar `git add`.
- O aplicativo é **local**, voltado ao uso individual; não tem login, usuários, permissões ou sincronização.
- A exportação CSV neutraliza entradas que poderiam ser interpretadas como fórmulas por planilhas.
- A exclusão de registros e a restauração de backup têm efeito permanente; revise antes de confirmar.
- O módulo de metas acompanha minutos por semana, não mede concentração, qualidade de aprendizagem ou desempenho futuro.
- A interface gráfica precisa ser validada no seu navegador e no Windows após a instalação das bibliotecas; os testes automatizados cobrem a camada de dados.

## Como citar no currículo

> **StudyTrack — Gerenciador de Estudos:** aplicativo Python com interface Streamlit e banco SQLite, cadastro de matérias, análise de desempenho, metas semanais, tarefas e relatórios. Projeto desenvolvido e validado com assistência de IA, com documentação e testes automatizados.

Adapte a descrição para representar **somente o trabalho que você efetivamente realizou e consegue explicar**. IA foi utilizada como apoio à concepção, geração inicial e revisão do código; a autoria não deve ser descrita como exclusivamente manual.

## Próximos passos de estudo

Depois de compreender o sistema, melhorias possíveis: implantação segura de uma demonstração com dados fictícios, autenticação e multiusuário, testes de interface e uma API REST independente. Esses itens **não fazem parte desta versão local**.

## Licença

Código sob licença MIT, consulte [`LICENSE`](LICENSE).

# Guia de instalação — StudyTrack 3.0 (Windows + VS Code)

Este guia contém todas as etapas de uma vez. Você não precisa executar o programa após cada modificação.

## 1. Abra o projeto

1. Extraia `StudyTrack_FINAL.zip` na pasta **Documentos**.
2. No **VS Code**, clique em **Arquivo → Abrir Pasta** e selecione a pasta `StudyTrack` que contém `app.py`.
3. Clique em **Terminal → Novo Terminal**. O PowerShell deve aparecer na parte inferior.

## 2. Instale as bibliotecas

Digite exatamente:

```powershell
py -m pip install -r requirements.txt
```

Se aparecer `No module named pip`, use `py -m ensurepip --upgrade` e repita. Se `py` não for reconhecido, tente `python -m pip install -r requirements.txt`.

As bibliotecas instaladas são **Streamlit** (interface) e **Pandas** (tabelas e gráficos). É normal que a instalação baixe outras dependências.

## 3. Abra a interface gráfica

```powershell
py -m streamlit run app.py
```

O navegador normalmente abrirá `http://127.0.0.1:8501`. Se não abrir, copie esse endereço para a barra de endereços do navegador.

**Para fechar:** pressione `Ctrl + C` no terminal que está executando o Streamlit.

## 4. Teste o programa completo

- Abra **Matérias** e cadastre `Português` ou `Python`.
- Em **Registrar estudo**, informe 45 minutos.
- Em **Registrar questões**, informe 10 questões com 8 acertos.
- No **Painel**, confira seus registros e a taxa de 80% para esse lançamento.
- Em **Metas semanais**, defina 120 minutos para a matéria.
- Em **Tarefas**, cadastre uma tarefa de revisão e conclua-a.
- Em **Histórico**, filtre a data, corrija um registro e exporte o CSV.
- Em **Exportar e backup**, salve um arquivo de cópia de segurança.
- Feche e abra novamente: o histórico deve persistir.

Se já houver registros anteriores, os totais agregados não serão iguais aos números do exemplo.

## 5. Levar seus dados da versão antiga

**Importante: faça isso antes de cadastrar dados novos na versão final.**

1. Feche o terminal do `main.py`, a interface do Streamlit e o VS Code, se estiver usando o app.
2. Na pasta **antiga** do StudyTrack, localize `studytrack.db` (o Windows pode mostrar apenas `studytrack`).
3. Faça uma cópia do arquivo e guarde-a em outra pasta como backup.
4. Copie `studytrack.db` para a nova pasta `StudyTrack`, na qual estão `app.py` e `database.py`.
5. **Não substitua** um banco novo que já tenha dados importantes. Esta versão não mescla automaticamente dois arquivos `.db`.
6. Abra o painel; as matérias, sessões e questões anteriores deverão ser reconhecidas automaticamente.

O programa adicionará novas tabelas e campos quando abrir. Na primeira migração, a cópia de segurança é especialmente importante.

## 6. Executar os testes de programação

Feche o Streamlit (`Ctrl + C`) e execute no terminal:

```powershell
py -m unittest discover -s tests -v
```

Você deverá ver os testes concluídos com `OK`. Eles criam bancos **temporários**, sem modificar suas matérias reais.

## 7. Publicar código no GitHub com segurança

Antes de publicar, confira que `studytrack.db`, cópias `.db`, relatórios pessoais e `.env` **não estão incluídos**. Não publique backups com seus registros.

Se Git já estiver instalado e você tiver um repositório vazio no GitHub:

```powershell
git init
git add .
git status
git commit -m "feat: primeira versao publica do StudyTrack"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
git push -u origin main
```

Substitua o endereço de exemplo pelo URL do **seu** repositório. O comando `git status` é uma etapa de segurança: verifique que **nenhum banco de dados** foi adicionado. Se Git pedir nome/e-mail, configure sua identidade do Git segundo sua preferência. Caso o repositório já exista ou tenha arquivos, siga o fluxo adequado sem sobrescrever trabalho existente.

## Problemas frequentes

| Mensagem | Como resolver |
|---|---|
| `No module named streamlit` | Execute `py -m pip install -r requirements.txt`. |
| `No module named pandas` | Repita a instalação das dependências com o mesmo Python usado para abrir o app. |
| `py` não reconhecido | Use `python` ou confira a instalação do Python. |
| `Address already in use` | Encerre a sessão anterior com `Ctrl + C`, ou inicie na porta 8502: `py -m streamlit run app.py --server.port 8502`. |
| O programa antigo não aparece | Use `py main.py` para abrir o menu em terminal; `app.py` é a versão com interface visual. |
| Minha matéria sumiu | Confira se você abriu o programa na pasta correta e se copiou o `studytrack.db` certo. Não crie dados novos até identificar o arquivo antigo. |

**Uso responsável:** o StudyTrack foi feito para aprender programação e gerenciar estudos localmente. A interface gráfica não foi criada para acesso público ou múltiplos usuários.

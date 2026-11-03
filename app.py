"""Interface web local do StudyTrack — versão 3.0.

Execute com: py -m streamlit run app.py
Os dados permanecem no SQLite local; não há autenticação ou nuvem.
"""
from __future__ import annotations

import csv
from datetime import date, timedelta, datetime
from io import StringIO
import sqlite3

import pandas as pd
import streamlit as st

import database as db

st.set_page_config(
    page_title="StudyTrack | Gestão de estudos",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.initialize_database()

st.markdown("""
<style>
.block-container {max-width: 1230px; padding-top: 1.7rem; padding-bottom: 4rem;}
.stApp {background: #f5f7fc; color: #12213c;}
[data-testid="stSidebar"] {background: #10213e;}
[data-testid="stSidebar"] * {color: #e7edfa !important;}
[data-testid="stMetric"] {background: #fff; padding: 1rem 1.2rem;
  border-radius: 13px; border: 1px solid #e2e9f3;}
.hero {background: linear-gradient(110deg, #17345c, #245e9b);
  color: white; padding: 1.6rem 1.9rem; border-radius: 16px; margin-bottom: 1.3rem;}
.hero h1 {font-size: 2.1rem; color: white; margin: 0;}
.hero p {color: #d8e9ff; margin: .4rem 0 0;}
</style>
""", unsafe_allow_html=True)

PAGES = ["🏠 Painel", "📚 Matérias", "⏱️ Registrar estudo", "🧠 Registrar questões",
         "🎯 Metas semanais", "✅ Tarefas", "🗂️ Histórico", "💾 Exportar e backup"]


def flash(message):
    st.session_state["flash_message"] = message
    st.rerun()


def minutes_label(value):
    hours, minutes = divmod(int(value), 60)
    return f"{hours}h {minutes:02d}min" if hours else f"{minutes}min"


def percent(correct, total):
    return 100 * correct / total if total else 0


def safe_csv(value):
    txt = str(value)
    return "'" + txt if txt.lstrip().startswith(("=", "+", "-", "@")) else txt


def create_csv(headers, rows):
    result = StringIO()
    writer = csv.writer(result, delimiter=";", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows([[safe_csv(item) for item in row] for row in rows])
    return "\ufeff" + result.getvalue()


def summary_csv():
    stats = db.subject_statistics()
    rows = [[v["name"], v["minutes"], v["sessions"], v["questions"],
             v["correct"], f"{percent(v['correct'], v['questions']):.1f}"] for v in stats]
    return create_csv(["Matéria", "Minutos", "Sessões", "Questões", "Acertos", "Aproveitamento (%)"], rows)


def history_csv(rows):
    return create_csv(["Data", "Matéria", "Tipo", "Detalhes", "Observação"],
                      [[r["study_date"], r["subject"], r["event_type"],
                        r["details"], r["note"]] for r in rows])


def show_error(err):
    st.error(f"Não foi possível salvar: {err}")


subjects = db.list_subjects()
subject_labels = {s["id"]: s["name"] for s in subjects}

with st.sidebar:
    st.markdown("## 📚 StudyTrack")
    st.caption("Sua rotina de estudos, organizada.")
    page = st.radio("Navegação", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("Versão final • uso local")
    st.caption("🔒 Seus dados são salvos neste computador.")

st.markdown('<div class="hero"><h1>StudyTrack</h1><p>Estude com foco. Acompanhe seu progresso. Evolua com dados.</p></div>',
            unsafe_allow_html=True)
if "flash_message" in st.session_state:
    st.success(st.session_state.pop("flash_message"))


if page == "🏠 Painel":
    st.subheader("Visão geral")
    stats = db.overview()
    a, b, c, d = st.columns(4)
    a.metric("Matérias", stats["subjects"])
    b.metric("Tempo estudado", minutes_label(stats["minutes"]))
    c.metric("Questões", stats["questions"])
    d.metric("Aproveitamento", f"{percent(stats['correct'],stats['questions']):.1f}%" if stats["questions"] else "—")

    st.write("")
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        st.markdown("#### Evolução dos últimos 30 dias")
        start = date.today() - timedelta(days=29)
        daily = db.daily_study_minutes(start.isoformat(), date.today().isoformat())
        if daily:
            chart_days = pd.DataFrame(daily)
            chart_days["study_date"] = pd.to_datetime(chart_days["study_date"])
            chart_days = chart_days.set_index("study_date")
            chart_days = chart_days.reindex(pd.date_range(start, date.today(), freq="D"), fill_value=0)
            chart_days.index.name = "Dia"
            st.bar_chart(chart_days["minutes"], y_label="Minutos")
        else:
            st.info("Ainda não há sessões nos últimos 30 dias. Registre seu primeiro estudo.")
    with right:
        st.markdown("#### Metas desta semana")
        goals = db.weekly_goal_progress()
        if not goals:
            st.info("Defina uma meta semanal para acompanhar seu ritmo.")
        else:
            for goal in goals:
                ratio = goal["minutes"] / goal["target_minutes"]
                st.write(f"**{goal['subject']}** · {minutes_label(goal['minutes'])} / {minutes_label(goal['target_minutes'])}")
                st.progress(min(1.0, ratio), text=f"{ratio*100:.0f}% da meta")
    st.markdown("#### Desempenho por matéria")
    rows = db.subject_statistics()
    if rows:
        df = pd.DataFrame([{
            "Matéria": r["name"], "Tempo (min)": r["minutes"],
            "Sessões": r["sessions"], "Questões": r["questions"],
            "Acertos": r["correct"],
            "Acerto (%)": round(percent(r["correct"], r["questions"]), 1) if r["questions"] else None,
        } for r in rows])
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Cadastre uma matéria para começar a acompanhar seu progresso.")
    st.markdown("#### Atividades recentes")
    history = db.recent_history(8)
    if history:
        st.dataframe(pd.DataFrame([{
            "Data": r["study_date"], "Matéria": r["subject"],
            "Atividade": r["event_type"], "Resultado": r["details"]
        } for r in history]), hide_index=True, use_container_width=True)
    else:
        st.caption("Nenhuma atividade registrada.")


elif page == "📚 Matérias":
    st.subheader("Gerenciar matérias")
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown("#### Adicionar matéria")
        with st.form("add_subject", clear_on_submit=True):
            name = st.text_input("Nome", placeholder="Ex.: Matemática")
            if st.form_submit_button("Cadastrar matéria", type="primary"):
                try:
                    db.add_subject(name)
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash("Matéria cadastrada com sucesso!")
    with right:
        st.markdown("#### Matérias cadastradas")
        if subjects:
            st.dataframe(pd.DataFrame(subjects).rename(columns={"id": "ID", "name": "Matéria"}),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma matéria ainda.")
    if subjects:
        st.divider()
        st.markdown("#### Renomear matéria")
        with st.form("rename_subject"):
            old_id = st.selectbox("Escolha a matéria", list(subject_labels),
                                  format_func=lambda k: subject_labels[k])
            new_name = st.text_input("Novo nome", value=subject_labels[old_id])
            if st.form_submit_button("Salvar novo nome"):
                try:
                    db.rename_subject(old_id, new_name)
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash("Nome atualizado!")
        with st.expander("Excluir uma matéria vazia"):
            st.caption("Por segurança, só é possível excluir matérias que não tenham histórico, metas ou tarefas.")
            unwanted_id = st.selectbox("Matéria para excluir", list(subject_labels),
                                       format_func=lambda k: subject_labels[k], key="delete_subject_choice")
            confirmation = st.checkbox("Confirmo que quero excluir esta matéria", key=f"delete_subject_confirm_{unwanted_id}")
            if st.button("Excluir matéria", disabled=not confirmation):
                try:
                    db.delete_subject(unwanted_id)
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash("Matéria excluída.")


elif page == "⏱️ Registrar estudo":
    st.subheader("Registrar uma sessão de estudo")
    if not subjects:
        st.warning("Cadastre uma matéria antes de registrar um estudo.")
    else:
        with st.form("study_form", clear_on_submit=False):
            sid = st.selectbox("Matéria", list(subject_labels), format_func=lambda k: subject_labels[k])
            duration = st.number_input("Minutos estudados", min_value=1, max_value=1440, value=45, step=5)
            when = st.date_input("Data", value=date.today(), max_value=date.today())
            note = st.text_area("O que você estudou? (opcional)", placeholder="Ex.: funções e laços de repetição", max_chars=1000)
            if st.form_submit_button("Salvar sessão", type="primary"):
                try:
                    db.add_study_session(sid, when.isoformat(), int(duration), note)
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash(f"Sessão de {duration} minutos salva em {subject_labels[sid]}!")
        st.caption("Cada clique em Salvar cria uma nova sessão. Registros podem ser corrigidos no Histórico.")


elif page == "🧠 Registrar questões":
    st.subheader("Registrar resolução de questões")
    if not subjects:
        st.warning("Cadastre uma matéria antes de registrar questões.")
    else:
        with st.form("questions_form", clear_on_submit=False):
            sid = st.selectbox("Matéria", list(subject_labels), format_func=lambda k: subject_labels[k])
            a, b = st.columns(2)
            with a:
                total = st.number_input("Questões respondidas", min_value=1, max_value=100000, value=10)
            with b:
                correct = st.number_input("Acertos", min_value=0, max_value=100000, value=8)
            when = st.date_input("Data", value=date.today(), max_value=date.today())
            note = st.text_area("Assunto/observação (opcional)", max_chars=1000)
            if st.form_submit_button("Salvar resultado", type="primary"):
                try:
                    db.add_question_record(sid, when.isoformat(), int(total), int(correct), note)
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash(f"Resultado registrado: {correct}/{total} — {percent(correct,total):.1f}% de acerto.")
        st.caption("Confira o total e a quantidade de acertos antes de salvar.")


elif page == "🎯 Metas semanais":
    st.subheader("Metas de estudo por semana")
    st.caption("Cada meta representa o total de minutos desejado de segunda-feira a domingo. A meta se repete semanalmente.")
    if not subjects:
        st.warning("Cadastre uma matéria antes de definir metas.")
    else:
        with st.form("goal_form"):
            sid = st.selectbox("Matéria", list(subject_labels), format_func=lambda k: subject_labels[k])
            hours = st.number_input("Meta semanal (em minutos)", min_value=1, max_value=10080, value=120, step=30)
            if st.form_submit_button("Salvar meta", type="primary"):
                try:
                    db.set_weekly_goal(sid, int(hours))
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash("Meta semanal atualizada!")
        goals = db.weekly_goal_progress()
        if goals:
            st.markdown("#### Progresso da semana atual")
            for goal in goals:
                st.markdown(f"**{goal['subject']}** — {minutes_label(goal['minutes'])} de {minutes_label(goal['target_minutes'])}")
                st.progress(min(1.0, goal["minutes"] / goal["target_minutes"]))
            with st.expander("Remover uma meta"):
                id_to_remove = st.selectbox("Meta", [g["subject_id"] for g in goals],
                                             format_func=lambda k: subject_labels[k])
                if st.button("Remover meta selecionada"):
                    db.delete_weekly_goal(id_to_remove)
                    flash("Meta removida.")


elif page == "✅ Tarefas":
    st.subheader("Planejamento de tarefas")
    if not subjects:
        st.warning("Cadastre uma matéria antes de criar tarefas.")
    else:
        has_due = st.checkbox("Definir prazo para a nova tarefa")
        with st.form("task_form", clear_on_submit=True):
            sid = st.selectbox("Matéria", list(subject_labels), format_func=lambda k: subject_labels[k])
            title = st.text_input("Tarefa", placeholder="Ex.: Resolver 20 questões de porcentagem", max_chars=200)
            a, b = st.columns(2)
            with a:
                priority = st.selectbox("Prioridade", ["Média", "Alta", "Baixa"])
            with b:
                st.caption("O prazo é opcional.")
            due = st.date_input("Prazo", date.today()) if has_due else None
            if st.form_submit_button("Adicionar tarefa", type="primary"):
                try:
                    db.add_task(sid, title, due.isoformat() if due else None, priority)
                except (ValueError, sqlite3.Error) as err:
                    show_error(err)
                else:
                    flash("Tarefa adicionada!")
    tasks = db.list_tasks()
    if tasks:
        st.markdown("#### Lista de tarefas")
        show_done = st.checkbox("Mostrar tarefas concluídas", value=True)
        filtered = [t for t in tasks if show_done or not t["done"]]
        if filtered:
            st.dataframe(pd.DataFrame([{
                "ID": t["id"], "Matéria": t["subject"], "Tarefa": t["title"],
                "Prazo": t["due_date"] or "—", "Prioridade": t["priority"],
                "Situação": "Concluída" if t["done"] else "Pendente"
            } for t in filtered]), hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma tarefa pendente.")
        with st.expander("Concluir, reabrir ou excluir tarefa"):
            chosen = st.selectbox("Escolha a tarefa", tasks,
                                  format_func=lambda t: f"#{t['id']} · {t['title'][:55]}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reabrir" if chosen["done"] else "Concluir", type="primary"):
                    db.set_task_done(chosen["id"], not chosen["done"])
                    flash("Tarefa atualizada!")
            with col2:
                confirm = st.checkbox("Confirmar exclusão", key=f"confirm_task_{chosen['id']}")
                if st.button("Excluir tarefa", disabled=not confirm):
                    db.delete_task(chosen["id"])
                    flash("Tarefa excluída!")
    else:
        st.info("Nenhuma tarefa adicionada.")


elif page == "🗂️ Histórico":
    st.subheader("Histórico de estudos e questões")
    a, b, c = st.columns([1.3, 1, 1])
    with a:
        period = st.date_input("Período", value=(date.today()-timedelta(days=29), date.today()),
                               max_value=date.today())
    with b:
        selection = st.selectbox("Matéria", [None]+list(subject_labels),
                                 format_func=lambda k: "Todas" if k is None else subject_labels[k])
    with c:
        kind = st.selectbox("Tipo", ["Todos", "Estudo", "Questões"])
    if not (isinstance(period, tuple) and len(period) == 2):
        st.info("Selecione o início e o fim do período.")
    elif period[0] > period[1]:
        st.error("O início deve ser anterior ao fim.")
    else:
        history = db.full_history(period[0].isoformat(), period[1].isoformat(), selection)
        if kind != "Todos":
            history = [h for h in history if h["event_type"] == kind]
        if not history:
            st.info("Nenhum registro encontrado no período.")
        else:
            st.dataframe(pd.DataFrame([{
                "Data": h["study_date"], "Matéria": h["subject"],
                "Tipo": h["event_type"], "Resultado": h["details"],
                "Observação": h["note"]
            } for h in history]), hide_index=True, use_container_width=True)
            st.download_button("⬇️ Exportar histórico filtrado (CSV)", history_csv(history),
                               "studytrack_historico.csv", mime="text/csv")
            with st.expander("Editar ou excluir um registro"):
                labels = {f"{h['event_type']} #{h['id']} — {h['study_date']} — {h['subject']}": h for h in history}
                chosen_label = st.selectbox("Registro", list(labels))
                item = labels[chosen_label]
                with st.form("edit_history"):
                    new_sid = st.selectbox("Matéria", list(subject_labels),
                                            index=list(subject_labels).index(item["subject_id"]),
                                            format_func=lambda k: subject_labels[k], key=f"edit_sid_{chosen_label}")
                    new_date = st.date_input("Data", value=date.fromisoformat(item["study_date"]),
                                              max_value=date.today(), key=f"edit_date_{chosen_label}")
                    if item["event_type"] == "Estudo":
                        minutes = st.number_input("Minutos", value=int(item["minutes"]), min_value=1, max_value=1440,
                                                  key=f"edit_mins_{chosen_label}")
                    else:
                        total = st.number_input("Questões", value=int(item["total"]), min_value=1,
                                                key=f"edit_total_{chosen_label}")
                        correct = st.number_input("Acertos", value=int(item["correct"]), min_value=0,
                                                  key=f"edit_correct_{chosen_label}")
                    note = st.text_area("Observação", value=item["note"], max_chars=1000,
                                        key=f"edit_note_{chosen_label}")
                    if st.form_submit_button("Salvar alterações", type="primary"):
                        try:
                            if item["event_type"] == "Estudo":
                                db.edit_study_session(item["id"], new_sid, new_date.isoformat(), int(minutes), note)
                            else:
                                db.edit_question_record(item["id"], new_sid, new_date.isoformat(), int(total), int(correct), note)
                        except (ValueError, sqlite3.Error) as err:
                            show_error(err)
                        else:
                            flash("Registro atualizado com sucesso!")
                delete_confirm = st.checkbox("Confirmo que quero apagar este registro permanentemente",
                                             key=f"confirm_history_{chosen_label}")
                if st.button("Excluir registro", disabled=not delete_confirm):
                    try:
                        db.delete_record(item["event_type"], item["id"])
                    except (ValueError, sqlite3.Error) as err:
                        show_error(err)
                    else:
                        flash("Registro removido.")


elif page == "💾 Exportar e backup":
    st.subheader("Exportações e cópia de segurança")
    st.write("Baixe seus resultados para planilhas ou salve um backup completo do banco de dados.")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### Relatório CSV")
        st.caption("Resumo acumulado por matéria, compatível com Excel e LibreOffice.")
        st.download_button("⬇️ Baixar relatório CSV", data=summary_csv(),
                           file_name="studytrack_relatorio.csv", mime="text/csv", type="primary")
    with col2:
        st.markdown("#### Backup dos dados")
        st.caption("Inclui matérias, sessões, questões, metas e tarefas.")
        st.download_button("💾 Baixar backup SQLite", data=db.database_backup_bytes(),
                           file_name=f"studytrack_backup_{datetime.now():%Y%m%d}.db",
                           mime="application/octet-stream", type="primary")
    st.divider()
    st.warning("**Privacidade:** o backup `.db` contém seus registros. Não envie esse arquivo ao GitHub nem o exponha publicamente.")
    st.markdown("""**Para restaurar um backup:** feche o aplicativo, faça uma cópia do banco atual e substitua
`studytrack.db` pelo arquivo do backup (renomeado para `studytrack.db`) na pasta do projeto. 
O programa deve estar **fechado** durante a substituição. Esse processo substitui os dados atuais, não mescla bancos.""")

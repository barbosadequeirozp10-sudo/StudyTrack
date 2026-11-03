"""StudyTrack: gerenciador de estudos em terminal."""

import csv
from datetime import date, datetime
from pathlib import Path

import database as db


BASE_DIR = Path(__file__).resolve().parent


def separator():
    print("=" * 48)


def read_integer(message, minimum=1, maximum=None):
    while True:
        raw = input(message).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Digite um número inteiro válido.")
            continue
        if value < minimum or (maximum is not None and value > maximum):
            if maximum is None:
                print(f"Digite um número maior ou igual a {minimum}.")
            else:
                print(f"Digite um número entre {minimum} e {maximum}.")
            continue
        return value


def read_date():
    while True:
        raw = input("Data (AAAA-MM-DD; Enter = hoje): ").strip()
        if not raw:
            return date.today().isoformat()
        try:
            return date.fromisoformat(raw).isoformat()
        except ValueError:
            print("Data inválida. Exemplo: 2026-11-03.")


def choose_subject():
    subjects = db.list_subjects()
    if not subjects:
        print("Nenhuma matéria cadastrada. Use primeiro a opção 1.")
        return None
    print("\nMatérias cadastradas:")
    valid_ids = {subject["id"] for subject in subjects}
    for subject in subjects:
        print(f"  {subject['id']} - {subject['name']}")
    while True:
        subject_id = read_integer("Número da matéria (0 para cancelar): ", minimum=0)
        if subject_id == 0:
            return None
        if subject_id in valid_ids:
            return subject_id
        print("Essa matéria não existe. Escolha um número da lista.")


def register_subject():
    print("\nCADASTRAR MATÉRIA")
    name = input("Nome da matéria: ").strip()
    try:
        db.add_subject(name)
        print("Matéria cadastrada com sucesso!")
    except ValueError as error:
        print(f"Não foi possível cadastrar: {error}")


def show_subjects():
    print("\nSUAS MATÉRIAS")
    subjects = db.list_subjects()
    if not subjects:
        print("Nenhuma matéria cadastrada ainda.")
    for subject in subjects:
        print(f"  {subject['id']} - {subject['name']}")


def register_study():
    print("\nREGISTRAR TEMPO DE ESTUDO")
    subject_id = choose_subject()
    if subject_id is None:
        return
    minutes = read_integer("Quantos minutos você estudou? ")
    day = read_date()
    db.add_study_session(subject_id, day, minutes)
    print("Sessão de estudo registrada com sucesso!")


def register_questions():
    print("\nREGISTRAR QUESTÕES")
    subject_id = choose_subject()
    if subject_id is None:
        return
    total = read_integer("Quantas questões você respondeu? ")
    correct = read_integer("Quantas acertou? ", minimum=0, maximum=total)
    day = read_date()
    db.add_question_record(subject_id, day, total, correct)
    print("Resultado registrado com sucesso!")


def format_duration(minutes):
    hours, remainder = divmod(minutes, 60)
    return f"{hours}h {remainder}min" if hours else f"{remainder}min"


def show_report():
    print("\nRELATÓRIO DE PROGRESSO")
    separator()
    overall = db.overview()
    if overall["subjects"] == 0:
        print("Cadastre uma matéria para começar.")
        return
    accuracy = (
        100 * overall["correct"] / overall["questions"]
        if overall["questions"] else 0
    )
    print(f"Matérias: {overall['subjects']}")
    print(f"Tempo estudado: {format_duration(overall['minutes'])}")
    print(f"Sessões registradas: {overall['sessions']}")
    print(f"Questões: {overall['questions']}")
    print(f"Acertos: {overall['correct']}")
    print(f"Aproveitamento geral: {accuracy:.1f}%" if overall["questions"] else
          "Aproveitamento geral: sem questões registradas")
    print("\nDESEMPENHO POR MATÉRIA")
    for item in db.subject_statistics():
        question_info = (
            f"{item['correct']}/{item['questions']} "
            f"({100 * item['correct'] / item['questions']:.1f}%)"
            if item["questions"] else "sem questões"
        )
        print(f"- {item['name']}: {format_duration(item['minutes'])}, "
              f"{item['sessions']} sessão(ões), {question_info}")


def show_history():
    print("\nHISTÓRICO RECENTE")
    events = db.recent_history()
    if not events:
        print("Ainda não existem registros.")
    for event in events:
        print(f"{event['study_date']} | {event['subject']} | "
              f"{event['event_type']}: {event['details']}")


def spreadsheet_safe(value):
    """Impede que nomes de matérias virem fórmulas em planilhas."""
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def export_csv():
    rows = db.subject_statistics()
    if not rows:
        print("Cadastre pelo menos uma matéria antes de exportar.")
        return
    export_dir = BASE_DIR / "exports"
    export_dir.mkdir(exist_ok=True)
    filepath = export_dir / f"relatorio_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with filepath.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Matéria", "Minutos", "Sessões", "Questões", "Acertos", "Aproveitamento (%)"])
        for item in rows:
            accuracy = round(100 * item["correct"] / item["questions"], 1) if item["questions"] else 0
            writer.writerow([
                spreadsheet_safe(item["name"]), item["minutes"], item["sessions"],
                item["questions"], item["correct"], accuracy,
            ])
    print(f"Relatório exportado para: {filepath}")


def main():
    db.initialize_database()
    separator()
    print("             STUDYTRACK (Terminal)")
    print("        Seu progresso começa aqui!")
    separator()
    while True:
        print("\n1 - Cadastrar matéria")
        print("2 - Listar matérias")
        print("3 - Registrar estudo")
        print("4 - Registrar questões")
        print("5 - Ver relatório de progresso")
        print("6 - Consultar histórico")
        print("7 - Exportar relatório CSV")
        print("0 - Sair")
        option = input("Escolha uma opção: ").strip()
        actions = {
            "1": register_subject,
            "2": show_subjects,
            "3": register_study,
            "4": register_questions,
            "5": show_report,
            "6": show_history,
            "7": export_csv,
        }
        if option == "0":
            print("Até a próxima! Bons estudos.")
            break
        action = actions.get(option)
        if action:
            action()
        else:
            print("Opção inválida. Escolha um número do menu.")


if __name__ == "__main__":
    main()

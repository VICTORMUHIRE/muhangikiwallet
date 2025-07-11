import threading, schedule, time
from .tasks import remboursement_automatique_pret

def run_scheduler():
    # Planifier la tâche tous les jours à 12h
    schedule.every().day.at("12:00").do(remboursement_automatique_pret)

    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

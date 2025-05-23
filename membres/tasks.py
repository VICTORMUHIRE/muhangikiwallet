from celery import shared_task
import time

@shared_task
def hello_world_task():
    print("Hello World!")
    time.sleep(2) 
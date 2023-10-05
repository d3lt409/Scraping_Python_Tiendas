import click
from scraping import ara,d1,olimpicav2, jumbo, exito,exitov2

import multiprocessing as mp

NUM_THREADS = 5
jobs = []

@click.group()
def main_click():
    pass

@main_click.command(name = "ara")
def ara_click():
    job = mp.Process(target=ara.main)
    job.start()
    job.join()

@main_click.command(name = "d1")
def d1_click():
    job = mp.Process(target=d1.main)
    job.start()
    job.join()

@main_click.command(name = "olimpica")
def olimpica_click():
    job = mp.Process(target=olimpicav2.main)
    job.start()
    job.join()

@main_click.command(name = "jumbo")
def jumbo_click():
    job = mp.Process(target=jumbo.main)
    job.start()
    job.join()

@main_click.command(name = "exito")
def exito_click():
    job = mp.Process(target=exito.main)
    job.start()
    job.join()
    
@main_click.command(name = "exitov2")
def exito_click():
    job = mp.Process(target=exitov2.main)
    job.start()
    job.join()

if __name__ == '__main__':
    main_click()
    

# poetry run scalene --html --outfile prof.html --reduced-profile src/telegram_downloader.py
# poetry run scalene --html --outfile prof_full.html src/telegram_downloader.py

# poetry run scalene --html --outfile prof.html --reduced-profile src/enqueue_jobs.py
# poetry run scalene --html --outfile prof_full.html src/enqueue_jobs.py

PONY_DEBUG=True poetry run scalene --html --outfile prof.html --reduced-profile src/worker.py
# poetry run scalene --html --outfile prof_full.html src/worker.py



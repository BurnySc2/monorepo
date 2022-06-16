FROM python:3.10-slim

WORKDIR /root/discord_bot

ADD poetry.lock pyproject.toml ./

RUN pip install poetry --no-cache-dir \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

ADD . /root/discord_bot

# Allow imports like 'from discord_bot.commands.public_remind import Remind'
ENV PYTHONPATH "${PYTHONPATH}:/root"

CMD ["poetry", "run", "python", "main.py"]

# See run.sh

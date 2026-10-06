# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Prima solo i metadati: il layer delle dipendenze resta in cache finche' non cambiano.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install .

# Utente non-root senza shell ne' home scrivibile.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin aristotle
USER aristotle

# Nessuna porta esposta: il bot usa il long polling verso api.telegram.org.
CMD ["aristotle"]

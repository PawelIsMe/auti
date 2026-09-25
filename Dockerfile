#FROM ubuntu:latest
#LABEL authors="pawel"
#
#ENTRYPOINT ["top", "-b"]


# ==========================================
# ETAP 1: Budowanie Frontendu (React)
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Kopiowanie zależności i instalacja
COPY frontend/package*.json ./
RUN npm install

# Kopiowanie reszty źródeł frontendu i budowanie (tworzy /dist)
COPY frontend/ ./
RUN npm run build

# ==========================================
# ETAP 2: Obraz produkcyjny (Python)
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# Instalacja zależności Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu backendu oraz tworzenie pustego folderu data/
COPY app/ ./app/
RUN mkdir -p data


# Kopiowanie zbudowanych plików statycznych Reacta do katalogu frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

# Uruchomienie aplikacji z modułu app.main
CMD ["python", "-m", "app.main"]
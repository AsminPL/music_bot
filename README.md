# 🎶 Discord Music Bot (STABLE)

Witaj! Ten bot umożliwia odtwarzanie muzyki z YouTube i Spotify bezpośrednio na Twoim serwerze Discord.

---

## ⚠️ Ważna informacja

> **Przed uruchomieniem bota**:  
> W pliku `bot.py` ustaw `DEBUG_GUILD_IDS = [TWOJE_ID_SERWERA]`, aby komendy ukośnika (`/`) działały poprawnie.
> Bez tego mogą się nie pojawiać.

---

## ✨ Funkcje

- `/play <link lub tytuł>` — odtwarza muzykę z YouTube lub Spotify (pojedyncze utwory)
- `/pause` — pauzuje aktualnie odtwarzany utwór
- `/resume` — wznawia odtwarzanie
- `/volume <0-100>` — ustawia głośność
- `/stop` — zatrzymuje muzykę i czyści kolejkę
- `/skip` — pomija utwór
- `/leave` — bot wychodzi z kanału głosowego
- `/pomoc` — pokazuje dostępne komendy i instrukcje

---

## 🧪 Wersja STABLE

Bot jest w STABLE  — lecz mogą występować błędy których nie odkryłem sam podczas testowania (z względu ze koduje solo)
**Zgłaszaj je w issues!**

> ⚠️ Integracja ze Spotify może być niedoskonała (konwersja na YouTube). Zalecane jest używanie linków YouTube.

---

## 🚀 Wymagania

| Komponent          | Wersja            |
|--------------------|-------------------|
| Python             | 3.8 lub wyższy    |
| FFmpeg             | Zainstalowany     |
| pip                | Aktualny          |
| Discord Bot Token  | Własny            |
| Spotify API Keys   | Client ID/Secret  |

---

## 🔧 Instalacja (Linux)

### 1. Instalacja zależności systemowych

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip ffmpeg
```

### 2. Instalacja bibliotek Pythona

```bash
pip3 install py-cord yt-dlp spotipy
```

### 3. Utwórz plik `bot.py`

```bash
mkdir ~/discord_music_bot
cd ~/discord_music_bot
nano bot.py
```

Wklej kod bota i podmień dane:

```python
DISCORD_BOT_TOKEN = 'TWOJ_TOKEN_BOTA_DISCORD'
SPOTIFY_CLIENT_ID = 'TWOJ_SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET = 'TWOJ_SPOTIFY_CLIENT_SECRET'
DEBUG_GUILD_IDS = [TWOJE_ID_SERWERA]
```

Zapisz i zamknij (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

## 🔑 Tokeny i klucze

### 🔹 Discord Bot Token

1. Wejdź na [Discord Developer Portal](https://discord.com/developers/applications)
2. Utwórz aplikację → zakładka **Bot** → kliknij „Add Bot”
3. Skopiuj token i zaznacz:
   - ✅ `PRESENCE INTENT`
   - ✅ `MESSAGE CONTENT INTENT`

### 🔹 Spotify API

1. Wejdź na [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Utwórz aplikację
3. Skopiuj `Client ID` i `Client Secret`
4. W **Edit Settings** dodaj `http://localhost:8888/callback` do Redirect URIs

---

## 🤖 Zaproszenie bota na serwer

1. W Discord Developer Portal → **OAuth2 → URL Generator**
2. Zaznacz:
   - **Scopes**: `bot`, `applications.commands`
   - **Permissions**: `Send Messages`, `Connect`, `Speak`, `Use Voice Activity`
3. Wygeneruj link i otwórz go w przeglądarce

---

## ▶️ Uruchamianie bota

```bash
cd ~/discord_music_bot
python3 bot.py
```

Aby działał w tle:

```bash
sudo apt install screen
screen -S muzyka
python3 bot.py
# potem: Ctrl+A, D — odłączenie sesji
```

---

## 🧯 Rozwiązywanie problemów

| Problem | Rozwiązanie |
|--------|-------------|
| `ModuleNotFoundError: No module named 'discord.commands'` | Upewnij się, że zainstalowano `py-cord` |
| `SyntaxError: (unicode error)` | Plik zapisany w UTF-8 z nagłówkiem `# -*- coding: utf-8 -*-` |
| `Invalid data found when processing input` | Uaktualnij `yt-dlp`: `pip3 install --upgrade yt-dlp` |
| Bot nie odtwarza / nie dołącza | Sprawdź czy FFmpeg działa (`ffmpeg -version`) i bot ma uprawnienia |
| Slash komendy się nie pojawiają | Upewnij się, że `DEBUG_GUILD_IDS` zawiera poprawne ID serwera lub wywal `debug_guilds` do rejestracji globalnej |

---

## 🤝 Wsparcie

Masz pytania, bugi, albo chcesz coś dodać do kodu?  
Zgłoś **issues**
lub:
E-Mail: asmin@asmin.pl lub developer@asmin.pl
Tel: +48 732 797 370
Discord: asminpl

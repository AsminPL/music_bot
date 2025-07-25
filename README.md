
# 🎶 Discord Music Bot (Wersja BETA) 🎧

Witaj w moim repozytorium bota muzycznego na Discorda!  
Ten bot pozwala na odtwarzanie muzyki z YouTube i Spotify bezpośrednio na Twoim serwerze Discord.

---

## ✨ Funkcje

- `!play <link lub tytuł>` — Odtwarza muzykę z YouTube lub Spotify (tylko pojedyncze utwory). Możesz podać link URL lub tytuł utworu do wyszukania.
- `!pause` — Wstrzymuje aktualnie odtwarzany utwór.
- `!resume` — Wznawia wstrzymany utwór.
- `!volume <wartość>` — Ustawia głośność odtwarzania (wartość od 0 do 100).
- `!leave` — Bot opuszcza kanał głosowy i czyści kolejkę odtwarzania.
- `!pomoc` — Wyświetla listę dostępnych komend oraz ważne informacje.

---

## ⚠️ UWAGA! Wersja BETA (1.0-beta)

Ten bot jest w fazie **BETA**. Mogą występować bugi oraz błędy.  
Prosimy o zgłaszanie wszelkich problemów!

- Podczas korzystania z komendy `!play`, wklej link do Spotify/YouTube.  
- Musisz być na **kanale głosowym**, aby bot zadziałał!
- **Zalecamy korzystanie z linków YouTube**, ponieważ integracja ze Spotify może być niestabilna (konwersja na YouTube).

---

## 🚀 Wymagania

Aby uruchomić bota, potrzebujesz:

- Python 3.8+ (zalecane)
- `pip` (menedżer pakietów Pythona)
- `FFmpeg` (program do przetwarzania audio/wideo)
- Token bota Discord
- Klucze API Spotify (Client ID i Client Secret)

---

## 🛠️ Instalacja i Konfiguracja

Poniżej znajdziesz kroki do uruchomienia bota na systemie Linux (np. Ubuntu/Debian):

### 1. Aktualizacja systemu i instalacja Pythona

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip
```

### 2. Instalacja FFmpeg

```bash
sudo apt install -y ffmpeg
```

### 3. Instalacja bibliotek Pythona

```bash
pip3 install discord.py yt-dlp spotipy
```

### 4. Przygotowanie pliku bota

#### a. Utwórz katalog:

```bash
mkdir ~/discord_music_bot
cd ~/discord_music_bot
```

#### b. Utwórz plik `bot.py`:

```bash
nano bot.py
```

#### c. Wklej kod bota i skonfiguruj tokeny:

Zamień dane na swoje:

```python
DISCORD_BOT_TOKEN = 'TWOJ_TOKEN_BOTA_DISCORD'
SPOTIFY_CLIENT_ID = 'TWOJ_SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET = 'TWOJ_SPOTIFY_CLIENT_SECRET'
```

Zapisz plik (`Ctrl+O`, Enter) i wyjdź (`Ctrl+X`).

---

### 5. Uzyskanie Tokenu Bota Discord

1. Przejdź do [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Zaloguj się i utwórz nową aplikację.
3. Przejdź do zakładki **Bot** → kliknij **Add Bot**.
4. Skopiuj token bota.
5. Włącz opcje:
   - `PRESENCE INTENT`
   - `MESSAGE CONTENT INTENT`

---

### 6. Uzyskanie Kluczy API Spotify

1. Przejdź do [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Utwórz nową aplikację.
3. Skopiuj `Client ID` oraz `Client Secret`.
4. W **Edit Settings** → dodaj `http://localhost:8888/callback` jako Redirect URI.

---

### 7. Zaproszenie bota na serwer Discord

1. W Discord Developer Portal → **OAuth2** → **URL Generator**
2. Zaznacz:
   - **SCOPES**: `bot`
   - **BOT PERMISSIONS**:
     - `Read Messages/View Channels`
     - `Send Messages`
     - `Connect`
     - `Speak`
     - `Use Voice Activity`
3. Skopiuj wygenerowany link i wklej go do przeglądarki, aby zaprosić bota.

---

## ▶️ Uruchamianie Bota

Po przygotowaniu środowiska uruchom bota:

```bash
cd ~/discord_music_bot
python3 bot.py
```

Aby bot działał w tle:

```bash
sudo apt install -y screen
screen
cd ~/discord_music_bot
python3 bot.py
# Następnie Ctrl+A, potem D, aby odłączyć sesję screena
```

---

## ❓ Rozwiązywanie problemów

- `SyntaxError: Non-UTF-8 code...`  
  → Dodaj `# -*- coding: utf-8 -*-` na początku pliku `bot.py` i upewnij się, że plik zapisany jest w UTF-8.

- `Invalid data found when processing input`  
  → Zaktualizuj yt-dlp:

  ```bash
  pip3 install --upgrade yt-dlp
  ```

- Bot nie odtwarza / nie łączy się z kanałem głosowym  
  → Sprawdź:
  - Uprawnienia bota (`Connect`, `Speak`)
  - Instalację FFmpeg (`ffmpeg` musi działać w terminalu)

---

## 🤝 Wsparcie i Kontakt

Masz pytania lub potrzebujesz pomocy?  
Skontaktuj się ze mną — chętnie pomogę! 🎧

---

> Projekt w wersji **BETA** — rozwijany i testowany na bieżąco.

# -*- coding: utf-8 -*-
# --> Credits: ChatGPT (za napisanie tych # i opisu README)
import discord
from discord.commands import slash_command, Option # Importujemy ApplicationCommand i Option
from discord.ext import commands # Zmieniamy z discord.Client na discord.ext.commands.Bot
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import os

# --- Konfiguracja Bota ---
# Zastap 'TWOJ_TOKEN_BOTA_DISCORD' rzeczywistym tokenem Twojego bota Discord.
# Mozesz go znalezc w Discord Developer Portal (https://discord.com/developers/applications).
DISCORD_BOT_TOKEN = 'nahbro'

# --- Konfiguracja Spotify API ---
# Zastap 'TWOJ_SPOTIFY_CLIENT_ID' i 'TWOJ_SPOTIFY_CLIENT_SECRET' swoimi kluczami API Spotify.
# Mozesz je uzyskac na Spotify Developer Dashboard (https://developer.spotify.com/dashboard/applications).
SPOTIFY_CLIENT_ID = 'nahbro'
SPOTIFY_CLIENT_SECRET = 'nahbro'

# --- Inicjalizacja klienta Spotify ---
# Autoryzacja do korzystania z API Spotify.
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                                           client_secret=SPOTIFY_CLIENT_SECRET))

# --- Opcje yt-dlp ---
# Opcje konfiguracji dla yt-dlp, uzywanego do pobierania informacji o audio z YouTube.
YDL_OPTIONS = {
    'format': 'bestaudio/best',  # Wybiera najlepszy format audio.
    'noplaylist': True,          # Nie pobiera calych playlist, tylko pojedyncze utwory.
    'quiet': True,               # Wylacza komunikaty yt-dlp w konsoli.
    'extract_flat': True,        # Szybkie wyodrebnianie informacji bez pobierania.
    'cookiefile': 'cookies.txt', # Opcjonalnie: sciezka do pliku z ciasteczkami, jesli masz problemy z wiekiem/geoblokada.
    'default_search': 'ytsearch', # Domyslne wyszukiwanie na YouTube, jesli podano tylko tytul.
    'source_address': '0.0.0.0'  # Opcjonalnie: adres IP do uzycia przy pobieraniu.
}

# --- Opcje FFmpeg ---
# Opcje konfiguracji dla FFmpeg, uzywanego do odtwarzania strumienia audio.
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'  # `-vn` oznacza "no video", czyli tylko strumien audio.
}

# --- Klasa pomocnicza do obslugi zrodel audio z yt-dlp ---
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        
        # DEBUG: Sprawdzamy, czy YDL_OPTIONS jest dostepne w globalnym zakresie
        if 'YDL_OPTIONS' not in globals():
            print("ERROR: YDL_OPTIONS nie jest zdefiniowane w globalnym zakresie!")
            ydl_options_to_use = {}
        else:
            ydl_options_to_use = YDL_OPTIONS

        ydl = yt_dlp.YoutubeDL(ydl_options_to_use)
        
        # Sprawdzamy, czy to link Spotify
        if "spotify.com" in url:
            try:
                if "track" in url:
                    track = sp.track(url)
                    search_query = f"{track['name']} {track['artists'][0]['name']}"
                    # Wyszukujemy utwor Spotify na YouTube
                    data = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{search_query}", download=not stream))
                    if 'entries' in data:
                        data = data['entries'][0]
                else:
                    # Nie obslugujemy playlist ani albumow Spotify bezposrednio w tej wersji.
                    raise ValueError("Obecnie obslugiwane sa tylko pojedyncze utwory Spotify.")
            except Exception as e:
                print(f"Blad podczas przetwarzania linku Spotify: {e}")
                raise
        else:
            # Jesli to nie link Spotify, traktujemy to jako link YouTube lub zapytanie wyszukiwania.
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
            if 'entries' in data:
                # Jesli to playlisty lub wyniki wyszukiwania, bierzemy pierwszy wpis.
                data = data['entries'][0]

        if stream:
            # Jesli streamujemy, uzywamy bezposredniego URL audio.
            return cls(discord.FFmpegPCMAudio(data['url'], **FFMPEG_OPTIONS), data=data)
        else:
            # Jesli nie streamujemy (np. do pobrania), zwracamy dane.
            return cls(discord.FFmpegPCMAudio(ydl.prepare_filename(data), **FFMPEG_OPTIONS), data=data)

# --- Klient Discorda ---
# Ustawiamy intencje, aby bot mogl czytac zawartosc wiadomosci.
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# --- WAŻNE: Wstaw tutaj ID swojego serwera Discord (Guild ID) ---
# Komendy ukośnika zarejestrowane dla konkretnego serwera pojawiaja sie natychmiast.
# Aby uzyskac ID serwera:
# 1. Wlacz Tryb Dewelopera w ustawieniach Discorda (Ustawienia Uzytkownika -> Zaawansowane).
# 2. Kliknij prawym przyciskiem myszy na nazwe swojego serwera i wybierz "Kopiuj ID".
DEBUG_GUILD_IDS = [TUTAJID] # <--- WSTAW TUTAJ ID SWOJEGO SERWERA

# Inicjalizacja bota z obsluga komend ukośnika
bot = commands.Bot(command_prefix="!", intents=intents, debug_guilds=DEBUG_GUILD_IDS) 

# Slownik do przechowywania kolejek odtwarzania dla kazdego serwera.
# Klucz: ID serwera (guild.id), Wartosc: asyncio.Queue()
music_queues = {}

# Slownik do przechowywania obiektow voice_client dla kazdego serwera.
# Klucz: ID serwera (guild.id), Wartosc: discord.VoiceClient
voice_clients = {}

async def play_next_song(guild_id):
    """Odtwarza nastepny utwor z kolejki dla danego serwera."""
    if guild_id in music_queues and not music_queues[guild_id].empty():
        source = await music_queues[guild_id].get()
        voice_client = voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_connected():
            # Odtwarza utwor, a po jego zakonczeniu wywoluje play_next_song ponownie.
            voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(guild_id), bot.loop).result())
            channel = bot.get_channel(source.data['channel_id']) # Pobieramy kanal, z ktorego przyszla komenda
            if channel:
                await channel.send(f"Teraz odtwarzam: **{source.title}**")
        else:
            # Jesli bot nie jest juz polaczony, czyscimy kolejke.
            while not music_queues[guild_id].empty():
                await music_queues[guild_id].get()
            print(f"Bot nie jest polaczony na serwerze {guild_id}, kolejka wyczyszczona.")
    else:
        # Jesli kolejka jest pusta, nic nie robimy.
        pass

@bot.event
async def on_ready():
    """Wywolywane, gdy bot jest gotowy i zalogowany."""
    print(f'Zalogowano jako {bot.user}')
    print(f'ID bota: {bot.user.id}')
    print('Bot jest gotowy do dzialania!')
    await bot.change_presence(activity=discord.Game(name="/pomoc")) # Tutaj mozesz ustawic status swojego bota


# --- Komenda /play ---
@bot.slash_command(name="play", description="Odtwarza muzyke z YouTube/Spotify lub dodaje do kolejki.")
async def play(ctx: discord.ApplicationContext, query: Option(str, "Link lub tytul utworu", required=True)):
    if not ctx.author.voice:
        await ctx.respond("Musisz byc na kanale glosowym, aby uzyc tej komendy!", ephemeral=True)
        return

    # Uzywamy ctx.defer(), aby bot nie zglosil bledu timeoutu, jesli przetwarzanie trwa dluzej
    await ctx.defer() 

    voice_channel = ctx.author.voice.channel
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)

    # Sprawdzamy, czy bot jest juz polaczony z kanalem glosowym na tym serwerze
    if voice_client and voice_client.is_connected():
        # Jesli bot jest polaczony, ale na innym kanale niz uzytkownik
        if voice_client.channel.id != voice_channel.id:
            await ctx.followup.send("? Jestem juz na innym kanale, niestety nie moge do ciebie dolaczyc!", ephemeral=True)
            return
        # Jesli bot jest polaczony i na tym samym kanale co uzytkownik, kontynuuj normalnie
    else:
        # Bot nie jest polaczony, probujemy sie polaczyc
        try:
            voice_clients[guild_id] = await voice_channel.connect()
            voice_client = voice_clients[guild_id] # Zapewniamy, ze voice_client jest zaktualizowany
            await ctx.followup.send(f"Dolaczylem do kanalu: **{voice_channel.name}**")
        except Exception as e:
            await ctx.followup.send(f"Nie udalo mi sie dolaczyc do kanalu: {e}", ephemeral=True)
            print(f"Blad dolaczania do kanalu: {e}")
            return # Wychodzimy, jesli polaczenie sie nie powiodlo
    
    if voice_client is None or not voice_client.is_connected():
        await ctx.followup.send("Wystapil problem z polaczeniem bota z kanalem glosowym. Sprobuj ponownie.", ephemeral=True)
        print(f"DEBUG: voice_client is None or not connected after connection logic for guild {guild_id}. This indicates an unexpected state.")
        return

    # Reszta logiki komendy /play (dodawanie do kolejki, odtwarzanie)
    try:
        source = await YTDLSource.from_url(query, loop=bot.loop, stream=True) # Uzywamy bot.loop zamiast client.loop
        source.data['channel_id'] = ctx.channel.id # Uzywamy ctx.channel.id dla kanalu tekstowego

        if guild_id not in music_queues:
            music_queues[guild_id] = asyncio.Queue()
        
        await music_queues[guild_id].put(source)
        await ctx.followup.send(f"Dodano do kolejki: **{source.title}**")

        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next_song(guild_id)

    except ValueError as ve:
        await ctx.followup.send(f"Blad: {ve}", ephemeral=True)
    except Exception as e:
        await ctx.followup.send(f"Wystapil blad podczas wyszukiwania/przygotowywania utworu: {e}", ephemeral=True)
        print(f"Blad /play: {e}")

# --- Komenda /pause ---
@bot.slash_command(name="pause", description="Wstrzymuje aktualnie odtwarzany utwor.")
async def pause(ctx: discord.ApplicationContext):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.respond("Wstrzymano odtwarzanie.")
    else:
        await ctx.respond("Nic nie jest odtwarzane lub juz jest wstrzymane.", ephemeral=True)

# --- Komenda /resume ---
@bot.slash_command(name="resume", description="Wznawia wstrzymany utwor.")
async def resume(ctx: discord.ApplicationContext):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.respond("Wznowiono odtwarzanie.")
    else:
        await ctx.respond("Nic nie jest wstrzymane.", ephemeral=True)

# --- Komenda /stop ---
@bot.slash_command(name="stop", description="Zatrzymuje odtwarzanie i czysci kolejke.")
async def stop(ctx: discord.ApplicationContext):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop() # Zatrzymuje odtwarzanie
        # Czysci kolejke po zatrzymaniu, aby nie odtwarzal nastepnego utworu automatycznie
        if guild_id in music_queues:
            while not music_queues[guild_id].empty():
                await music_queues[guild_id].get()
        await ctx.respond("Zatrzymano odtwarzanie i wyczyszczono kolejke.")
    else:
        await ctx.respond("Nic nie jest odtwarzane, aby zatrzymac.", ephemeral=True)

# --- Komenda /skip ---
@bot.slash_command(name="skip", description="Pomija aktualnie odtwarzany utwor.")
async def skip(ctx: discord.ApplicationContext):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)
    if not voice_client or not voice_client.is_connected():
        await ctx.respond("Bot nie jest polaczony z kanalem glosowym.", ephemeral=True)
        return

    if guild_id in music_queues and not music_queues[guild_id].empty():
        # Zatrzymanie aktualnego utworu spowoduje wywolanie funkcji 'after',
        # ktora automatycznie odtworzy nastepny utwor z kolejki.
        voice_client.stop()
        await ctx.respond("Pominieto aktualny utwor.")
    else:
        await ctx.respond("Kolejka jest pusta. Brak utworow do pominiecia.", ephemeral=True)

# --- Komenda /volume ---
@bot.slash_command(name="volume", description="Ustawia glosnosc odtwarzania.")
async def volume(ctx: discord.ApplicationContext, wartosc: Option(int, "Wartosc glosnosci od 0 do 100", min_value=0, max_value=100, required=True)):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)

    if not voice_client or not voice_client.is_connected():
        await ctx.respond("Bot nie jest polaczony z kanalem glosowym.", ephemeral=True)
        return
    
    if not voice_client.source:
        await ctx.respond("Nic nie jest aktualnie odtwarzane.", ephemeral=True)
        return

    try:
        # Wartosc jest juz sparsowana dzieki Option(int, ...)
        voice_client.source.volume = wartosc / 100.0
        await ctx.respond(f"Ustawiono glosnosc na {wartosc}%.")
    except Exception as e:
        await ctx.respond(f"Wystapil blad podczas zmiany glosnosci: {e}", ephemeral=True)
        print(f"Blad /volume: {e}")

# --- Komenda /leave ---
@bot.slash_command(name="leave", description="Bot opuszcza kanal glosowy.")
async def leave(ctx: discord.ApplicationContext):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(guild_id)
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        del voice_clients[guild_id]
        # Czyscimy kolejke dla tego serwera po wyjsciu.
        if guild_id in music_queues:
            while not music_queues[guild_id].empty():
                await music_queues[guild_id].get()
            del music_queues[guild_id]
        await ctx.respond("Opuscilem kanal glosowy.")
    else:
        await ctx.respond("Nie jestem na zadnym kanale glosowym.", ephemeral=True)

# --- Komenda /pomoc ---
@bot.slash_command(name="pomoc", description="Wyswietla liste dostepnych komend.")
async def pomoc(ctx: discord.ApplicationContext):
    help_message = """
**Dostepne komendy bota muzycznego (komendy ukosnika):**
`/play <link lub tytul>` - Odtwarza muzyke z YouTube lub Spotify (tylko pojedyncze utwory). Mozesz podac link lub tytul utworu.
    * Jesli bot jest juz na innym kanale glosowym na tym samym serwerze, otrzymasz prywatna wiadomosc z informacja.
`/pause` - Wstrzymuje aktualnie odtwarzany utwor.
`/resume` - Wznawia wstrzymany utwor.
`/stop` - Zatrzymuje odtwarzanie i czysci kolejke, ale bot pozostaje na kanale glosowym.
`/skip` - Pomija aktualnie odtwarzany utwor i przechodzi do nastepnego w kolejce.
`/volume <wartosc>` - Ustawia glosnosc odtwarzania (od 0 do 100).
`/leave` - Bot opuszcza kanal glosowy i czysci kolejke.
`/pomoc` - Wyswietla ta liste komend.

---.
Podczas korzystania z komendy `/play`, wklej link do Spotify/Youtube (Pamietaj ze musisz byc na kanale!).
Zalecamy korzystanie z YOUTUBE poniewaz Spotify nie zawsze dziala!
        """
    await ctx.respond(help_message, ephemeral=True) # Pomoc zawsze jako wiadomosc efemeryczna

# Uruchomienie bota
# Bot bedzie dzialal, dopoki skrypt nie zostanie zatrzymany.
bot.run(DISCORD_BOT_TOKEN)

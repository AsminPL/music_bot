# -*- coding: utf-8 -*-
import discord
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio
import os


DISCORD_BOT_TOKEN = 'uzupelnij'
SPOTIFY_CLIENT_ID = 'uzupelnij'
SPOTIFY_CLIENT_SECRET = 'uzupelnij'



sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                                           client_secret=SPOTIFY_CLIENT_SECRET))



YTDL_OPTIONS = {
    'format': 'bestaudio/best',  # Wybiera najlepszy format audio.
    'noplaylist': True,          # Nie pobiera calych playlist, tylko pojedyncze utwory.
    'quiet': True,               # Wylacza komunikaty yt-dlp w konsoli.
    'extract_flat': True,        # Szybkie wyodrebnianie informacji bez pobierania.
    'cookiefile': 'cookies.txt', # Opcjonalnie: sciezka do pliku z ciasteczkami, jesli masz problemy z wiekiem/geoblokada.
    'default_search': 'ytsearch', # Domyslne wyszukiwanie na YouTube, jesli podano tylko tytul.
    'source_address': '0.0.0.0'  # Opcjonalnie: adres IP do uzycia przy pobieraniu.
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'  # `-vn` oznacza "no video", czyli tylko strumien audio.
}


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
        ydl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
        
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

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True # Wymagane do zarzadzania stanami glosowymi.
client = discord.Client(intents=intents)

music_queues = {}
voice_clients = {}

async def play_next_song(guild_id):
    """Odtwarza nastepny utwor z kolejki dla danego serwera."""
    if guild_id in music_queues and not music_queues[guild_id].empty():
        source = await music_queues[guild_id].get()
        voice_client = voice_clients.get(guild_id)
        
        if voice_client and voice_client.is_connected():
            voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(guild_id), client.loop).result())
            channel = client.get_channel(source.data['channel_id']) # Pobieramy kanal, z ktorego przyszla komenda
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

@client.event
async def on_ready():
    """Wywolywane, gdy bot jest gotowy i zalogowany."""
    print(f'Zalogowano jako {client.user}')
    print(f'ID bota: {client.user.id}')
    print('Bot jest gotowy do dzialania!')
    await client.change_presence(activity=discord.Game(name="!pomoc")) # Ustawia status bota.

@client.event
async def on_message(message):
    """Wywolywane przy kazdej nowej wiadomosci."""
    if message.author == client.user:
        return # Ignoruj wiadomosci wyslane przez samego bota.

    # --- Komenda !play ---
    if message.content.startswith('!play'):
        if not message.author.voice:
            await message.channel.send("Musisz byc na kanale glosowym, aby uzyc tej komendy!")
            return

        query = message.content[len('!play '):].strip()
        if not query:
            await message.channel.send("Podaj link lub tytul utworu, ktory chcesz odtworzyc.")
            return

        voice_channel = message.author.voice.channel
        guild_id = message.guild.id

        # Dolacz do kanalu glosowego, jesli jeszcze nie jest polaczony.
        if guild_id not in voice_clients or not voice_clients[guild_id].is_connected():
            try:
                voice_clients[guild_id] = await voice_channel.connect()
                await message.channel.send(f"Dolaczylem do kanalu: **{voice_channel.name}**")
            except Exception as e:
                await message.channel.send(f"Nie udalo mi sie dolaczyc do kanalu: {e}")
                print(f"Blad dolaczania do kanalu: {e}")
                return
        
        voice_client = voice_clients[guild_id]

        try:
            source = await YTDLSource.from_url(query, loop=client.loop, stream=True)
            source.data['channel_id'] = message.channel.id 

            if guild_id not in music_queues:
                music_queues[guild_id] = asyncio.Queue()
            
            await music_queues[guild_id].put(source)
            await message.channel.send(f"Dodano do kolejki: **{source.title}**")

            # Jesli nic nie jest odtwarzane, rozpocznij odtwarzanie z kolejki.
            if not voice_client.is_playing() and not voice_client.is_paused():
                await play_next_song(guild_id)

        except ValueError as ve:
            await message.channel.send(f"Blad: {ve}")
        except Exception as e:
            await message.channel.send(f"Wystapil blad podczas wyszukiwania/przygotowywania utworu: {e}")
            print(f"Blad !play: {e}")

    # --- Komenda !pause ---
    elif message.content == '!pause':
        guild_id = message.guild.id
        voice_client = voice_clients.get(guild_id)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await message.channel.send("Wstrzymano odtwarzanie.")
        else:
            await message.channel.send("Nic nie jest odtwarzane lub juz jest wstrzymane.")

    # --- Komenda !resume ---
    elif message.content == '!resume':
        guild_id = message.guild.id
        voice_client = voice_clients.get(guild_id)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await message.channel.send("Wznowiono odtwarzanie.")
        else:
            await message.channel.send("Nic nie jest wstrzymane.")

    # --- Komenda !volume ---
    elif message.content.startswith('!volume'):
        guild_id = message.guild.id
        voice_client = voice_clients.get(guild_id)

        if not voice_client or not voice_client.is_connected():
            await message.channel.send("Bot nie jest polaczony z kanalem glosowym.")
            return
        
        if not voice_client.source:
            await message.channel.send("Nic nie jest aktualnie odtwarzane.")
            return

        try:
            # Pobierz argument glosnosci
            args = message.content.split()
            if len(args) < 2:
                await message.channel.send("Uzycie: `!volume <wartosc>` (wartosc od 0 do 100).")
                return
            
            volume = int(args[1])

            if 0 <= volume <= 100:
                voice_client.source.volume = volume / 100.0
                await message.channel.send(f"Ustawiono glosnosc na {volume}%.")
            else:
                await message.channel.send("Wartosc glosnosci musi byc miedzy 0 a 100.")
        except ValueError:
            await message.channel.send("Nieprawidlowa wartosc glosnosci. Podaj liczbe od 0 do 100.")
        except Exception as e:
            await message.channel.send(f"Wystapil blad podczas zmiany glosnosci: {e}")
            print(f"Blad !volume: {e}")

    # --- Komenda !leave ---
    elif message.content == '!leave':
        guild_id = message.guild.id
        voice_client = voice_clients.get(guild_id)
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            del voice_clients[guild_id]
            # Czyscimy kolejke dla tego serwera po wyjsciu.
            if guild_id in music_queues:
                while not music_queues[guild_id].empty():
                    await music_queues[guild_id].get()
                del music_queues[guild_id]
            await message.channel.send("Opuscilem kanal glosowy.")
        else:
            await message.channel.send("Nie jestem na zadnym kanale glosowym.")

    # --- Komenda !pomoc ---
    elif message.content == '!pomoc':
        help_message = """
**Dostepne komendy bota muzycznego:**
`!play <link lub tytul>` - Odtwarza muzyke z YouTube lub Spotify (tylko pojedyncze utwory). Mozesz podac link lub tytul utworu.
`!pause` - Wstrzymuje aktualnie odtwarzany utwor.
`!resume` - Wznawia wstrzymany utwor.
`!volume <wartosc>` - Ustawia glosnosc odtwarzania (od 0 do 100).
`!leave` - Bot opuszcza kanal glosowy i czysci kolejke.
`!pomoc` - Wyswietla ta liste komend.

---
**UWAGA!** Bot w wersji BETA (1.0-beta) moga wystepowac bugi oraz bledy.
Podczas korzystania z komendy `!play`, wklej link do Spotify/Youtube (Pamietaj ze musisz byc na kanale!).
Zalecamy korzystanie z YOUTUBE poniewaz Spotify nie zawsze dziala!
        """
        await message.channel.send(help_message)

# Uruchomienie bota
# Bot bedzie dzialal, dopoki skrypt nie zostanie zatrzymany.
client.run(DISCORD_BOT_TOKEN)

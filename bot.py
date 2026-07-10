import logging
import re
import requests
from bs4 import BeautifulSoup
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InputTextMessageContent
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    InlineQueryHandler, filters, ContextTypes
)

# ============================================
# USE ENVIRONMENT VARIABLE FOR TOKEN
# export BOT_TOKEN="your_token_here"
# ============================================
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8860075842:AAG7fgxo4RCvZvstEhVsOxM-Kl8njoIydSE")

# ============================================
# WEBSITE CONFIGURATIONS
# ============================================
MOVIESDA_BASE = "https://moviesda33.com"
MOVIESDA_2026 = "https://moviesda33.com/tamil-2026-movies/"
MOVIESDA_2025 = "https://moviesda33.com/tamil-2025-movies/"
MOVIESDA_2024 = "https://moviesda33.com/tamil-2024-movies/"
MOVIESDA_2023 = "https://moviesda33.com/tamil-2023-movies/"
MOVIESDA_2022 = "https://moviesda33.com/tamil-2022-movies/"
MOVIESDA_2021 = "https://moviesda33.com/tamil-2021-movies/"

ISAIDUB_BASE = "https://isaidub.guru"
ISAIDUB_2026 = "https://isaidub.guru/tamil-2026-dubbed-movies/"
ISAIDUB_2025 = "https://isaidub.guru/tamil-2025-dubbed-movies/"
ISAIDUB_2024 = "https://isaidub.guru/tamil-2024-dubbed-movies/"
ISAIDUB_2023 = "https://isaidub.guru/tamil-2023-dubbed-movies/"
ISAIDUB_2022 = "https://isaidub.guru/tamil-2022-dubbed-movies/"

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================
# HELPER FUNCTIONS
# ============================================

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def check_url_exists(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
        return response.status_code == 200
    except:
        return False


def get_year_from_url(url):
    year_match = re.search(r"-(\d{4})-", url)
    if year_match:
        return year_match.group(1)
    return None


def generate_moviesda_urls(movie_name, year=None):
    slug = slugify(movie_name)
    urls = []
    if year:
        urls.append(f"{MOVIESDA_BASE}/{slug}-{year}-tamil-movie/")
        urls.append(f"{MOVIESDA_BASE}/{slug}-{year}/")
    for y in ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018"]:
        if y != year:
            urls.append(f"{MOVIESDA_BASE}/{slug}-{y}-tamil-movie/")
            urls.append(f"{MOVIESDA_BASE}/{slug}-{y}/")
    urls.append(f"{MOVIESDA_BASE}/{slug}-1080p-hd-movie/")
    urls.append(f"{MOVIESDA_BASE}/{slug}-720p-hd-movie/")
    urls.append(f"{MOVIESDA_BASE}/{slug}-480p-hd-movie/")
    urls.append(f"{MOVIESDA_BASE}/{slug}-full-movie/")
    urls.append(f"{MOVIESDA_BASE}/{slug}-hd-movie/")
    urls.append(f"{MOVIESDA_BASE}/{slug}/")
    return urls


def generate_isaidub_urls(movie_name, year=None):
    slug = slugify(movie_name)
    urls = []
    if year:
        urls.append(f"{ISAIDUB_BASE}/movie/{slug}-{year}-tamil-dubbed-web-series/")
        urls.append(f"{ISAIDUB_BASE}/movie/{slug}-{year}-tamil-dubbed-movie/")
        urls.append(f"{ISAIDUB_BASE}/movie/{slug}-{year}-tamil-dubbed/")
    for y in ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018"]:
        if y != year:
            urls.append(f"{ISAIDUB_BASE}/movie/{slug}-{y}-tamil-dubbed-web-series/")
            urls.append(f"{ISAIDUB_BASE}/movie/{slug}-{y}-tamil-dubbed-movie/")
            urls.append(f"{ISAIDUB_BASE}/movie/{slug}-{y}-tamil-dubbed/")
    urls.append(f"{ISAIDUB_BASE}/movie/{slug}-tamil-dubbed/")
    urls.append(f"{ISAIDUB_BASE}/movie/{slug}-hd-tamil-dubbed/")
    return urls


def scrape_movie_page(url, base_url):
    """Scrape movie page for poster, details, and download links"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")

        # Get title
        title_tag = soup.find("title")
        movie_title = "Unknown Movie"
        if title_tag:
            title_text = title_tag.text
            if "Download" in title_text:
                movie_title = title_text.split("Download")[0].strip()
            else:
                movie_title = title_text.strip()

        # Find poster image
        poster_url = None

        # Method 1: og:image meta tag
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            poster_url = og_image["content"]

        # Method 2: Look for poster images
        if not poster_url:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                alt = img.get("alt", "")
                if src and ("poster" in src.lower() or "movie" in alt.lower() or 
                           ("upload" in src.lower() and (".jpg" in src.lower() or ".png" in src.lower()))):
                    poster_url = src if src.startswith("http") else base_url + src
                    break

        # Method 3: First large image
        if not poster_url:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if src and (".jpg" in src.lower() or ".png" in src.lower() or ".jpeg" in src.lower()):
                    if "logo" not in src.lower() and "icon" not in src.lower():
                        poster_url = src if src.startswith("http") else base_url + src
                        break

        # Find download links - look for quality-specific links
        download_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if any(keyword in href.lower() for keyword in ["download", "720p", "1080p", "480p", "mp4", "hd", "mkv"]):
                full_url = href if href.startswith("http") else base_url + href
                if full_url not in [d["url"] for d in download_links]:
                    download_links.append({"text": text if text else "Download", "url": full_url})

        # Find movie info from page content
        movie_info = {}

        # Look for director, cast, rating in page text
        page_text = soup.get_text()

        # Director
        director_match = re.search(r"(?:Director|Directed by)[\s:]+([^\n]+)", page_text, re.I)
        if director_match:
            movie_info["Director"] = director_match.group(1).strip()[:50]

        # Cast
        cast_match = re.search(r"(?:Starring|Cast)[\s:]+([^\n]+)", page_text, re.I)
        if cast_match:
            movie_info["Starring"] = cast_match.group(1).strip()[:100]

        # Rating
        rating_match = re.search(r"(?:Rating|IMDb)[\s:]+([\d.]+)[\s/]*(?:10)?", page_text, re.I)
        if rating_match:
            movie_info["Rating"] = rating_match.group(1)

        # Genre
        genre_match = re.search(r"(?:Genre)[\s:]+([^\n]+)", page_text, re.I)
        if genre_match:
            movie_info["Genre"] = genre_match.group(1).strip()[:50]

        # Find synopsis
        synopsis = ""
        synopsis_header = soup.find(text=re.compile(r"Synopsis|Story|Plot", re.I))
        if synopsis_header:
            parent = synopsis_header.find_parent()
            if parent:
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    synopsis = next_sibling.get_text(strip=True)[:200]

        # If no synopsis found, get first paragraph
        if not synopsis:
            first_p = soup.find("p")
            if first_p:
                synopsis = first_p.get_text(strip=True)[:200]

        return {
            "title": movie_title,
            "url": url,
            "poster_url": poster_url,
            "download_links": download_links[:5],
            "info": movie_info,
            "synopsis": synopsis
        }
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        return None


def scrape_moviesda_year(year):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(f"{MOVIESDA_BASE}/tamil-{year}-movies/", headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        movies = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if year in text and len(text) > 3 and text[0].isalpha():
                if any(skip in href.lower() for skip in ["tamil-202", "dubbed", "collection", "mobile", "home"]):
                    continue
                full_url = href if href.startswith("http") else MOVIESDA_BASE + href
                movies.append({"name": text, "url": full_url})
        return movies[:20]
    except:
        return []


def scrape_isaidub_year(year):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(f"{ISAIDUB_BASE}/tamil-{year}-dubbed-movies/", headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        movies = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if len(text) > 3 and text[0].isalpha():
                if any(skip in href.lower() for skip in ["tamil-202", "collection", "mobile", "home"]):
                    continue
                if "/movie/" in href:
                    full_url = href if href.startswith("http") else ISAIDUB_BASE + href
                    movies.append({"name": text, "url": full_url})
        return movies[:20]
    except:
        return []


async def search_movie(movie_name, year=None):
    """Search movie in both sources"""
    results = []

    # Search Moviesda
    md_urls = generate_moviesda_urls(movie_name, year)
    for url in md_urls:
        if check_url_exists(url):
            movie_data = scrape_movie_page(url, MOVIESDA_BASE)
            if movie_data:
                found_year = get_year_from_url(url) or "Unknown"
                results.append({
                    "name": movie_name.title(),
                    "url": url,
                    "poster_url": movie_data.get("poster_url"),
                    "download_links": movie_data.get("download_links", []),
                    "info": movie_data.get("info", {}),
                    "synopsis": movie_data.get("synopsis", ""),
                    "source": "Moviesda",
                    "type": "Tamil",
                    "year": found_year
                })
                break

    # Search IsaiDub
    id_urls = generate_isaidub_urls(movie_name, year)
    for url in id_urls:
        if check_url_exists(url):
            movie_data = scrape_movie_page(url, ISAIDUB_BASE)
            if movie_data:
                found_year = get_year_from_url(url) or "Unknown"
                results.append({
                    "name": movie_name.title(),
                    "url": url,
                    "poster_url": movie_data.get("poster_url"),
                    "download_links": movie_data.get("download_links", []),
                    "info": movie_data.get("info", {}),
                    "synopsis": movie_data.get("synopsis", ""),
                    "source": "IsaiDub",
                    "type": "Tamil Dubbed",
                    "year": found_year
                })
                break

    return results




def generate_direct_quality_urls(movie_name):
    """Generate direct quality download URLs based on movie name only (no year)"""
    slug = slugify(movie_name)
    urls = {
        "720p": f"{MOVIESDA_BASE}/{slug}-720p-hd-movie/",
        "1080p": f"{MOVIESDA_BASE}/{slug}-1080p-hd-movie/",
        "480p": f"{MOVIESDA_BASE}/{slug}-480p-hd-movie/",
        "hd": f"{MOVIESDA_BASE}/{slug}-hd-movie/",
        "full": f"{MOVIESDA_BASE}/{slug}-full-movie/",
        "web_series_720p": f"{MOVIESDA_BASE}/{slug}-720p-hd-web-series/",
        "web_series_1080p": f"{MOVIESDA_BASE}/{slug}-1080p-hd-web-series/",
        "season_720p": f"{MOVIESDA_BASE}/{slug}-season-01-720p-hd-web-series/",
        "season_1080p": f"{MOVIESDA_BASE}/{slug}-season-01-1080p-hd-web-series/",
    }
    return urls


def check_ott_availability(movie_name):
    """Check if movie is available on OTT platforms"""
    try:
        # Search on JustWatch via web
        search_query = movie_name.replace(" ", "+").lower()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # Try JustWatch search
        jw_url = f"https://www.justwatch.com/in/search?q={search_query}"
        response = requests.get(jw_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for provider logos/names
            providers = []
            provider_keywords = {
                "netflix": "Netflix",
                "prime": "Amazon Prime Video", 
                "amazon": "Amazon Prime Video",
                "hotstar": "Disney+ Hotstar",
                "disney": "Disney+ Hotstar",
                "sony": "SonyLIV",
                "zee5": "ZEE5",
                "jio": "JioCinema",
                "mx": "MX Player",
                "youtube": "YouTube",
                "apple": "Apple TV+",
                "aha": "aha",
                "sun": "Sun NXT",
                "eros": "Eros Now"
            }

            page_text = soup.get_text().lower()
            page_html = response.text.lower()

            for keyword, platform_name in provider_keywords.items():
                if keyword in page_text or keyword in page_html:
                    if platform_name not in providers:
                        providers.append(platform_name)

            return providers[:5]  # Return top 5 providers

    except Exception as e:
        logger.error(f"OTT check error: {e}")

    return []


def search_tmdb_for_ott(movie_name):
    """Search TMDB for movie and check streaming providers"""
    try:
        tmdb_key = os.environ.get("5e954e81b228882695cc616e63d538b0", "")
        if not tmdb_key:
            return []

        query = movie_name.replace(" ", "%20")
        search_url = f"https://api.themoviedb.org/3/search/movie?query={query}&api_key={tmdb_key}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                movie_id = data["results"][0]["id"]

                # Get watch providers
                providers_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={tmdb_key}"
                prov_response = requests.get(providers_url, headers=headers, timeout=10)

                if prov_response.status_code == 200:
                    prov_data = prov_response.json()
                    india_providers = prov_data.get("results", {}).get("IN", {})

                    providers = []
                    flatrate = india_providers.get("flatrate", [])
                    for p in flatrate:
                        provider_name = p.get("provider_name", "")
                        if provider_name and provider_name not in providers:
                            providers.append(provider_name)

                    return providers[:5]

    except Exception as e:
        logger.error(f"TMDB OTT check error: {e}")

    return []

# ============================================
# BOT COMMANDS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    welcome_text = (
        f"🎬 Hyy buddyy {user}!\n\n"
        "🤖 Welcome to **Thoufii Movie Bot**!\n\n"
        "✨ **Features:**\n"
        "• 🖼️ Movie Poster + Details\n"
        "• 🔍 Auto Year Detection\n"
        "• 🎬 Tamil Movies (All Years)\n"
        "• 🌐 Tamil Dubbed (All Years)\n"
        "• ⬇️ Direct Download Links\n\n"
        "💡 **Just type movie name!**\n"
        "Poster + Details + Download link varum!\n\n"
        "📋 **Commands:**\n"
        "/tamil - Tamil 2026 Movies\n"
        "/tamil2025 - Tamil 2025 Movies\n"
        "/tamil2024 - Tamil 2024 Movies\n"
        "/tamil2023 - Tamil 2023 Movies\n"
        "/dubbed - Dubbed 2026 Movies\n"
        "/dubbed2025 - Dubbed 2025 Movies\n"
        "/help - Full Help"
    )
    keyboard = [
        [InlineKeyboardButton("🎬 Tamil 2026", callback_data="tamil"), InlineKeyboardButton("🎬 Tamil 2025", callback_data="tamil2025")],
        [InlineKeyboardButton("🎬 Tamil 2024", callback_data="tamil2024"), InlineKeyboardButton("🎬 Tamil 2023", callback_data="tamil2023")],
        [InlineKeyboardButton("🌐 Dubbed 2026", callback_data="dubbed"), InlineKeyboardButton("🌐 Dubbed 2025", callback_data="dubbed2025")],
        [InlineKeyboardButton("🔥 Trending", url=MOVIESDA_2026)]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def tamil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    movies = scrape_moviesda_year("2026")
    await send_movie_list(update, movies, "🎬 Tamil 2026 Movies", MOVIESDA_2026)


async def tamil2025(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    movies = scrape_moviesda_year("2025")
    await send_movie_list(update, movies, "🎬 Tamil 2025 Movies", MOVIESDA_2025)


async def tamil2024(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    movies = scrape_moviesda_year("2024")
    await send_movie_list(update, movies, "🎬 Tamil 2024 Movies", MOVIESDA_2024)


async def tamil2023(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    movies = scrape_moviesda_year("2023")
    await send_movie_list(update, movies, "🎬 Tamil 2023 Movies", MOVIESDA_2023)


async def dubbed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    movies = scrape_isaidub_year("2026")
    await send_movie_list(update, movies, "🌐 Tamil Dubbed 2026 Movies", ISAIDUB_2026, is_dubbed=True)


async def dubbed2025(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="typing")
    movies = scrape_isaidub_year("2025")
    await send_movie_list(update, movies, "🌐 Tamil Dubbed 2025 Movies", ISAIDUB_2025, is_dubbed=True)


async def send_movie_list(update, movies, title, more_url, is_dubbed=False):
    if movies:
        keyboard = []
        response_text = f"{title}\n\nSelect a movie:\n"
        for i, movie in enumerate(movies[:15]):
            keyboard.append([InlineKeyboardButton(f"{i+1}. {movie['name']}", url=movie["url"])])
        keyboard.append([InlineKeyboardButton("🔥 More Movies", url=more_url)])
        base_url = ISAIDUB_BASE if is_dubbed else MOVIESDA_BASE
        keyboard.append([InlineKeyboardButton("🌐 Home", url=base_url)])
        await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    else:
        base_url = ISAIDUB_BASE if is_dubbed else MOVIESDA_BASE
        keyboard = [
            [InlineKeyboardButton("🔥 More Movies", url=more_url)],
            [InlineKeyboardButton("🌐 Home", url=base_url)]
        ]
        await update.message.reply_text(f"{title}\n\nClick below:", reply_markup=InlineKeyboardMarkup(keyboard))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **Thoufii Movie Bot - Full Help**\n\n"
        "🎬 **Year-wise Commands:**\n"
        "/tamil - Tamil 2026 Movies\n"
        "/tamil2025 - Tamil 2025 Movies\n"
        "/tamil2024 - Tamil 2024 Movies\n"
        "/tamil2023 - Tamil 2023 Movies\n"
        "/dubbed - Dubbed 2026 Movies\n"
        "/dubbed2025 - Dubbed 2025 Movies\n\n"
        "🔍 **Search Examples:**\n"
        "• Leo (poster + details + link!)\n"
        "• Leo 2023 (exact year)\n"
        "• Vikram Vedha\n"
        "• Elle (dubbed)\n\n"
        "💡 Bot sends POSTER + DETAILS + DOWNLOAD LINK!"
    )
    await update.message.reply_text(help_text)


# ============================================
# INLINE MODE
# ============================================

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    if not query or len(query) < 2:
        tamil_movies = scrape_moviesda_year("2026")[:5]
        dubbed_movies = scrape_isaidub_year("2026")[:5]
        results = []
        for movie in tamil_movies:
            results.append(InlineQueryResultArticle(
                id=f"md_{movie['name']}",
                title=f"🎬 {movie['name']}",
                description="Tamil Movie",
                input_message_content=InputTextMessageContent(f"🎬 **{movie['name']}**\n\n🔗 [Open Movie Page]({movie['url']})"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Open Movie Page", url=movie["url"])]])
            ))
        for movie in dubbed_movies:
            results.append(InlineQueryResultArticle(
                id=f"id_{movie['name']}",
                title=f"🌐 {movie['name']}",
                description="Tamil Dubbed",
                input_message_content=InputTextMessageContent(f"🌐 **{movie['name']}**\n\n🔗 [Open Movie Page]({movie['url']})"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Open Movie Page", url=movie["url"])]])
            ))
        await update.inline_query.answer(results, cache_time=300)
        return

    results = []
    search_results = await search_movie(query)

    if search_results:
        for result in search_results:
            emoji = "🎬" if result["source"] == "Moviesda" else "🌐"
            year_text = f" ({result['year']})" if result['year'] != "Unknown" else ""
            results.append(InlineQueryResultArticle(
                id=f"{result['source']}_{result['name']}",
                title=f"{emoji} {result['name']}{year_text}",
                description=f"{result['type']} | {result['source']}",
                input_message_content=InputTextMessageContent(
                    f"{emoji} **{result['name']}** ({result['year']})\n\n"
                    f"📁 {result['type']}\n"
                    f"🔗 [Open Movie Page]({result['url']})"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{emoji} Open Movie Page", url=result["url"])]
                ])
            ))
    else:
        results.append(InlineQueryResultArticle(
            id="not_found",
            title="❌ Movie Not Found",
            description="Try different name or year",
            input_message_content=InputTextMessageContent(f"❌ **{query}** not found. Try adding year: Leo 2023")
        ))

    await update.inline_query.answer(results, cache_time=10)


# ============================================
# MESSAGE HANDLER - ENHANCED POSTER + DETAILS
# ============================================

async def handle_movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movie_input = update.message.text.strip()
    await update.message.chat.send_action(action="typing")

    # Extract year if provided
    year_match = re.search(r"(\d{4})$", movie_input)
    if year_match:
        year = year_match.group(1)
        movie_name = movie_input[:movie_input.rfind(year)].strip()
    else:
        year = None
        movie_name = movie_input

    # Search movie
    search_results = await search_movie(movie_name, year)
    # Add this line in search results

    if search_results:
        for result in search_results:
            emoji = "🎬" if result["source"] == "Moviesda" else "🌐"
            year_text = f" ({result['year']})" if result['year'] != "Unknown" else ""

            # Build enhanced caption with movie details
            caption = f"{emoji} **{result['name']}{year_text}**\n\n"
            caption += f"📁 **Type:** {result['type']}\n"
            caption += f"🎯 **Quality:** 720p | 1080p\n"

            # Add movie info
            info = result.get("info", {})
            if info.get("Director"):
                caption += f"🎬 **Director:** {info['Director']}\n"
            if info.get("Starring"):
                cast = info['Starring'][:80] + "..." if len(info['Starring']) > 80 else info['Starring']
                caption += f"⭐ **Cast:** {cast}\n"
            if info.get("Rating"):
                caption += f"⭐ **Rating:** {info['Rating']}/10\n"
            if info.get("Genre"):
                caption += f"🎭 **Genre:** {info['Genre']}\n"

            # Add synopsis
            if result.get("synopsis") and len(result["synopsis"]) > 10:
                synopsis = result["synopsis"][:180] + "..." if len(result["synopsis"]) > 180 else result["synopsis"]
                caption += f"\n📝 **Synopsis:** {synopsis}\n"

            caption += f"\n🔗 [Open Movie Page]({result['url']})"

            # Build keyboard with download links
            keyboard = []

            # Main movie page button
            keyboard.append([InlineKeyboardButton(f"{emoji} Open Movie Page", url=result["url"])])

            # MoviesPage Download button
            result_slug = slugify(result["name"])
            result_year = result["year"] if result["year"] != "Unknown" else "2026"
            keyboard.append([InlineKeyboardButton("⬇️ MoviesPage Download", url=f"https://moviespage.xyz/{result_slug}-{result_year}-tamil-movie/")])

            # Download quality buttons (if links found)
            if result.get("download_links"):
                for link in result["download_links"][:3]:
                    btn_text = f"⬇️ {link['text'][:25]}" if link['text'] else "⬇️ Download"
                    keyboard.append([InlineKeyboardButton(btn_text, url=link["url"])])

            # Dynamic Quality Download Links - Movie Name Only (No Year)
            quality_urls = generate_direct_quality_urls(result["name"])

            # Check all possible quality URLs and collect valid ones
            quality_buttons = []

            # Check movie format URLs
            if check_url_exists(quality_urls["720p"]):
                quality_buttons.append(InlineKeyboardButton("🎬 720p HD Movie", url=quality_urls["720p"]))
            if check_url_exists(quality_urls["1080p"]):
                quality_buttons.append(InlineKeyboardButton("🎬 1080p HD Movie", url=quality_urls["1080p"]))
            if check_url_exists(quality_urls["480p"]):
                quality_buttons.append(InlineKeyboardButton("🎬 480p HD Movie", url=quality_urls["480p"]))
            if check_url_exists(quality_urls["hd"]):
                quality_buttons.append(InlineKeyboardButton("🎬 HD Movie", url=quality_urls["hd"]))

            # Check web series format URLs
            if check_url_exists(quality_urls["web_series_720p"]):
                quality_buttons.append(InlineKeyboardButton("📺 720p Web Series", url=quality_urls["web_series_720p"]))
            if check_url_exists(quality_urls["web_series_1080p"]):
                quality_buttons.append(InlineKeyboardButton("📺 1080p Web Series", url=quality_urls["web_series_1080p"]))

            # Check season format URLs
            if check_url_exists(quality_urls["season_720p"]):
                quality_buttons.append(InlineKeyboardButton("📺 S01 720p", url=quality_urls["season_720p"]))
            if check_url_exists(quality_urls["season_1080p"]):
                quality_buttons.append(InlineKeyboardButton("📺 S01 1080p", url=quality_urls["season_1080p"]))

            # Add quality buttons if any found
            if quality_buttons:
                # Arrange in rows of 2
                for i in range(0, len(quality_buttons), 2):
                    keyboard.append(quality_buttons[i:i+2])
            else:
                # Fallback to main page if no direct quality links found
                keyboard.append([
                    InlineKeyboardButton("🎬 720p HD", url=result["url"]),
                    InlineKeyboardButton("🎬 1080p HD", url=result["url"])
                ])

            # Source links
            keyboard.append([
                InlineKeyboardButton("🎬 Moviesda", url=MOVIESDA_BASE),
                InlineKeyboardButton("🌐 IsaiDub", url=ISAIDUB_BASE)
            ])

            # Send poster image with caption and buttons
            if result.get("poster_url"):
                try:
                    await update.message.reply_photo(
                        photo=result["poster_url"],
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Photo send error: {e}")
                    # If photo fails, send text with link preview
                    await update.message.reply_text(
                        caption,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        disable_web_page_preview=False
                    )
            else:
                # No poster found, send text with link preview
                await update.message.reply_text(
                    caption,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=False
                )
    else:
        # Movie not found - Check OTT availability
        slug = slugify(movie_name)

        # Check OTT platforms
        ott_platforms = check_ott_availability(movie_name)
        if not ott_platforms:
            ott_platforms = search_tmdb_for_ott(movie_name)

        response_text = f"❌ **{movie_name.title()}** not found in our database.\n\n"

        if ott_platforms:
            response_text += f"📺 **Available on OTT Platforms:**\n"
            for platform in ott_platforms:
                response_text += f"• {platform}\n"
            response_text += "\n"
        else:
            response_text += "📺 **OTT Status:** Not found on major platforms\n\n"

        response_text += "💡 **Try:**\n• Different spelling\n• Add year (Leo 2023)\n• Browse year lists"

        keyboard = [
            [InlineKeyboardButton("🎬 Tamil 2026", url=MOVIESDA_2026), InlineKeyboardButton("🎬 Tamil 2025", url=MOVIESDA_2025)],
            [InlineKeyboardButton("🎬 Tamil 2024", url=MOVIESDA_2024), InlineKeyboardButton("🎬 Tamil 2023", url=MOVIESDA_2023)],
            [InlineKeyboardButton("🌐 IsaiDub", url=ISAIDUB_BASE)]
        ]
        await update.message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("⚠️ Error! Try again.")


# ============================================
# MAIN
# ============================================

def main():
    print("🤖 Thoufii Movie Bot (Enhanced) start aaguthu...")
    print("=" * 50)

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n❌ ERROR: Bot token set pannala!")
        print("👉 Set environment variable: export BOT_TOKEN=your_token\n")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tamil", tamil))
    app.add_handler(CommandHandler("tamil2025", tamil2025))
    app.add_handler(CommandHandler("tamil2024", tamil2024))
    app.add_handler(CommandHandler("tamil2023", tamil2023))
    app.add_handler(CommandHandler("dubbed", dubbed))
    app.add_handler(CommandHandler("dubbed2025", dubbed2025))
    app.add_handler(CommandHandler("help", help_command))

    # Inline mode
    app.add_handler(InlineQueryHandler(inline_query))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_search))

    # Errors
    app.add_error_handler(error_handler)

    print("✅ Bot ready! Enhanced Poster + Details + Links!")
    print("=" * 50)
    app.run_polling()


if __name__ == "__main__":
    main()
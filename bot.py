import os
import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import asyncio
import logging
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ============================================
# CLASE BANNER
# ============================================
class Banner:
    def __init__(self, name: str, banner_type: str, time_remaining: str, 
                 featured_5star: list, featured_4star: list, 
                 light_cones: list, duration_text: str = ""):
        self.name = name
        self.type = banner_type
        self.time_remaining = time_remaining
        self.featured_5star = featured_5star
        self.featured_4star = featured_4star
        self.light_cones = light_cones
        self.duration_text = duration_text

# ============================================
# CLASE BANNER SCRAPER
# ============================================
class BannerScraper:
    """Clase para hacer scraping de los banners desde la página principal de Prydwen"""
    
    def __init__(self):
        self.url = "https://www.prydwen.gg/star-rail/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def extract_image_url(self, img_tag) -> str:
        """Extrae la URL de la imagen"""
        if not img_tag:
            return None
        
        srcset = img_tag.get('srcset', '')
        if srcset:
            urls = srcset.split(',')
            if urls:
                last_url = urls[-1].strip().split(' ')[0]
                if last_url.startswith('http'):
                    return last_url
                return f"https://www.prydwen.gg{last_url}"
        
        src = img_tag.get('src', '')
        if src:
            if src.startswith('http'):
                return src
            return f"https://www.prydwen.gg{src}"
        
        return None
    
    def parse_character_card(self, card) -> dict:
        """Parsea una tarjeta de personaje"""
        try:
            name = "Unknown"
            a_tag = card.find('a')
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                name = href.split('/')[-1].replace('-', ' ').title()
            
            img_tag = card.find('img')
            image_url = self.extract_image_url(img_tag)
            
            element = "Unknown"
            element_tag = card.find('span', class_='floating-element')
            if element_tag:
                element_img = element_tag.find('img')
                if element_img and element_img.get('alt'):
                    element = element_img.get('alt')
            
            card_html = str(card)
            rarity = 5 if 'rarity-5' in card_html or 'rar-5' in card_html else 4
            
            return {
                'name': name,
                'image': image_url,
                'element': element,
                'rarity': rarity
            }
        except Exception:
            return None
    
    def parse_light_cone(self, cone_div) -> dict:
        """Parsea un cono de luz"""
        try:
            name_tag = cone_div.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            img_tag = cone_div.find('img')
            image_url = self.extract_image_url(img_tag)
            
            cone_html = str(cone_div)
            rarity = 5 if 'rarity-5' in cone_html else 4
            
            return {
                'name': name,
                'image': image_url,
                'rarity': rarity
            }
        except Exception:
            return None
    
    def extract_banners_from_html(self, soup):
        """Extrae los banners del HTML"""
        banners = []
        
        # Buscar secciones de banners (basado en el HTML que viste)
        banner_sections = soup.find_all('div', class_=re.compile('banner|event|warp', re.I))
        
        for section in banner_sections:
            try:
                # Buscar duración
                duration_text = ""
                duration_tag = section.find(string=re.compile('Event Duration', re.I))
                if duration_tag:
                    duration_text = duration_tag.parent.get_text() if duration_tag.parent else ""
                
                # Nombre del banner
                name = "Banner"
                name_tag = section.find(['h2', 'h3', 'h4'], class_=re.compile('name|title', re.I))
                if name_tag:
                    name = name_tag.text.strip()
                
                # Tipo
                banner_type = "Personaje"
                if "Light Cone" in str(section):
                    banner_type = "Cono de Luz"
                
                # Tiempo restante (difícil de extraer)
                time_remaining = "Consultar web"
                
                if name and duration_text:
                    banner = Banner(
                        name=name,
                        banner_type=banner_type,
                        time_remaining=time_remaining,
                        featured_5star=[],
                        featured_4star=[],
                        light_cones=[],
                        duration_text=duration_text
                    )
                    banners.append(banner)
                    
            except Exception as e:
                logger.error(f"Error en sección: {e}")
                continue
        
        return banners
    
    def get_banners(self):
        """Obtiene los banners desde la página principal"""
        try:
            logger.info(f"Obteniendo banners desde {self.url}")
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            banners = self.extract_banners_from_html(soup)
            
            if banners:
                logger.info(f"✅ Encontrados {len(banners)} banners")
                return banners
            else:
                logger.warning("Usando datos manuales de respaldo")
                return self.get_banners_manual()
                
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return self.get_banners_manual()
    
    def get_banners_manual(self):
        """Datos manuales de respaldo"""
        return [
            Banner(
                name="Black Swan & Kafka",
                banner_type="Personaje",
                time_remaining="17d 10h",
                featured_5star=[{
                    'name': 'Black Swan',
                    'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/e/e4/Character_Black_Swan_Splash_Art.png',
                    'element': 'Wind',
                    'rarity': 5
                }],
                featured_4star=[
                    {
                        'name': 'Pela',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/6/6f/Character_Pela_Splash_Art.png',
                        'element': 'Ice',
                        'rarity': 4
                    },
                    {
                        'name': 'Hanya',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/e/e9/Character_Hanya_Splash_Art.png',
                        'element': 'Physical',
                        'rarity': 4
                    }
                ],
                light_cones=[],
                duration_text="Event Duration: After 4.0 patch goes live — 2026/03/03 15:00"
            ),
            Banner(
                name="Reforged Remembrance",
                banner_type="Cono de Luz",
                time_remaining="17d 10h",
                featured_5star=[],
                featured_4star=[],
                light_cones=[{
                    'name': 'Reforged Remembrance',
                    'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/8/8e/Light_Cone_Reforged_Remembrance.png',
                    'rarity': 5
                }],
                duration_text="Event Duration: After 4.0 patch goes live — 2026/03/03 15:00"
            ),
            Banner(
                name="Tribbie & Yunli",
                banner_type="Personaje",
                time_remaining="38 días",
                featured_5star=[
                    {
                        'name': 'Tribbie',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/e/e5/Character_Tribbie_Splash_Art.png',
                        'element': 'Quantum',
                        'rarity': 5
                    },
                    {
                        'name': 'Yunli',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/0/0f/Character_Yunli_Splash_Art.png',
                        'element': 'Physical',
                        'rarity': 5
                    }
                ],
                featured_4star=[
                    {
                        'name': 'Guinaifen',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/5/5c/Character_Guinaifen_Splash_Art.png',
                        'element': 'Fire',
                        'rarity': 4
                    }
                ],
                light_cones=[],
                duration_text="Event Duration: After 4.0 patch goes live — 2026/03/24 15:00"
            )
        ]

# ============================================
# INSTANCIA GLOBAL DEL SCRAPER (¡IMPORTANTE!)
# ============================================
scraper = BannerScraper()  # <--- ESTA LÍNEA ES CRUCIAL

# ============================================
# FUNCIONES AUXILIARES
# ============================================
def get_element_emoji(element: str) -> str:
    """Devuelve el emoji del elemento"""
    elements = {
        'Physical': '💪', 'Fire': '🔥', 'Ice': '❄️',
        'Lightning': '⚡', 'Wind': '💨', 'Quantum': '⚛️',
        'Imaginary': '✨'
    }
    return elements.get(element, '🔮')

def create_banner_embed(banner: Banner) -> discord.Embed:
    """Crea un embed para un banner"""
    
    color = discord.Color.from_rgb(255, 215, 0) if banner.banner_type == "Personaje" else discord.Color.purple()
    emoji = "🦸" if banner.banner_type == "Personaje" else "⚔️"
    
    embed = discord.Embed(
        title=f"{emoji} {banner.name}",
        description=f"**Tipo:** {banner.banner_type}\n**⏳ Tiempo:** {banner.time_remaining}",
        color=color,
        timestamp=datetime.now()
    )
    
    if banner.duration_text:
        embed.add_field(name="📅 Duración", value=banner.duration_text, inline=False)
    
    if banner.featured_5star:
        chars = "\n".join([f"{get_element_emoji(c['element'])} **{c['name']}** (★5)" for c in banner.featured_5star[:4]])
        embed.add_field(name="✨ Personajes 5★", value=chars, inline=True)
    
    if banner.featured_4star:
        chars = "\n".join([f"{get_element_emoji(c['element'])} **{c['name']}** (★4)" for c in banner.featured_4star[:4]])
        embed.add_field(name="⭐ Personajes 4★", value=chars, inline=True)
    
    if banner.light_cones:
        cones = "\n".join([f"• **{c['name']}** ({'★5' if c['rarity']==5 else '★4'})" for c in banner.light_cones[:3]])
        embed.add_field(name="💫 Conos de Luz", value=cones, inline=False)
    
    # Thumbnail
    thumbnail = None
    if banner.featured_5star and banner.featured_5star[0].get('image'):
        thumbnail = banner.featured_5star[0]['image']
    elif banner.light_cones and banner.light_cones[0].get('image'):
        thumbnail = banner.light_cones[0]['image']
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    embed.set_footer(text="Datos de Prydwen.gg")
    return embed

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 50)
logger.info("INICIANDO BOT DE HONKAI STAR RAIL")
logger.info("=" * 50)

TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_STR = os.environ.get('DISCORD_CHANNEL_ID')

logger.info(f"DISCORD_TOKEN: {'✅' if TOKEN else '❌'}")
logger.info(f"DISCORD_CHANNEL_ID: {'✅' if CHANNEL_ID_STR else '❌'}")

TARGET_CHANNEL_ID = None
if CHANNEL_ID_STR:
    try:
        TARGET_CHANNEL_ID = int(CHANNEL_ID_STR.strip())
        logger.info(f"✅ Canal objetivo: {TARGET_CHANNEL_ID}")
    except ValueError:
        logger.error(f"❌ Channel ID inválido")

if not TOKEN:
    logger.error("❌ No hay token. Saliendo...")
    sys.exit(1)

# ============================================
# EVENTOS Y COMANDOS DEL BOT
# ============================================
@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} ha conectado!')
    await bot.change_presence(activity=discord.Game(name="!banners | HSR"))
    
    if TARGET_CHANNEL_ID:
        daily_banners.start()

@tasks.loop(hours=24)
async def daily_banners():
    await publish_banners()

async def publish_banners():
    if not TARGET_CHANNEL_ID:
        return
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        await send_banners(channel)

async def send_banners(channel):
    loading = await channel.send("🔄 Obteniendo banners...")
    
    try:
        banners = scraper.get_banners()
        
        if not banners:
            await loading.edit(content="❌ No se encontraron banners")
            return
        
        await loading.delete()
        
        for banner in banners:
            embed = create_banner_embed(banner)
            await channel.send(embed=embed)
            await asyncio.sleep(1)
        
        await channel.send(f"✅ Mostrando {len(banners)} banners")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await loading.edit(content=f"❌ Error: {str(e)[:100]}")

@bot.command(name='banners')
async def banners_command(ctx):
    await send_banners(ctx.channel)

@bot.command(name='refresh')
@commands.has_permissions(administrator=True)
async def refresh_banners(ctx):
    await ctx.send("🔄 Actualizando...")
    await send_banners(ctx.channel)

# ============================================
# INICIAR BOT
# ============================================
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Error: {e}")

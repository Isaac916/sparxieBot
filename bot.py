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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
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
        self.banner_type = banner_type
        self.time_remaining = time_remaining
        self.featured_5star = featured_5star if featured_5star else []
        self.featured_4star = featured_4star if featured_4star else []
        self.light_cones = light_cones if light_cones else []
        self.duration_text = duration_text

# ============================================
# CLASE BANNER SCRAPER
# ============================================
class BannerScraper:
    """Clase para hacer scraping de los banners desde la página principal de Prydwen"""
    
    def __init__(self):
        self.url = "https://www.prydwen.gg/star-rail/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def extract_image_url(self, img_tag) -> str:
        """Extrae la URL de la imagen del tag de Gatsby"""
        if not img_tag:
            return None
        
        # Método 1: srcset
        srcset = img_tag.get('srcset', '')
        if srcset:
            urls = srcset.split(',')
            if urls:
                last_url = urls[-1].strip().split(' ')[0]
                if last_url.startswith('http'):
                    return last_url
                elif last_url.startswith('/'):
                    return f"https://www.prydwen.gg{last_url}"
        
        # Método 2: src
        src = img_tag.get('src', '')
        if src:
            if src.startswith('http'):
                return src
            elif src.startswith('/'):
                return f"https://www.prydwen.gg{src}"
            else:
                return f"https://www.prydwen.gg/{src}"
        
        return "https://www.prydwen.gg/static/default-icon.png"
    
    def parse_character_card(self, card) -> dict:
        """Parsea una tarjeta de personaje"""
        try:
            # Nombre del personaje
            name = "Unknown"
            a_tag = card.find('a')
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                name = href.split('/')[-1].replace('-', ' ').title()
            
            # Imagen
            img_tag = card.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Elemento
            element = "Unknown"
            element_tag = card.find('span', class_='floating-element')
            if element_tag:
                element_img = element_tag.find('img')
                if element_img and element_img.get('alt'):
                    element = element_img.get('alt')
            
            # Rareza
            card_html = str(card)
            rarity = 5 if 'rarity-5' in card_html or 'rar-5' in card_html else 4
            
            return {
                'name': name,
                'image': image_url,
                'element': element,
                'rarity': rarity
            }
        except Exception as e:
            logger.error(f"Error parseando personaje: {e}")
            return None
    
    def parse_light_cone(self, cone_div) -> dict:
        """Parsea un cono de luz"""
        try:
            # Nombre
            name = "Unknown"
            name_tag = cone_div.find('span', class_='hsr-set-name')
            if name_tag:
                name = name_tag.text.strip()
            
            # Imagen
            image_url = None
            img_tag = cone_div.find('img')
            if img_tag:
                image_url = self.extract_image_url(img_tag)
            
            # Rareza
            cone_html = str(cone_div)
            rarity = 5 if 'rarity-5' in cone_html or 'rar-5' in cone_html else 4
            
            return {
                'name': name,
                'image': image_url,
                'rarity': rarity
            }
        except Exception:
            return None
    
    def get_banners(self):
        """Obtiene los banners desde la página principal"""
        try:
            logger.info(f"Obteniendo banners desde {self.url}")
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Intentar extraer banners
            banners = []
            
            # Buscar secciones que contengan información de banners
            event_sections = soup.find_all(['div', 'section'], string=re.compile(r'Event Duration', re.I))
            
            for section in event_sections:
                try:
                    parent = section.find_parent(['div', 'section'])
                    if not parent:
                        continue
                    
                    # Extraer duración
                    duration_text = section.parent.get_text() if section.parent else ""
                    
                    # Nombre del banner (buscar personajes destacados)
                    name = "Banner de Personaje"
                    
                    # Buscar personajes 5★
                    featured_5star = []
                    char_section = parent.find(string=re.compile(r'Featured 5★ character', re.I))
                    if char_section:
                        char_container = char_section.find_next(['div', 'p'])
                        if char_container:
                            char_links = char_container.find_all('a')
                            for link in char_links:
                                char_name = link.get_text().strip()
                                if char_name:
                                    featured_5star.append({
                                        'name': char_name,
                                        'image': None,
                                        'element': 'Unknown',
                                        'rarity': 5
                                    })
                    
                    # Determinar tipo
                    banner_type = "Personaje"
                    if "Light Cone" in parent.get_text():
                        banner_type = "Cono de Luz"
                    
                    # Tiempo restante (simplificado)
                    time_remaining = "Consultar web"
                    
                    if featured_5star:
                        name = featured_5star[0]['name'] + " Banner"
                    
                    banner = Banner(
                        name=name,
                        banner_type=banner_type,
                        time_remaining=time_remaining,
                        featured_5star=featured_5star,
                        featured_4star=[],
                        light_cones=[],
                        duration_text=duration_text
                    )
                    banners.append(banner)
                    
                except Exception as e:
                    logger.error(f"Error procesando sección: {e}")
                    continue
            
            if banners:
                logger.info(f"✅ Encontrados {len(banners)} banners")
                return banners
            else:
                logger.warning("No se encontraron banners, usando datos manuales")
                return self.get_banners_manual()
                
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return self.get_banners_manual()
    
    def get_banners_manual(self):
        """Datos manuales de respaldo actualizados"""
        return [
            Banner(
                name="Butterfly on Swordtip (Seele)",
                banner_type="Personaje",
                time_remaining="15 días",
                featured_5star=[{
                    'name': 'Seele',
                    'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/5/5d/Character_Seele_Splash_Art.png',
                    'element': 'Quantum',
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
                    },
                    {
                        'name': 'Qingque',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/0/0c/Character_Qingque_Splash_Art.png',
                        'element': 'Quantum',
                        'rarity': 4
                    }
                ],
                light_cones=[{
                    'name': 'In the Night',
                    'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/1/13/Light_Cone_In_the_Night.png',
                    'rarity': 5
                }],
                duration_text="Event Duration: 2024/01/17 - 2024/02/07"
            ),
            Banner(
                name="Brilliant Fixation (Reforged Remembrance)",
                banner_type="Cono de Luz",
                time_remaining="15 días",
                featured_5star=[],
                featured_4star=[],
                light_cones=[
                    {
                        'name': 'Reforged Remembrance',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/8/8e/Light_Cone_Reforged_Remembrance.png',
                        'rarity': 5
                    },
                    {
                        'name': 'Planetary Rendezvous',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/8/8d/Light_Cone_Planetary_Rendezvous.png',
                        'rarity': 4
                    },
                    {
                        'name': 'Resolution Shines As Pearls of Sweat',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/0/05/Light_Cone_Resolution_Shines_As_Pearls_of_Sweat.png',
                        'rarity': 4
                    }
                ],
                duration_text="Event Duration: 2024/01/17 - 2024/02/07"
            ),
            Banner(
                name="Stellar Warp (Estándar)",
                banner_type="Estándar",
                time_remaining="Permanente",
                featured_5star=[
                    {
                        'name': 'Himeko',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/3/37/Character_Himeko_Splash_Art.png',
                        'element': 'Fire',
                        'rarity': 5
                    },
                    {
                        'name': 'Welt',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Welt_Splash_Art.png',
                        'element': 'Imaginary',
                        'rarity': 5
                    },
                    {
                        'name': 'Bronya',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/e/e3/Character_Bronya_Splash_Art.png',
                        'element': 'Wind',
                        'rarity': 5
                    },
                    {
                        'name': 'Gepard',
                        'image': 'https://static.wikia.nocookie.net/houkai-star-rail/images/0/06/Character_Gepard_Splash_Art.png',
                        'element': 'Ice',
                        'rarity': 5
                    }
                ],
                featured_4star=[],
                light_cones=[],
                duration_text="Siempre disponible"
            )
        ]

# ============================================
# INSTANCIA GLOBAL DEL SCRAPER
# ============================================
scraper = BannerScraper()

# ============================================
# FUNCIONES AUXILIARES
# ============================================
def get_element_emoji(element: str) -> str:
    """Devuelve el emoji del elemento"""
    elements = {
        'Physical': '💪', 'Fire': '🔥', 'Ice': '❄️',
        'Lightning': '⚡', 'Wind': '💨', 'Quantum': '⚛️',
        'Imaginary': '✨', 'physical': '💪', 'fire': '🔥',
        'ice': '❄️', 'lightning': '⚡', 'wind': '💨',
        'quantum': '⚛️', 'imaginary': '✨'
    }
    return elements.get(element, elements.get(element.lower(), '🔮'))

def create_banner_embed(banner: Banner) -> discord.Embed:
    """Crea un embed para un banner"""
    
    # Color y emoji según tipo
    if banner.banner_type == "Personaje":
        color = discord.Color.from_rgb(255, 215, 0)  # Dorado
        emoji = "🦸"
    elif banner.banner_type == "Cono de Luz":
        color = discord.Color.from_rgb(147, 112, 219)  # Púrpura
        emoji = "⚔️"
    else:
        color = discord.Color.blue()
        emoji = "📚"
    
    embed = discord.Embed(
        title=f"{emoji} {banner.name}",
        description=f"**Tipo:** {banner.banner_type}\n**⏳ Tiempo restante:** {banner.time_remaining}",
        color=color,
        timestamp=datetime.now()
    )
    
    # Duración del evento
    if banner.duration_text:
        clean_duration = banner.duration_text.replace('Event Duration', 'Duración')
        if len(clean_duration) > 1024:
            clean_duration = clean_duration[:1021] + "..."
        embed.add_field(name="📅 Duración", value=clean_duration, inline=False)
    
    # Personajes 5★
    if banner.featured_5star:
        chars_text = ""
        for char in banner.featured_5star[:4]:
            if char and char.get('name'):
                element_emoji = get_element_emoji(char.get('element', 'Unknown'))
                chars_text += f"{element_emoji} **{char['name']}** (★5)\n"
        
        if chars_text:
            embed.add_field(name="✨ Personajes 5★", value=chars_text, inline=True)
    
    # Personajes 4★
    if banner.featured_4star:
        chars_text = ""
        for char in banner.featured_4star[:4]:
            if char and char.get('name'):
                element_emoji = get_element_emoji(char.get('element', 'Unknown'))
                chars_text += f"{element_emoji} **{char['name']}** (★4)\n"
        
        if chars_text:
            embed.add_field(name="⭐ Personajes 4★", value=chars_text, inline=True)
    
    # Conos de luz
    if banner.light_cones:
        cones_text = ""
        for cone in banner.light_cones[:3]:
            if cone and cone.get('name'):
                rarity_star = "★5" if cone.get('rarity') == 5 else "★4"
                cones_text += f"• **{cone['name']}** ({rarity_star})\n"
        
        if cones_text:
            embed.add_field(name="💫 Conos de Luz", value=cones_text, inline=False)
    
    # Thumbnail
    thumbnail_url = None
    if banner.featured_5star and len(banner.featured_5star) > 0 and banner.featured_5star[0].get('image'):
        thumbnail_url = banner.featured_5star[0]['image']
    elif banner.light_cones and len(banner.light_cones) > 0 and banner.light_cones[0].get('image'):
        thumbnail_url = banner.light_cones[0]['image']
    else:
        thumbnail_url = "https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png"
    
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    embed.set_footer(text="Datos de Prydwen.gg • Actualizado diariamente")
    
    return embed

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 50)
logger.info("INICIANDO BOT DE HONKAI STAR RAIL")
logger.info("=" * 50)

TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_STR = os.environ.get('DISCORD_CHANNEL_ID')

logger.info(f"DISCORD_TOKEN: {'✅ ENCONTRADO' if TOKEN else '❌ NO ENCONTRADO'}")
logger.info(f"DISCORD_CHANNEL_ID: {'✅ ENCONTRADO' if CHANNEL_ID_STR else '❌ NO ENCONTRADO'}")

TARGET_CHANNEL_ID = None
if CHANNEL_ID_STR:
    try:
        TARGET_CHANNEL_ID = int(CHANNEL_ID_STR.strip())
        logger.info(f"✅ Canal objetivo: {TARGET_CHANNEL_ID}")
    except ValueError:
        logger.error(f"❌ DISCORD_CHANNEL_ID no es válido: {CHANNEL_ID_STR}")

if not TOKEN:
    logger.error("❌ ERROR CRÍTICO: No hay token de Discord")
    sys.exit(1)

# ============================================
# EVENTOS Y COMANDOS DEL BOT
# ============================================
@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} ha conectado a Discord!')
    
    # Estado personalizado
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="los banners de HSR | !banners"
        )
    )
    
    # Iniciar tarea diaria
    if TARGET_CHANNEL_ID:
        daily_banners.start()
        logger.info(f"📅 Tarea diaria iniciada para el canal {TARGET_CHANNEL_ID}")

@tasks.loop(hours=24)
async def daily_banners():
    """Publica banners cada 24 horas"""
    await publish_banners()

@daily_banners.before_loop
async def before_daily_banners():
    """Espera a que el bot esté listo"""
    await bot.wait_until_ready()

async def publish_banners():
    """Publica banners en el canal configurado"""
    if not TARGET_CHANNEL_ID:
        return
    
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        logger.error(f"❌ No se encontró el canal {TARGET_CHANNEL_ID}")
        return
    
    await send_banners(channel)

async def send_banners(channel):
    """Envía los banners a un canal"""
    
    loading_msg = await channel.send("🔄 Obteniendo información de los banners de Honkai: Star Rail...")
    
    try:
        banners = scraper.get_banners()
        
        if not banners:
            await loading_msg.edit(content="❌ No se pudieron obtener los banners. Intenta más tarde.")
            return
        
        await loading_msg.delete()
        
        # Enviar cada banner
        banners_enviados = 0
        for banner in banners:
            try:
                embed = create_banner_embed(banner)
                await channel.send(embed=embed)
                banners_enviados += 1
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error enviando banner {banner.name}: {e}")
                continue
        
        # Mensaje de resumen
        if banners_enviados > 0:
            await channel.send(f"✅ Mostrando **{banners_enviados}** banners activos.\n📅 Próxima actualización automática en 24h.")
        else:
            await channel.send("❌ No se pudo enviar ningún banner.")
        
        logger.info(f"✅ {banners_enviados} banners enviados a {channel.name}")
        
    except Exception as e:
        logger.error(f"❌ Error enviando banners: {e}")
        await loading_msg.edit(content=f"❌ Error: {str(e)[:200]}")

@bot.command(name='banners')
async def banners_command(ctx):
    """Comando para mostrar los banners actuales"""
    await send_banners(ctx.channel)

@bot.command(name='banner')
async def banner_info(ctx, *, banner_name: str = None):
    """Muestra información de un banner específico"""
    if not banner_name:
        await ctx.send("❌ Usa: `!banner nombre_del_banner`")
        return
    
    banners = scraper.get_banners()
    
    # Buscar por nombre
    found_banners = [b for b in banners if banner_name.lower() in b.name.lower()]
    
    # Buscar por personaje
    if not found_banners:
        for b in banners:
            for char in b.featured_5star + b.featured_4star:
                if banner_name.lower() in char.get('name', '').lower():
                    found_banners.append(b)
                    break
    
    if not found_banners:
        await ctx.send(f"❌ No se encontró '{banner_name}'")
        return
    
    for banner in found_banners[:2]:  # Máximo 2 banners
        embed = create_banner_embed(banner)
        await ctx.send(embed=embed)

@bot.command(name='refresh')
@commands.has_permissions(administrator=True)
async def refresh_banners(ctx):
    """Fuerza actualización (solo admins)"""
    await ctx.send("🔄 Actualizando banners manualmente...")
    await send_banners(ctx.channel)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado. Usa `!banners`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permiso para usar este comando")
    else:
        logger.error(f"Error en comando: {error}")
        await ctx.send(f"❌ Error: {str(error)[:100]}")

# ============================================
# INICIAR BOT
# ============================================
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"❌ Error iniciando bot: {e}")
        sys.exit(1)

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

# Configurar logging para ver todo en Railway
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

class BannerScraper:
    """Clase para hacer scraping de los banners desde la página principal de Prydwen"""
    
    def __init__(self):
        # ¡URL CORREGIDA! Usamos la página principal
        self.url = "https://www.prydwen.gg/star-rail/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def extract_banners_from_html(self, soup):
        """Extrae los banners del HTML basado en la estructura real"""
        banners = []
        
        # Buscar todas las secciones de eventos que contienen banners
        # En la página, los banners están dentro de contenedores con información de duración
        event_sections = soup.find_all('div', string=re.compile(r'Event Duration:', re.I))
        
        for section in event_sections:
            try:
                # Encontrar el contenedor padre que agrupa toda la info del banner
                parent = section.find_parent(['div', 'section'])
                if not parent:
                    continue
                
                # Extraer duración
                duration_text = section.parent.get_text() if section.parent else ""
                
                # Buscar nombre del banner (usando el personaje o cono destacado)
                name = "Banner de Personaje"
                featured_char = parent.find('strong', string=re.compile(r'Featured 5★ character', re.I))
                if featured_char:
                    # Buscar el nombre del personaje
                    char_name_tag = featured_char.find_next(['a', 'strong'])
                    if char_name_tag:
                        name = char_name_tag.get_text().strip()
                
                # Determinar tipo
                banner_type = "Personaje"
                if "Light Cone" in parent.get_text():
                    banner_type = "Cono de Luz"
                
                # Buscar tiempo restante (difícil de extraer directamente, usamos la duración)
                time_remaining = "Consultar web"
                
                # Crear banner con la información disponible
                banner = Banner(
                    name=name,
                    banner_type=banner_type,
                    time_remaining=time_remaining,
                    featured_5star=[],  # Podríamos extraer más detalles si es necesario
                    featured_4star=[],
                    light_cones=[],
                    duration_text=duration_text
                )
                banners.append(banner)
                
            except Exception as e:
                logger.error(f"Error extrayendo banner: {e}")
                continue
        
        return banners
    
    def get_banners(self):
        """Obtiene los banners desde la página principal"""
        try:
            logger.info(f"Obteniendo banners desde {self.url}")
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Intentar extraer banners con el método específico
            banners = self.extract_banners_from_html(soup)
            
            if banners:
                logger.info(f"✅ Encontrados {len(banners)} banners")
                return banners
            else:
                logger.warning("No se encontraron banners con el método específico, usando respaldo")
                return self.get_banners_manual()
                
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return self.get_banners_manual()
    
    def get_banners_manual(self):
        """Datos manuales de respaldo (actualizados con la info de la página)"""
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

def get_element_emoji(element: str) -> str:
    """Devuelve el emoji del elemento"""
    elements = {
        'Physical': '💪',
        'Fire': '🔥',
        'Ice': '❄️',
        'Lightning': '⚡',
        'Wind': '💨',
        'Quantum': '⚛️',
        'Imaginary': '✨'
    }
    return elements.get(element, '🔮')

def create_banner_embed(banner: Banner) -> discord.Embed:
    """Crea un embed para un banner"""
    
    # Color según tipo
    if banner.banner_type == "Personaje":
        color = discord.Color.from_rgb(255, 215, 0)  # Dorado
        emoji = "🦸"
    elif banner.banner_type == "Cono de Luz":
        color = discord.Color.from_rgb(147, 112, 219)  # Púrpura
        emoji = "⚔️"
    else:
        color = discord.Color.blue()
        emoji = "🎁"
    
    embed = discord.Embed(
        title=f"{emoji} {banner.name}",
        description=f"**Tipo:** {banner.banner_type}\n**⏳ Tiempo restante:** {banner.time_remaining}",
        color=color,
        timestamp=datetime.now()
    )
    
    # Duración del evento
    if banner.duration_text:
        # Limpiar el texto de duración
        clean_duration = banner.duration_text.replace('Event Duration', 'Duración').replace('server time', 'hora del servidor')
        embed.add_field(
            name="📅 Duración",
            value=clean_duration,
            inline=False
        )
    
    # Personajes 5★
    if banner.featured_5star:
        chars_text = ""
        for char in banner.featured_5star[:4]:
            element_emoji = get_element_emoji(char['element'])
            chars_text += f"{element_emoji} **{char['name']}** (★5)\n"
        
        if chars_text:
            embed.add_field(name="✨ Personajes 5★", value=chars_text, inline=True)
    
    # Personajes 4★
    if banner.featured_4star:
        chars_text = ""
        for char in banner.featured_4star[:4]:
            element_emoji = get_element_emoji(char['element'])
            chars_text += f"{element_emoji} **{char['name']}** (★4)\n"
        
        if chars_text:
            embed.add_field(name="⭐ Personajes 4★", value=chars_text, inline=True)
    
    # Conos de luz
    if banner.light_cones:
        cones_text = ""
        for cone in banner.light_cones[:3]:
            rarity_star = "★5" if cone['rarity'] == 5 else "★4"
            cones_text += f"• **{cone['name']}** ({rarity_star})\n"
        
        if cones_text:
            embed.add_field(name="💫 Conos de Luz", value=cones_text, inline=False)
    
    # Thumbnail
    if banner.featured_5star and banner.featured_5star[0].get('image'):
        embed.set_thumbnail(url=banner.featured_5star[0]['image'])
    elif banner.light_cones and banner.light_cones[0].get('image'):
        embed.set_thumbnail(url=banner.light_cones[0]['image'])
    
    embed.set_footer(text="Datos de Prydwen.gg • Actualizado diariamente")
    
    return embed

@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} ha conectado a Discord!')
    logger.info(f'📊 ID del bot: {bot.user.id}')
    
    # Estado personalizado
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="los banners de HSR | !banners"
        )
    )
    
    # Iniciar tarea diaria si hay canal configurado
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
        logger.warning("⚠️ No hay canal configurado para publicaciones automáticas")
        return
    
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        logger.error(f"❌ No se encontró el canal {TARGET_CHANNEL_ID}")
        return
    
    await send_banners(channel)

async def send_banners(channel):
    """Envía los banners a un canal"""
    
    loading_msg = await channel.send("🔄 Obteniendo información de los banners...")
    
    try:
        banners = scraper.get_banners()
        
        if not banners:
            await loading_msg.edit(content="❌ No se pudieron obtener los banners. Intenta más tarde.")
            return
        
        await loading_msg.delete()
        
        # Enviar cada banner
        for banner in banners:
            embed = create_banner_embed(banner)
            await channel.send(embed=embed)
            await asyncio.sleep(1)
        
        # Mensaje de resumen
        await channel.send(f"✅ Mostrando **{len(banners)}** banners activos.\n📅 Próxima actualización automática en 24h.")
        
        logger.info(f"✅ Banners enviados a {channel.name}")
        
    except Exception as e:
        logger.error(f"❌ Error enviando banners: {e}")
        await loading_msg.edit(content=f"❌ Error: {str(e)[:100]}")

@bot.command(name='banners')
async def banners_command(ctx):
    """Comando para mostrar banners"""
    await send_banners(ctx.channel)

@bot.command(name='banner')
async def banner_info(ctx, *, banner_name: str = None):
    """Muestra información de un banner específico"""
    if not banner_name:
        await ctx.send("❌ Usa: `!banner nombre_del_banner`")
        return
    
    banners = scraper.get_banners()
    
    found_banners = [b for b in banners if banner_name.lower() in b.name.lower()]
    
    if not found_banners:
        # Buscar por personaje
        for b in banners:
            for char in b.featured_5star + b.featured_4star:
                if banner_name.lower() in char['name'].lower():
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
    await ctx.send("🔄 Actualizando banners...")
    await send_banners(ctx.channel)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado. Usa `!banners`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permiso")
    else:
        logger.error(f"Error: {error}")
        await ctx.send(f"❌ Error: {str(error)[:100]}")

# ============================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ============================================

logger.info("=" * 50)
logger.info("INICIANDO BOT DE HONKAI STAR RAIL")
logger.info("=" * 50)

# Leer variables de entorno
TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_STR = os.environ.get('DISCORD_CHANNEL_ID')

# Diagnóstico
logger.info("🔍 DIAGNÓSTICO DE VARIABLES:")
logger.info(f"DISCORD_TOKEN: {'✅ ENCONTRADO' if TOKEN else '❌ NO ENCONTRADO'}")
if TOKEN:
    logger.info(f"  Longitud: {len(TOKEN)} caracteres")
    logger.info(f"  Primeros 5 chars: {TOKEN[:5]}...")
else:
    logger.error("  ⚠️  El token es necesario para que el bot funcione")

logger.info(f"DISCORD_CHANNEL_ID: {'✅ ENCONTRADO' if CHANNEL_ID_STR else '❌ NO ENCONTRADO'}")
if CHANNEL_ID_STR:
    logger.info(f"  Valor: {CHANNEL_ID_STR}")
logger.info("=" * 50)

# Convertir channel_id a entero si existe
TARGET_CHANNEL_ID = None
if CHANNEL_ID_STR:
    try:
        TARGET_CHANNEL_ID = int(CHANNEL_ID_STR.strip())
        logger.info(f"✅ Canal objetivo configurado: {TARGET_CHANNEL_ID}")
    except ValueError:
        logger.error(f"❌ DISCORD_CHANNEL_ID no es un número válido: {CHANNEL_ID_STR}")
        TARGET_CHANNEL_ID = None

# Ejecutar el bot
if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ ERROR CRÍTICO: No hay token de Discord")
        logger.error("📝 Solución: Configura DISCORD_TOKEN en Railway (Variables → New Variable)")
        logger.error("   Nombre: DISCORD_TOKEN")
        logger.error("   Valor: [tu token de Discord]")
        sys.exit(1)
    
    try:
        logger.info("🚀 Iniciando bot...")
        bot.run(TOKEN, log_handler=None)  # log_handler=None para evitar duplicados
    except discord.LoginFailure:
        logger.error("❌ ERROR: Token inválido")
        logger.error("📝 Solución: Verifica que el token en Railway sea correcto")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error iniciando bot: {e}")
        sys.exit(1)

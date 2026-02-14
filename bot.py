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
    """Clase para hacer scraping de los banners de Prydwen"""
    
    def __init__(self):
        self.url = "https://www.prydwen.gg/star-rail/warp-events"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def extract_image_url(self, img_tag) -> str:
        """Extrae la URL de la imagen del tag de Gatsby"""
        if not img_tag:
            return None
        
        # Buscar en srcset
        srcset = img_tag.get('srcset', '')
        if srcset:
            urls = srcset.split(',')
            if urls:
                last_url = urls[-1].strip().split(' ')[0]
                if last_url.startswith('http'):
                    return last_url
                return f"https://www.prydwen.gg{last_url}"
        
        # Buscar en src
        src = img_tag.get('src', '')
        if src:
            if src.startswith('http'):
                return src
            return f"https://www.prydwen.gg{src}"
        
        return None
    
    def parse_character_card(self, card) -> dict:
        """Parsea una tarjeta de personaje"""
        try:
            # Nombre del personaje
            name_tag = card.find('a')
            if name_tag and name_tag.get('href'):
                name = name_tag.get('href', '').split('/')[-1].replace('-', ' ').title()
            else:
                name = "Unknown"
            
            # Imagen del personaje
            img_tag = card.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Elemento
            element_tag = card.find('span', class_='floating-element')
            element_img = element_tag.find('img') if element_tag else None
            element = element_img.get('alt', 'Unknown') if element_img else "Unknown"
            
            # Rareza
            rarity = 5 if 'rarity-5' in str(card) else 4
            
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
            # Imagen
            img_tag = cone_div.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Nombre
            name_tag = cone_div.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            # Rareza
            rarity = 5 if 'rarity-5' in str(cone_div) else 4
            
            return {
                'name': name,
                'image': image_url,
                'rarity': rarity
            }
        except Exception as e:
            logger.error(f"Error parseando cono de luz: {e}")
            return None
    
    def get_banners(self) -> list:
        """Obtiene todos los banners actuales"""
        banners = []
        
        try:
            logger.info(f"Obteniendo datos de {self.url}")
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todos los banners
            banner_items = soup.find_all('div', class_='swan accordion-item')
            logger.info(f"Encontrados {len(banner_items)} banners")
            
            for item in banner_items:
                try:
                    # Nombre del banner
                    name_tag = item.find('div', class_='event-name')
                    banner_name = name_tag.text.strip() if name_tag else "Banner sin nombre"
                    
                    # Tiempo restante
                    time_tag = item.find('span', class_='time')
                    time_remaining = time_tag.text.strip() if time_tag else "Tiempo desconocido"
                    
                    # Duración
                    duration_tag = item.find('p', class_='duration')
                    duration_text = duration_tag.text.strip() if duration_tag else ""
                    
                    # Tipo de banner
                    banner_type = "Personaje"
                    if "Light Cone" in duration_text or "light cone" in str(item).lower():
                        banner_type = "Cono de Luz"
                    
                    # Personajes
                    featured_5star = []
                    featured_4star = []
                    
                    characters_section = item.find_all('div', class_='featured-characters')
                    for section in characters_section:
                        character_cards = section.find_all('div', class_='avatar-card')
                        for card in character_cards:
                            char_data = self.parse_character_card(card)
                            if char_data:
                                if char_data['rarity'] == 5:
                                    featured_5star.append(char_data)
                                else:
                                    featured_4star.append(char_data)
                    
                    # Conos de luz
                    light_cones = []
                    cone_sections = item.find_all('div', class_='featured-cone')
                    for section in cone_sections:
                        cone_items = section.find_all('div', class_='accordion-item')
                        for cone in cone_items:
                            cone_data = self.parse_light_cone(cone)
                            if cone_data:
                                light_cones.append(cone_data)
                    
                    # Crear banner solo si tiene contenido
                    if featured_5star or featured_4star or light_cones:
                        banner = Banner(
                            name=banner_name,
                            banner_type=banner_type,
                            time_remaining=time_remaining,
                            featured_5star=featured_5star,
                            featured_4star=featured_4star,
                            light_cones=light_cones,
                            duration_text=duration_text
                        )
                        banners.append(banner)
                        logger.info(f"Banner añadido: {banner_name}")
                
                except Exception as e:
                    logger.error(f"Error procesando banner: {e}")
                    continue
            
            logger.info(f"Total banners parseados: {len(banners)}")
            
        except requests.RequestException as e:
            logger.error(f"Error de conexión: {e}")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
        
        return banners

# Instancia del scraper
scraper = BannerScraper()

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

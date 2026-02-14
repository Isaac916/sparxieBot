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
                 featured_5star_char: list, featured_4star_char: list, 
                 featured_5star_cone: list, featured_4star_cone: list,
                 duration_text: str = ""):
        self.name = name
        self.banner_type = banner_type
        self.time_remaining = time_remaining
        self.featured_5star_char = featured_5star_char if featured_5star_char else []
        self.featured_4star_char = featured_4star_char if featured_4star_char else []
        self.featured_5star_cone = featured_5star_cone if featured_5star_cone else []
        self.featured_4star_cone = featured_4star_cone if featured_4star_cone else []
        self.duration_text = duration_text

# ============================================
# CLASE BANNER SCRAPER
# ============================================
class BannerScraper:
    """Clase para hacer scraping de TODOS los banners de warps en Prydwen"""
    
    def __init__(self):
        self.url = "https://www.prydwen.gg/star-rail/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Imagen por defecto para fallback
        self.default_image = "https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png"
    
    def extract_image_url(self, img_tag) -> str:
        """Extrae la URL completa de la imagen de manera segura"""
        if not img_tag:
            return None
        
        url = None
        
        try:
            # Método 1: srcset (prioridad)
            srcset = img_tag.get('srcset', '')
            if srcset:
                urls = srcset.split(',')
                if urls:
                    # Tomar la URL de mayor resolución (última)
                    last_url = urls[-1].strip()
                    if ' ' in last_url:
                        last_url = last_url.split(' ')[0]
                    
                    if last_url.startswith('http'):
                        url = last_url
                    elif last_url.startswith('/'):
                        url = f"https://www.prydwen.gg{last_url}"
                    elif last_url.startswith('static'):
                        url = f"https://www.prydwen.gg/{last_url}"
            
            # Método 2: src
            if not url:
                src = img_tag.get('src', '')
                if src and not src.startswith('data:'):  # Ignorar data URIs
                    if src.startswith('http'):
                        url = src
                    elif src.startswith('/'):
                        url = f"https://www.prydwen.gg{src}"
                    elif src.startswith('static'):
                        url = f"https://www.prydwen.gg/{src}"
            
            # Validar que sea una URL HTTP/HTTPS válida
            if url and (url.startswith('http://') or url.startswith('https://')):
                # Limpiar la URL de posibles caracteres extraños
                url = url.split('?')[0].split('#')[0]
                return url
            
        except Exception as e:
            logger.error(f"Error extrayendo URL: {e}")
        
        return None
    
    def is_warp_banner(self, item) -> bool:
        """Determina si un accordion-item es un WARP (banner de personajes/conos)"""
        html = str(item)
        
        # Características de un warp banner:
        # 1. Tiene clase 'swan' en el accordion-item (los warps tienen clase 'swan')
        # 2. Tiene secciones 'featured-characters' o 'featured-cone'
        # 3. Tiene p.featured con rarezas (5★, 4★)
        
        has_swan_class = 'swan' in item.get('class', []) if item.has_attr('class') else False
        has_featured_chars = 'featured-characters' in html
        has_featured_cones = 'featured-cone' in html
        has_featured_text = 'featured' in html and ('5★' in html or '4★' in html)
        has_event_name = 'event-name' in html
        
        # Los warps SIEMPRE tienen swan class O featured content
        return (has_swan_class or has_featured_chars or has_featured_cones) and has_featured_text and has_event_name
    
    def classify_banner_type(self, item) -> str:
        """Clasifica si es banner de personaje, cono o mixto"""
        html = str(item).lower()
        has_chars = 'featured-characters' in html
        has_cones = 'featured-cone' in html
        
        # Verificar si tiene personajes 5★
        has_5star_char = '5★' in html and 'character' in html
        
        if has_chars and not has_cones:
            return "Personaje"
        elif has_cones and not has_chars:
            return "Cono de Luz"
        else:
            return "Mixto (Doble)"
    
    def parse_character(self, card) -> dict:
        """Parsea un personaje de avatar-card"""
        try:
            a_tag = card.find('a')
            name = "Unknown"
            
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                name = href.split('/')[-1].replace('-', ' ').title()
            
            # Imagen
            img_tag = card.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Si no hay imagen válida, usar la imagen por defecto
            if not image_url:
                image_url = self.default_image
            
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
            return {
                'name': "Unknown",
                'image': self.default_image,
                'element': "Unknown",
                'rarity': 4
            }
    
    def parse_light_cone(self, cone_item) -> dict:
        """Parsea un cono de luz"""
        try:
            name_tag = cone_item.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            img_tag = cone_item.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Si no hay imagen válida, usar la imagen por defecto
            if not image_url:
                image_url = self.default_image
            
            cone_html = str(cone_item)
            rarity = 5 if 'rarity-5' in cone_html or 'rar-5' in cone_html else 4
            
            return {
                'name': name,
                'image': image_url,
                'rarity': rarity
            }
        except Exception:
            return {
                'name': "Unknown Cone",
                'image': self.default_image,
                'rarity': 4
            }
    
    def extract_characters(self, item):
        """Extrae personajes 5★ y 4★ de un banner"""
        featured_5star_char = []
        featured_4star_char = []
        
        char_sections = item.find_all('div', class_='featured-characters')
        for section in char_sections:
            # Verificar si es 5★ o 4★ por el texto anterior
            prev_p = section.find_previous('p', class_='featured')
            is_five_star = prev_p and '5★' in prev_p.text if prev_p else False
            
            cards = section.find_all('div', class_='avatar-card')
            for card in cards:
                char_data = self.parse_character(card)
                if char_data:
                    if is_five_star or char_data['rarity'] == 5:
                        featured_5star_char.append(char_data)
                    else:
                        featured_4star_char.append(char_data)
        
        return featured_5star_char, featured_4star_char
    
    def extract_light_cones(self, item):
        """Extrae conos 5★ y 4★ de un banner"""
        featured_5star_cone = []
        featured_4star_cone = []
        
        cone_sections = item.find_all('div', class_='featured-cone')
        for section in cone_sections:
            # Verificar si es 5★ o 4★
            prev_p = section.find_previous('p', class_='featured')
            is_five_star = prev_p and '5★' in prev_p.text if prev_p else False
            
            cone_items = section.find_all('div', class_='accordion-item')
            for cone in cone_items:
                cone_data = self.parse_light_cone(cone)
                if cone_data:
                    if is_five_star or cone_data['rarity'] == 5:
                        featured_5star_cone.append(cone_data)
                    else:
                        featured_4star_cone.append(cone_data)
        
        return featured_5star_cone, featured_4star_cone
    
    def get_banners(self):
        """Obtiene TODOS los banners de warps (actuales y futuros)"""
        try:
            logger.info(f"Obteniendo banners desde {self.url}")
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar TODOS los accordion-item
            all_items = soup.find_all('div', class_='accordion-item')
            logger.info(f"Total accordion-items encontrados: {len(all_items)}")
            
            banners = []
            
            for item in all_items:
                # Verificar si es un WARP
                if not self.is_warp_banner(item):
                    continue
                
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
                    
                    # Clasificar por tipo
                    banner_type = self.classify_banner_type(item)
                    
                    # Extraer personajes y conos
                    featured_5star_char, featured_4star_char = self.extract_characters(item)
                    featured_5star_cone, featured_4star_cone = self.extract_light_cones(item)
                    
                    # Solo crear banner si tiene contenido
                    if (featured_5star_char or featured_4star_char or 
                        featured_5star_cone or featured_4star_cone):
                        
                        banner = Banner(
                            name=banner_name,
                            banner_type=banner_type,
                            time_remaining=time_remaining,
                            featured_5star_char=featured_5star_char,
                            featured_4star_char=featured_4star_char,
                            featured_5star_cone=featured_5star_cone,
                            featured_4star_cone=featured_4star_cone,
                            duration_text=duration_text
                        )
                        banners.append(banner)
                        logger.info(f"✅ Banner encontrado: {banner_name}")
                        logger.info(f"   - Tipo: {banner_type}")
                        logger.info(f"   - Personajes 5★: {len(featured_5star_char)}")
                        logger.info(f"   - Personajes 4★: {len(featured_4star_char)}")
                        logger.info(f"   - Conos 5★: {len(featured_5star_cone)}")
                        logger.info(f"   - Conos 4★: {len(featured_4star_cone)}")
                    
                except Exception as e:
                    logger.error(f"Error procesando banner: {e}")
                    continue
            
            logger.info(f"✅ TOTAL WARPS ENCONTRADOS: {len(banners)}")
            return banners
            
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return []

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
    """Crea un embed para un banner con manejo seguro de URLs"""
    
    # Color según tipo
    if banner.banner_type == "Personaje":
        color = discord.Color.from_rgb(255, 215, 0)  # Dorado
        emoji = "🦸"
    elif banner.banner_type == "Cono de Luz":
        color = discord.Color.from_rgb(147, 112, 219)  # Púrpura
        emoji = "⚔️"
    else:
        color = discord.Color.from_rgb(52, 152, 219)  # Azul
        emoji = "🎁"
    
    embed = discord.Embed(
        title=f"{emoji} {banner.name}",
        description=f"**Tipo:** {banner.banner_type}\n**⏳ Tiempo restante:** {banner.time_remaining}",
        color=color,
        timestamp=datetime.now()
    )
    
    # Duración del evento
    if banner.duration_text:
        clean_duration = banner.duration_text.replace('Event Duration', '📅 Duración')
        if len(clean_duration) > 1024:
            clean_duration = clean_duration[:1021] + "..."
        embed.add_field(name="📅 Duración", value=clean_duration, inline=False)
    
    # Personajes 5★
    if banner.featured_5star_char:
        chars_text = ""
        for char in banner.featured_5star_char[:6]:
            element_emoji = get_element_emoji(char.get('element', 'Unknown'))
            chars_text += f"{element_emoji} **{char['name']}**\n"
        
        if chars_text:
            embed.add_field(name="✨ Personajes 5★", value=chars_text, inline=True)
    
    # Personajes 4★
    if banner.featured_4star_char:
        chars_text = ""
        for char in banner.featured_4star_char[:6]:
            element_emoji = get_element_emoji(char.get('element', 'Unknown'))
            chars_text += f"{element_emoji} **{char['name']}**\n"
        
        if chars_text:
            embed.add_field(name="⭐ Personajes 4★", value=chars_text, inline=True)
    
    # Conos de luz 5★
    if banner.featured_5star_cone:
        cones_text = ""
        for cone in banner.featured_5star_cone[:4]:
            cones_text += f"• **{cone['name']}** (★5)\n"
        
        if cones_text:
            embed.add_field(name="💫 Conos de Luz 5★", value=cones_text, inline=False)
    
    # Conos de luz 4★
    if banner.featured_4star_cone:
        cones_text = ""
        for cone in banner.featured_4star_cone[:4]:
            cones_text += f"• **{cone['name']}** (★4)\n"
        
        if cones_text:
            embed.add_field(name="📿 Conos de Luz 4★", value=cones_text, inline=False)
    
    # THUMBNAIL CON VALIDACIÓN ESTRICTA
    thumbnail_url = None
    
    # Buscar una imagen válida en orden de prioridad
    if banner.featured_5star_char and len(banner.featured_5star_char) > 0:
        for char in banner.featured_5star_char:
            if char.get('image') and char['image'].startswith(('http://', 'https://')):
                thumbnail_url = char['image']
                break
    
    if not thumbnail_url and banner.featured_5star_cone and len(banner.featured_5star_cone) > 0:
        for cone in banner.featured_5star_cone:
            if cone.get('image') and cone['image'].startswith(('http://', 'https://')):
                thumbnail_url = cone['image']
                break
    
    if not thumbnail_url and banner.featured_4star_char and len(banner.featured_4star_char) > 0:
        for char in banner.featured_4star_char:
            if char.get('image') and char['image'].startswith(('http://', 'https://')):
                thumbnail_url = char['image']
                break
    
    if not thumbnail_url and banner.featured_4star_cone and len(banner.featured_4star_cone) > 0:
        for cone in banner.featured_4star_cone:
            if cone.get('image') and cone['image'].startswith(('http://', 'https://')):
                thumbnail_url = cone['image']
                break
    
    # Si no hay ninguna imagen válida, usar la imagen por defecto
    if not thumbnail_url:
        thumbnail_url = "https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png"
    
    # Establecer thumbnail
    try:
        embed.set_thumbnail(url=thumbnail_url)
    except Exception as e:
        logger.error(f"Error estableciendo thumbnail: {e}")
        # Si falla, intentar con la imagen por defecto
        embed.set_thumbnail(url="https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png")
    
    # Footer con totales
    total_5star = len(banner.featured_5star_char) + len(banner.featured_5star_cone)
    total_4star = len(banner.featured_4star_char) + len(banner.featured_4star_cone)
    embed.set_footer(text=f"✨ {total_5star} ★5  |  ⭐ {total_4star} ★4  •  Datos de Prydwen.gg")
    
    return embed

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 60)
logger.info("INICIANDO BOT DE HONKAI STAR RAIL - DETECTOR DE MÚLTIPLES BANNERS")
logger.info("=" * 60)

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
            name="todos los banners de HSR | !banners"
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
    
    loading_msg = await channel.send("🔍 Escaneando TODOS los banners de Honkai: Star Rail en Prydwen.gg...")
    
    try:
        banners = scraper.get_banners()
        
        if not banners:
            await loading_msg.edit(content="❌ No se encontraron banners. La estructura de la web puede haber cambiado.")
            return
        
        await loading_msg.delete()
        
        # Enviar cada banner
        banners_enviados = 0
        for banner in banners:
            try:
                embed = create_banner_embed(banner)
                await channel.send(embed=embed)
                banners_enviados += 1
                await asyncio.sleep(1.5)  # Pausa para evitar rate limits
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
            for char in b.featured_5star_char + b.featured_4star_char:
                if banner_name.lower() in char.get('name', '').lower():
                    found_banners.append(b)
                    break
    
    # Buscar por cono
    if not found_banners:
        for b in banners:
            for cone in b.featured_5star_cone + b.featured_4star_cone:
                if banner_name.lower() in cone.get('name', '').lower():
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
    await ctx.send("🔄 Forzando actualización de banners...")
    await send_banners(ctx.channel)

@bot.command(name='stats')
async def banner_stats(ctx):
    """Muestra estadísticas de los banners"""
    banners = scraper.get_banners()
    
    total_banners = len(banners)
    total_5star_chars = sum(len(b.featured_5star_char) for b in banners)
    total_4star_chars = sum(len(b.featured_4star_char) for b in banners)
    total_5star_cones = sum(len(b.featured_5star_cone) for b in banners)
    total_4star_cones = sum(len(b.featured_4star_cone) for b in banners)
    
    embed = discord.Embed(
        title="📊 Estadísticas de Banners HSR",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🎯 Banners activos", value=str(total_banners), inline=True)
    embed.add_field(name="✨ Personajes 5★", value=str(total_5star_chars), inline=True)
    embed.add_field(name="⭐ Personajes 4★", value=str(total_4star_chars), inline=True)
    embed.add_field(name="💫 Conos 5★", value=str(total_5star_cones), inline=True)
    embed.add_field(name="📿 Conos 4★", value=str(total_4star_cones), inline=True)
    
    await ctx.send(embed=embed)

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

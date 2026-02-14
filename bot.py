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
from dateutil import parser
from dateutil.relativedelta import relativedelta
import json

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
                 duration_text: str = "", start_date=None, end_date=None,
                 banner_id: str = ""):
        self.name = name
        self.banner_type = banner_type
        self.time_remaining = time_remaining
        self.featured_5star_char = featured_5star_char if featured_5star_char else []
        self.featured_4star_char = featured_4star_char if featured_4star_char else []
        self.featured_5star_cone = featured_5star_cone if featured_5star_cone else []
        self.featured_4star_cone = featured_4star_cone if featured_4star_cone else []
        self.duration_text = duration_text
        self.start_date = start_date
        self.end_date = end_date
        self.banner_id = banner_id

# ============================================
# CLASE PARA GESTIONAR MENSAJES
# ============================================
class MessageManager:
    """Gestiona los mensajes del bot para editarlos en lugar de crear nuevos"""
    
    def __init__(self):
        self.message_file = "banner_messages.json"
        self.messages = self.load_messages()
    
    def load_messages(self):
        """Carga los mensajes guardados"""
        try:
            if os.path.exists(self.message_file):
                with open(self.message_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando mensajes: {e}")
        return {}
    
    def save_messages(self):
        """Guarda los mensajes"""
        try:
            with open(self.message_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando mensajes: {e}")
    
    def get_message_id(self, channel_id, banner_name):
        """Obtiene el ID del mensaje para un banner específico"""
        key = f"{channel_id}_{banner_name}"
        return self.messages.get(key)
    
    def set_message_id(self, channel_id, banner_name, message_id):
        """Guarda el ID del mensaje para un banner específico"""
        key = f"{channel_id}_{banner_name}"
        self.messages[key] = message_id
        self.save_messages()
    
    def clear_channel(self, channel_id):
        """Limpia todos los mensajes de un canal"""
        keys_to_delete = [k for k in self.messages.keys() if k.startswith(f"{channel_id}_")]
        for key in keys_to_delete:
            del self.messages[key]
        self.save_messages()

# ============================================
# CLASE BANNER SCRAPER
# ============================================
class BannerScraper:
    """Clase para hacer scraping de los banners de warps en Prydwen"""
    
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
        
        # Mapeo de elementos a emojis
        self.element_emojis = {
            'Physical': '💪', 'Fire': '🔥', 'Ice': '❄️',
            'Lightning': '⚡', 'Wind': '💨', 'Quantum': '⚛️',
            'Imaginary': '✨'
        }
    
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
    
    def parse_date_from_duration(self, duration_text):
        """Parsea las fechas de inicio y fin del texto de duración"""
        if not duration_text:
            return None, None
        
        # Buscar patrones de fecha comunes
        # Formato: "2026/01/25 04:00 - 2026/02/16 03:59"
        # o "After 4.0 patch goes live — 2026/03/03 15:00"
        
        start_date = None
        end_date = None
        
        # Patrón para fechas con formato YYYY/MM/DD
        date_pattern = r'(\d{4}/\d{2}/\d{2}(?:\s+\d{2}:\d{2})?)'
        dates = re.findall(date_pattern, duration_text)
        
        if len(dates) >= 2:
            # Tiene fecha de inicio y fin
            try:
                start_date = parser.parse(dates[0], fuzzy=True)
                end_date = parser.parse(dates[1], fuzzy=True)
            except:
                pass
        elif len(dates) == 1:
            # Puede ser solo fecha de fin (banner que ya empezó)
            try:
                end_date = parser.parse(dates[0], fuzzy=True)
                # Asumimos que empezó hace algún tiempo
                start_date = datetime.now() - relativedelta(days=20)
            except:
                pass
        
        return start_date, end_date
    
    def is_warp_banner(self, item) -> bool:
        """Determina si un accordion-item es un WARP real basado en su estructura interna"""
        html = str(item)
        
        # Características que definen un WARP:
        # 1. Tiene párrafos con clase 'featured'
        # 2. Tiene spans con clase 'hsr-rar' que contienen '5★' o '4★'
        # 3. Tiene secciones 'featured-characters' o 'featured-cone'
        # 4. Tiene avatar-cards o hsr-set-image (contenido real)
        
        has_featured_p = 'class="featured"' in html
        has_rarity_spans = 'hsr-rar' in html and ('5★' in html or '4★' in html)
        has_featured_chars = 'featured-characters' in html
        has_featured_cones = 'featured-cone' in html
        has_avatar_cards = 'avatar-card' in html
        has_cone_images = 'hsr-set-image' in html
        
        # También debe tener elementos básicos
        has_event_name = 'event-name' in html
        has_duration = 'Event Duration' in html
        
        # Un warp SIEMPRE tiene rarezas Y contenido destacado
        is_warp = (has_featured_p or has_rarity_spans) and (has_featured_chars or has_featured_cones or has_avatar_cards or has_cone_images)
        
        # Los eventos de juego NO tienen featured
        is_game_event = 'Memory Turbulence' in html or 'Description:' in html
        
        return is_warp and not is_game_event and has_event_name and has_duration
    
    def parse_character(self, card) -> dict:
        """Parsea un personaje de avatar-card y extrae su imagen"""
        try:
            a_tag = card.find('a')
            name = "Unknown"
            char_key = ""
            
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                char_key = href.split('/')[-1]
                name = char_key.replace('-', ' ').title()
            
            # Imagen - prioridad a la extraída del HTML
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
            
            # Si no hay imagen, usar imagen por defecto
            if not image_url:
                image_url = self.default_image
            
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
        """Parsea un cono de luz y extrae su imagen"""
        try:
            name_tag = cone_item.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            img_tag = cone_item.find('img')
            image_url = self.extract_image_url(img_tag)
            
            cone_html = str(cone_item)
            rarity = 5 if 'rarity-5' in cone_html or 'rar-5' in cone_html else 4
            
            # Si no hay imagen, usar imagen por defecto
            if not image_url:
                image_url = self.default_image
            
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
    
    def classify_banner_type(self, item, chars5, chars4, cones5, cones4) -> str:
        """Clasifica el tipo de banner basado en lo que contiene"""
        has_chars = len(chars5) + len(chars4) > 0
        has_cones = len(cones5) + len(cones4) > 0
        
        if has_chars and not has_cones:
            return "Personaje"
        elif has_cones and not has_chars:
            return "Cono de Luz"
        elif has_chars and has_cones:
            return "Mixto (Doble)"
        else:
            return "Mixto"
    
    def get_banners(self):
        """Obtiene SOLO los banners de warps reales"""
        try:
            logger.info(f"Obteniendo banners desde {self.url}")
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar TODOS los accordion-item
            all_items = soup.find_all('div', class_='accordion-item')
            logger.info(f"Total accordion-items encontrados: {len(all_items)}")
            
            banners = []
            warp_count = 0
            skipped_count = 0
            
            for item in all_items:
                # Verificar si es un WARP por su estructura interna
                if not self.is_warp_banner(item):
                    skipped_count += 1
                    continue
                
                try:
                    # Nombre del banner (usado como ID único)
                    name_tag = item.find('div', class_='event-name')
                    banner_name = name_tag.text.strip() if name_tag else "Banner sin nombre"
                    
                    # Crear un ID único para el banner (nombre normalizado)
                    banner_id = re.sub(r'[^a-zA-Z0-9]', '', banner_name.lower())
                    
                    # Tiempo restante
                    time_tag = item.find('span', class_='time')
                    time_remaining = time_tag.text.strip() if time_tag else "Tiempo desconocido"
                    
                    # Duración
                    duration_tag = item.find('p', class_='duration')
                    duration_text = duration_tag.text.strip() if duration_tag else ""
                    
                    # Extraer fechas
                    start_date, end_date = self.parse_date_from_duration(duration_text)
                    
                    # Extraer personajes y conos
                    featured_5star_char, featured_4star_char = self.extract_characters(item)
                    featured_5star_cone, featured_4star_cone = self.extract_light_cones(item)
                    
                    # Determinar tipo
                    banner_type = self.classify_banner_type(item, featured_5star_char, featured_4star_char, 
                                                            featured_5star_cone, featured_4star_cone)
                    
                    warp_count += 1
                    
                    banner = Banner(
                        name=banner_name,
                        banner_type=banner_type,
                        time_remaining=time_remaining,
                        featured_5star_char=featured_5star_char,
                        featured_4star_char=featured_4star_char,
                        featured_5star_cone=featured_5star_cone,
                        featured_4star_cone=featured_4star_cone,
                        duration_text=duration_text,
                        start_date=start_date,
                        end_date=end_date,
                        banner_id=banner_id
                    )
                    banners.append(banner)
                    
                    # Log detallado
                    logger.info(f"✅ Warp {warp_count}: {banner_name}")
                    logger.info(f"   - ID: {banner_id}")
                    logger.info(f"   - Tipo: {banner_type}")
                    logger.info(f"   - Inicio: {start_date}")
                    logger.info(f"   - Fin: {end_date}")
                    logger.info(f"   - Personajes 5★: {len(featured_5star_char)}")
                    logger.info(f"   - Personajes 4★: {len(featured_4star_char)}")
                    logger.info(f"   - Conos 5★: {len(featured_5star_cone)}")
                    logger.info(f"   - Conos 4★: {len(featured_4star_cone)}")
                    
                except Exception as e:
                    logger.error(f"Error procesando banner: {e}")
                    continue
            
            logger.info(f"✅ WARPS REALES ENCONTRADOS: {len(banners)}")
            logger.info(f"📊 Items que no son warps: {skipped_count}")
            return banners
            
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return []

# ============================================
# INSTANCIAS GLOBALES
# ============================================
scraper = BannerScraper()
message_manager = MessageManager()

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

def create_banner_embed(banner: Banner, status: str = "actual") -> discord.Embed:
    """Crea un embed precioso para un banner con TODAS las imágenes posibles"""
    
    # Emoji según el tipo y estado
    type_emoji = {
        "Personaje": "🦸",
        "Cono de Luz": "⚔️",
        "Mixto (Doble)": "🎁"
    }.get(banner.banner_type, "🎯")
    
    # Color según el tipo y estado
    if status == "proximo":
        color = discord.Color.from_rgb(100, 100, 100)  # Gris para próximos
    elif banner.banner_type == "Personaje":
        color = discord.Color.from_rgb(255, 215, 0)  # Dorado
    elif banner.banner_type == "Cono de Luz":
        color = discord.Color.from_rgb(147, 112, 219)  # Púrpura
    else:
        color = discord.Color.from_rgb(52, 152, 219)  # Azul
    
    # Título con emoji y estado
    status_emoji = "🔴" if status == "actual" else "🟡"
    title = f"{status_emoji} {type_emoji} {banner.name}"
    
    embed = discord.Embed(
        title=title,
        description=f"**Tipo:** {banner.banner_type}\n**⏳ Tiempo restante:** {banner.time_remaining}",
        color=color,
        timestamp=datetime.now()
    )
    
    # Duración del evento (formateada bonito)
    if banner.duration_text:
        clean_duration = banner.duration_text.replace('Event Duration', '📅 **Duración**')
        clean_duration = clean_duration.replace('server time', 'hora del servidor')
        if len(clean_duration) > 1024:
            clean_duration = clean_duration[:1021] + "..."
        embed.add_field(name="📅 Duración", value=clean_duration, inline=False)
    
    # Fechas si están disponibles
    if banner.start_date and banner.end_date:
        fecha_text = f"Inicio: {banner.start_date.strftime('%d/%m/%Y %H:%M')}\nFin: {banner.end_date.strftime('%d/%m/%Y %H:%M')}"
        embed.add_field(name="📆 Fechas", value=fecha_text, inline=False)
    
    # Personajes 5★ (con emojis de elemento)
    if banner.featured_5star_char:
        chars_text = ""
        for char in banner.featured_5star_char:
            element_emoji = get_element_emoji(char.get('element', 'Unknown'))
            chars_text += f"{element_emoji} **{char['name']}**\n"
        
        if chars_text:
            embed.add_field(name="✨ **Personajes 5★**", value=chars_text, inline=True)
    
    # Personajes 4★
    if banner.featured_4star_char:
        chars_text = ""
        for char in banner.featured_4star_char:
            element_emoji = get_element_emoji(char.get('element', 'Unknown'))
            chars_text += f"{element_emoji} **{char['name']}**\n"
        
        if chars_text:
            embed.add_field(name="⭐ **Personajes 4★**", value=chars_text, inline=True)
    
    # Conos de luz 5★
    if banner.featured_5star_cone:
        cones_text = ""
        for cone in banner.featured_5star_cone:
            cones_text += f"💫 **{cone['name']}** (★5)\n"
        
        if cones_text:
            embed.add_field(name="💫 **Conos de Luz 5★**", value=cones_text, inline=False)
    
    # Conos de luz 4★
    if banner.featured_4star_cone:
        cones_text = ""
        for cone in banner.featured_4star_cone:
            cones_text += f"📿 **{cone['name']}** (★4)\n"
        
        if cones_text:
            embed.add_field(name="📿 **Conos de Luz 4★**", value=cones_text, inline=False)
    
    # IMÁGENES - Añadir todas las imágenes disponibles
    image_urls = []
    
    # Recopilar todas las URLs de imágenes
    for char in banner.featured_5star_char:
        if char.get('image') and char['image'] not in image_urls:
            image_urls.append(char['image'])
    
    for char in banner.featured_4star_char:
        if char.get('image') and char['image'] not in image_urls:
            image_urls.append(char['image'])
    
    for cone in banner.featured_5star_cone:
        if cone.get('image') and cone['image'] not in image_urls:
            image_urls.append(cone['image'])
    
    for cone in banner.featured_4star_cone:
        if cone.get('image') and cone['image'] not in image_urls:
            image_urls.append(cone['image'])
    
    # Si hay imágenes, mostrar la primera como thumbnail y las siguientes como imágenes
    if image_urls:
        # Primera imagen como thumbnail
        try:
            embed.set_thumbnail(url=image_urls[0])
        except Exception as e:
            logger.error(f"Error estableciendo thumbnail: {e}")
        
        # Si hay más imágenes, añadirlas como fields
        if len(image_urls) > 1:
            for i, img_url in enumerate(image_urls[1:4]):  # Máximo 3 imágenes adicionales
                try:
                    embed.add_field(name="🖼️" if i == 0 else "​", value=f"[Ver imagen]({img_url})", inline=True)
                except:
                    pass
    
    # Si no hay imágenes, usar imagen por defecto
    if not image_urls:
        embed.set_thumbnail(url="https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png")
    
    # Footer con estadísticas
    total_5star = len(banner.featured_5star_char) + len(banner.featured_5star_cone)
    total_4star = len(banner.featured_4star_char) + len(banner.featured_4star_cone)
    
    footer_text = f"✨ {total_5star} ★5  |  ⭐ {total_4star} ★4  •  {status.capitalize()} • Datos de Prydwen.gg"
    embed.set_footer(text=footer_text)
    
    return embed

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 60)
logger.info("🚀 INICIANDO BOT DE HONKAI STAR RAIL - EDITOR DE MENSAJES")
logger.info("=" * 60)

TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_ACTUAL = os.environ.get('DISCORD_CHANNEL_ACTUAL')
CHANNEL_ID_PROXIMO = os.environ.get('DISCORD_CHANNEL_PROXIMO')

logger.info(f"🔑 DISCORD_TOKEN: {'✅ ENCONTRADO' if TOKEN else '❌ NO ENCONTRADO'}")
logger.info(f"📢 Canal ACTUAL: {'✅ ' + CHANNEL_ID_ACTUAL if CHANNEL_ID_ACTUAL else '❌ NO CONFIGURADO'}")
logger.info(f"📢 Canal PRÓXIMO: {'✅ ' + CHANNEL_ID_PROXIMO if CHANNEL_ID_PROXIMO else '❌ NO CONFIGURADO'}")

TARGET_CHANNEL_ACTUAL = None
if CHANNEL_ID_ACTUAL:
    try:
        TARGET_CHANNEL_ACTUAL = int(CHANNEL_ID_ACTUAL.strip())
        logger.info(f"✅ Canal actual: {TARGET_CHANNEL_ACTUAL}")
    except ValueError:
        logger.error(f"❌ DISCORD_CHANNEL_ACTUAL no es válido: {CHANNEL_ID_ACTUAL}")

TARGET_CHANNEL_PROXIMO = None
if CHANNEL_ID_PROXIMO:
    try:
        TARGET_CHANNEL_PROXIMO = int(CHANNEL_ID_PROXIMO.strip())
        logger.info(f"✅ Canal próximo: {TARGET_CHANNEL_PROXIMO}")
    except ValueError:
        logger.error(f"❌ DISCORD_CHANNEL_PROXIMO no es válido: {CHANNEL_ID_PROXIMO}")

if not TOKEN:
    logger.error("❌ ERROR CRÍTICO: No hay token de Discord")
    sys.exit(1)

if not TARGET_CHANNEL_ACTUAL and not TARGET_CHANNEL_PROXIMO:
    logger.warning("⚠️ No hay canales configurados. Los banners solo se podrán ver con comandos.")

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
            name="🔮 Warps de HSR | !banners"
        )
    )
    
    # Iniciar tarea diaria si hay al menos un canal configurado
    if TARGET_CHANNEL_ACTUAL or TARGET_CHANNEL_PROXIMO:
        daily_banners.start()
        logger.info(f"📅 Tarea diaria iniciada")

@tasks.loop(hours=24)
async def daily_banners():
    """Actualiza los banners cada 24 horas (editando mensajes existentes)"""
    await update_banners()

@daily_banners.before_loop
async def before_daily_banners():
    """Espera a que el bot esté listo"""
    await bot.wait_until_ready()

async def update_banners():
    """Actualiza los banners en los canales (editando en lugar de crear nuevos)"""
    
    # Obtener todos los banners
    all_banners = scraper.get_banners()
    
    if not all_banners:
        logger.warning("No se encontraron banners para actualizar")
        return
    
    # Clasificar banners por fecha
    now = datetime.now()
    banners_actuales = []
    banners_proximos = []
    
    for banner in all_banners:
        if banner.end_date and banner.end_date > now:
            if banner.start_date and banner.start_date <= now:
                banners_actuales.append(banner)
            elif banner.start_date and banner.start_date > now:
                banners_proximos.append(banner)
            else:
                # Si no tenemos fecha de inicio, asumimos que es actual
                banners_actuales.append(banner)
    
    logger.info(f"Clasificación: {len(banners_actuales)} actuales, {len(banners_proximos)} próximos")
    
    # Actualizar canal de actuales
    if TARGET_CHANNEL_ACTUAL:
        await update_channel_banners(TARGET_CHANNEL_ACTUAL, banners_actuales, "actual")
    
    # Actualizar canal de próximos
    if TARGET_CHANNEL_PROXIMO:
        await update_channel_banners(TARGET_CHANNEL_PROXIMO, banners_proximos, "proximo")

async def update_channel_banners(channel_id, banners, status):
    """Actualiza los banners de un canal específico (editando mensajes)"""
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"❌ No se encontró el canal {channel_id}")
        return
    
    try:
        # Enviar mensaje de carga
        loading_msg = await channel.send(f"🔄 **Actualizando warps {status}es...**")
        
        # Obtener mensajes existentes en el canal
        existing_messages = []
        async for message in channel.history(limit=50):
            if message.author == bot.user and message.embeds:
                existing_messages.append(message)
        
        logger.info(f"Canal {channel.name}: {len(existing_messages)} mensajes existentes")
        
        # Mapear mensajes existentes por ID de banner
        existing_by_id = {}
        for msg in existing_messages:
            if msg.embeds and msg.embeds[0].title:
                # Intentar extraer ID del banner del título o footer
                for banner in banners:
                    if banner.name in msg.embeds[0].title:
                        existing_by_id[banner.banner_id] = msg
                        break
        
        # Actualizar o crear mensajes para cada banner
        for banner in banners:
            embed = create_banner_embed(banner, status)
            
            if banner.banner_id in existing_by_id:
                # Editar mensaje existente
                msg = existing_by_id[banner.banner_id]
                try:
                    await msg.edit(embed=embed)
                    logger.info(f"✅ Mensaje editado: {banner.name}")
                except Exception as e:
                    logger.error(f"Error editando mensaje {banner.name}: {e}")
            else:
                # Crear nuevo mensaje
                try:
                    new_msg = await channel.send(embed=embed)
                    message_manager.set_message_id(channel_id, banner.banner_id, new_msg.id)
                    logger.info(f"✅ Mensaje creado: {banner.name}")
                except Exception as e:
                    logger.error(f"Error creando mensaje {banner.name}: {e}")
            
            await asyncio.sleep(1)  # Pausa para evitar rate limits
        
        # Eliminar mensajes de banners que ya no existen
        current_ids = {b.banner_id for b in banners}
        for msg in existing_messages:
            msg_id = None
            for banner_id, existing_msg in existing_by_id.items():
                if existing_msg.id == msg.id and banner_id not in current_ids:
                    try:
                        await msg.delete()
                        logger.info(f"🗑️ Mensaje eliminado (banner ya no existe)")
                    except Exception as e:
                        logger.error(f"Error eliminando mensaje: {e}")
                    break
        
        # Limpiar mensaje de carga
        await loading_msg.delete()
        
        # Mensaje de resumen
        await channel.send(f"✅ **{len(banners)} warps {status}es actualizados.**")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando canal {channel.name}: {e}")

@bot.command(name='banners', aliases=['warps', 'warp'])
async def banners_command(ctx):
    """Comando para mostrar todos los warps (actuales y próximos)"""
    
    loading_msg = await ctx.send("🔮 **Escaneando warps...**")
    
    try:
        all_banners = scraper.get_banners()
        
        if not all_banners:
            await loading_msg.edit(content="❌ **No se encontraron warps.**")
            return
        
        # Clasificar
        now = datetime.now()
        banners_actuales = []
        banners_proximos = []
        
        for banner in all_banners:
            if banner.end_date and banner.end_date > now:
                if banner.start_date and banner.start_date <= now:
                    banners_actuales.append(banner)
                elif banner.start_date and banner.start_date > now:
                    banners_proximos.append(banner)
                else:
                    banners_actuales.append(banner)
        
        await loading_msg.delete()
        
        # Enviar actuales
        if banners_actuales:
            await ctx.send("🔴 **WARPS ACTIVOS ACTUALMENTE**")
            for banner in banners_actuales:
                embed = create_banner_embed(banner, "actual")
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
        
        # Enviar próximos
        if banners_proximos:
            await ctx.send("🟡 **PRÓXIMOS WARPS**")
            for banner in banners_proximos:
                embed = create_banner_embed(banner, "proximo")
                await ctx.send(embed=embed)
                await asyncio.sleep(1)
        
        # Resumen
        await ctx.send(f"📊 **Resumen:** {len(banners_actuales)} actuales, {len(banners_proximos)} próximos")
        
    except Exception as e:
        logger.error(f"Error en comando banners: {e}")
        await loading_msg.edit(content=f"❌ **Error:** {str(e)[:200]}")

@bot.command(name='banner', aliases=['warpinfo'])
async def banner_info(ctx, *, banner_name: str = None):
    """Muestra información de un warp específico"""
    if not banner_name:
        await ctx.send("❌ **Usa:** `!banner nombre_del_warp`\nPor ejemplo: `!banner Deadly Dancer`")
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
        await ctx.send(f"❌ **No se encontró '{banner_name}'**")
        return
    
    for banner in found_banners[:2]:  # Máximo 2 banners
        # Determinar si es actual o próximo
        now = datetime.now()
        status = "proximo" if (banner.start_date and banner.start_date > now) else "actual"
        embed = create_banner_embed(banner, status)
        await ctx.send(embed=embed)

@bot.command(name='refresh')
@commands.has_permissions(administrator=True)
async def refresh_banners(ctx):
    """Fuerza actualización (solo admins)"""
    await ctx.send("🔄 **Forzando actualización de warps...**")
    await update_banners()

@bot.command(name='reset_channel')
@commands.has_permissions(administrator=True)
async def reset_channel(ctx, channel_type: str = None):
    """Resetea los mensajes de un canal (solo admins)"""
    if not channel_type or channel_type not in ['actual', 'proximo']:
        await ctx.send("❌ **Usa:** `!reset_channel actual` o `!reset_channel proximo`")
        return
    
    channel_id = TARGET_CHANNEL_ACTUAL if channel_type == 'actual' else TARGET_CHANNEL_PROXIMO
    if not channel_id:
        await ctx.send(f"❌ **Canal {channel_type} no configurado**")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send(f"❌ **No se encontró el canal**")
        return
    
    # Limpiar mensajes del canal
    async for message in channel.history(limit=100):
        if message.author == bot.user:
            try:
                await message.delete()
                await asyncio.sleep(0.5)
            except:
                pass
    
    # Limpiar registro de mensajes
    message_manager.clear_channel(channel_id)
    
    await ctx.send(f"✅ **Canal {channel_type} reseteado. Los mensajes se recrearán en la próxima actualización.**")

@bot.command(name='stats')
async def banner_stats(ctx):
    """Muestra estadísticas de los warps"""
    banners = scraper.get_banners()
    
    # Clasificar
    now = datetime.now()
    banners_actuales = []
    banners_proximos = []
    
    for banner in banners:
        if banner.end_date and banner.end_date > now:
            if banner.start_date and banner.start_date <= now:
                banners_actuales.append(banner)
            elif banner.start_date and banner.start_date > now:
                banners_proximos.append(banner)
            else:
                banners_actuales.append(banner)
    
    total_5star_chars = sum(len(b.featured_5star_char) for b in banners)
    total_4star_chars = sum(len(b.featured_4star_char) for b in banners)
    total_5star_cones = sum(len(b.featured_5star_cone) for b in banners)
    total_4star_cones = sum(len(b.featured_4star_cone) for b in banners)
    
    embed = discord.Embed(
        title="📊 **Estadísticas de Warps HSR**",
        description="Resumen de los warps actualmente disponibles",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🔴 Actuales", value=str(len(banners_actuales)), inline=True)
    embed.add_field(name="🟡 Próximos", value=str(len(banners_proximos)), inline=True)
    embed.add_field(name="🎯 Total", value=str(len(banners)), inline=True)
    embed.add_field(name="✨ Personajes 5★", value=str(total_5star_chars), inline=True)
    embed.add_field(name="⭐ Personajes 4★", value=str(total_4star_chars), inline=True)
    embed.add_field(name="💫 Conos 5★", value=str(total_5star_cones), inline=True)
    embed.add_field(name="📿 Conos 4★", value=str(total_4star_cones), inline=True)
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Comando no encontrado.** Usa `!banners` para ver los warps.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ **No tienes permiso para usar este comando.**")
    elif isinstance(error, discord.Forbidden):
        logger.error(f"Error de permisos: {error}")
        try:
            await ctx.send("❌ **El bot no tiene permisos suficientes en este canal.** Por favor, verifica que tenga permisos de 'Enviar mensajes' y 'Insertar enlaces'.")
        except:
            logger.error("No se pudo enviar mensaje de error por falta de permisos")
    else:
        logger.error(f"Error en comando: {error}")
        try:
            await ctx.send(f"❌ **Error:** {str(error)[:100]}")
        except:
            pass

# ============================================
# INICIAR BOT
# ============================================
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"❌ Error iniciando bot: {e}")
        sys.exit(1)

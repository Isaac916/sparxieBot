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
                 banner_id: str = "", characters_data: list = None, cones_data: list = None):
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
        self.characters_data = characters_data if characters_data else []
        self.cones_data = cones_data if cones_data else []

# ============================================
# CLASE PARA GESTIONAR HILOS
# ============================================
class ThreadManager:
    """Gestiona los hilos (threads) del bot"""
    
    def __init__(self):
        self.thread_file = "banner_threads.json"
        self.threads = self.load_threads()
    
    def load_threads(self):
        """Carga los hilos guardados"""
        try:
            if os.path.exists(self.thread_file):
                with open(self.thread_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando hilos: {e}")
        return {}
    
    def save_threads(self):
        """Guarda los hilos"""
        try:
            with open(self.thread_file, 'w', encoding='utf-8') as f:
                json.dump(self.threads, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando hilos: {e}")
    
    def get_thread_id(self, channel_id, banner_id):
        """Obtiene el ID del hilo para un banner específico"""
        key = f"{channel_id}_{banner_id}"
        return self.threads.get(key)
    
    def set_thread_id(self, channel_id, banner_id, thread_id, message_id):
        """Guarda el ID del hilo para un banner específico"""
        key = f"{channel_id}_{banner_id}"
        self.threads[key] = {
            "thread_id": thread_id,
            "message_id": message_id,
            "last_updated": datetime.now().isoformat()
        }
        self.save_threads()
    
    def remove_thread(self, channel_id, banner_id):
        """Elimina un hilo del registro"""
        key = f"{channel_id}_{banner_id}"
        if key in self.threads:
            del self.threads[key]
            self.save_threads()
    
    def clear_channel(self, channel_id):
        """Limpia todos los hilos de un canal"""
        keys_to_delete = [k for k in self.threads.keys() if k.startswith(f"{channel_id}_")]
        for key in keys_to_delete:
            del self.threads[key]
        self.save_threads()

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
        
        start_date = None
        end_date = None
        
        # Patrón para fechas con formato YYYY/MM/DD
        date_pattern = r'(\d{4}/\d{2}/\d{2}(?:\s+\d{2}:\d{2})?)'
        dates = re.findall(date_pattern, duration_text)
        
        if len(dates) >= 2:
            try:
                start_date = parser.parse(dates[0], fuzzy=True)
                end_date = parser.parse(dates[1], fuzzy=True)
            except:
                pass
        elif len(dates) == 1:
            try:
                end_date = parser.parse(dates[0], fuzzy=True)
                start_date = datetime.now() - relativedelta(days=20)
            except:
                pass
        
        return start_date, end_date
    
    def is_warp_banner(self, item) -> bool:
        """Determina si un accordion-item es un WARP real basado en su estructura interna"""
        html = str(item)
        
        has_featured_p = 'class="featured"' in html
        has_rarity_spans = 'hsr-rar' in html and ('5★' in html or '4★' in html)
        has_featured_chars = 'featured-characters' in html
        has_featured_cones = 'featured-cone' in html
        has_avatar_cards = 'avatar-card' in html
        has_cone_images = 'hsr-set-image' in html
        
        has_event_name = 'event-name' in html
        has_duration = 'Event Duration' in html
        
        is_warp = (has_featured_p or has_rarity_spans) and (has_featured_chars or has_featured_cones or has_avatar_cards or has_cone_images)
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
        all_characters = []
        
        char_sections = item.find_all('div', class_='featured-characters')
        for section in char_sections:
            prev_p = section.find_previous('p', class_='featured')
            is_five_star = prev_p and '5★' in prev_p.text if prev_p else False
            
            cards = section.find_all('div', class_='avatar-card')
            for card in cards:
                char_data = self.parse_character(card)
                if char_data:
                    all_characters.append(char_data)
                    if is_five_star or char_data['rarity'] == 5:
                        featured_5star_char.append(char_data)
                    else:
                        featured_4star_char.append(char_data)
        
        return featured_5star_char, featured_4star_char, all_characters
    
    def extract_light_cones(self, item):
        """Extrae conos 5★ y 4★ de un banner"""
        featured_5star_cone = []
        featured_4star_cone = []
        all_cones = []
        
        cone_sections = item.find_all('div', class_='featured-cone')
        for section in cone_sections:
            prev_p = section.find_previous('p', class_='featured')
            is_five_star = prev_p and '5★' in prev_p.text if prev_p else False
            
            cone_items = section.find_all('div', class_='accordion-item')
            for cone in cone_items:
                cone_data = self.parse_light_cone(cone)
                if cone_data:
                    all_cones.append(cone_data)
                    if is_five_star or cone_data['rarity'] == 5:
                        featured_5star_cone.append(cone_data)
                    else:
                        featured_4star_cone.append(cone_data)
        
        return featured_5star_cone, featured_4star_cone, all_cones
    
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
            
            all_items = soup.find_all('div', class_='accordion-item')
            logger.info(f"Total accordion-items encontrados: {len(all_items)}")
            
            banners = []
            warp_count = 0
            skipped_count = 0
            
            for item in all_items:
                if not self.is_warp_banner(item):
                    skipped_count += 1
                    continue
                
                try:
                    name_tag = item.find('div', class_='event-name')
                    banner_name = name_tag.text.strip() if name_tag else "Banner sin nombre"
                    
                    banner_id = re.sub(r'[^a-zA-Z0-9]', '', banner_name.lower())
                    
                    time_tag = item.find('span', class_='time')
                    time_remaining = time_tag.text.strip() if time_tag else "Tiempo desconocido"
                    
                    duration_tag = item.find('p', class_='duration')
                    duration_text = duration_tag.text.strip() if duration_tag else ""
                    
                    start_date, end_date = self.parse_date_from_duration(duration_text)
                    
                    featured_5star_char, featured_4star_char, all_characters = self.extract_characters(item)
                    featured_5star_cone, featured_4star_cone, all_cones = self.extract_light_cones(item)
                    
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
                        banner_id=banner_id,
                        characters_data=all_characters,
                        cones_data=all_cones
                    )
                    banners.append(banner)
                    
                    logger.info(f"✅ Warp {warp_count}: {banner_name}")
                    logger.info(f"   - ID: {banner_id}")
                    logger.info(f"   - Tipo: {banner_type}")
                    logger.info(f"   - Personajes: {len(all_characters)}")
                    logger.info(f"   - Conos: {len(all_cones)}")
                    
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
thread_manager = ThreadManager()

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

async def create_banner_thread(channel, banner, status):
    """Crea un hilo (thread) para un banner con todas sus imágenes"""
    
    # Emoji según el tipo
    type_emoji = {
        "Personaje": "🦸",
        "Cono de Luz": "⚔️",
        "Mixto (Doble)": "🎁"
    }.get(banner.banner_type, "🎯")
    
    status_emoji = "🔴" if status == "actual" else "🟡"
    
    # Crear el mensaje inicial del hilo
    thread_name = f"{status_emoji} {type_emoji} {banner.name[:90]}"  # Máximo 100 chars
    
    # Mensaje principal con información del banner
    content = f"""# {status_emoji} **{banner.name}**

**Tipo:** {banner.banner_type}
**⏳ Tiempo restante:** {banner.time_remaining}

📅 **Duración:** {banner.duration_text.replace('Event Duration', '')}

"""
    
    # Añadir personajes destacados
    if banner.featured_5star_char or banner.featured_4star_char:
        content += "\n## ✨ Personajes Destacados\n"
        
        if banner.featured_5star_char:
            content += "\n**★5**\n"
            for char in banner.featured_5star_char:
                element_emoji = get_element_emoji(char.get('element', 'Unknown'))
                content += f"{element_emoji} **{char['name']}**\n"
        
        if banner.featured_4star_char:
            content += "\n**★4**\n"
            for char in banner.featured_4star_char:
                element_emoji = get_element_emoji(char.get('element', 'Unknown'))
                content += f"{element_emoji} **{char['name']}**\n"
    
    # Añadir conos de luz destacados
    if banner.featured_5star_cone or banner.featured_4star_cone:
        content += "\n## 💫 Conos de Luz Destacados\n"
        
        if banner.featured_5star_cone:
            content += "\n**★5**\n"
            for cone in banner.featured_5star_cone:
                content += f"💫 **{cone['name']}**\n"
        
        if banner.featured_4star_cone:
            content += "\n**★4**\n"
            for cone in banner.featured_4star_cone:
                content += f"📿 **{cone['name']}**\n"
    
    # Enviar mensaje principal
    main_msg = await channel.send(content)
    
    # Crear el hilo
    thread = await main_msg.create_thread(
        name=thread_name,
        auto_archive_duration=10080  # 7 días
    )
    
    # Enviar todas las imágenes como mensajes en el hilo
    all_images = []
    
    # Recopilar todas las URLs de imágenes
    for char in banner.characters_data:
        if char.get('image') and char['image'] not in all_images:
            all_images.append(char['image'])
    
    for cone in banner.cones_data:
        if cone.get('image') and cone['image'] not in all_images:
            all_images.append(cone['image'])
    
    # Enviar imágenes en lotes
    if all_images:
        await thread.send("## 🖼️ **Galería de Imágenes**")
        
        # Enviar imágenes en grupos de 5 para no saturar
        for i in range(0, len(all_images), 5):
            batch = all_images[i:i+5]
            img_content = ""
            for idx, img_url in enumerate(batch):
                img_content += f"[Imagen {i+idx+1}]({img_url})\n"
            
            if img_content:
                await thread.send(img_content)
            await asyncio.sleep(1)
    
    # Estadísticas finales
    total_5star = len(banner.featured_5star_char) + len(banner.featured_5star_cone)
    total_4star = len(banner.featured_4star_char) + len(banner.featured_4star_cone)
    
    await thread.send(f"✨ **{total_5star} ★5**  |  ⭐ **{total_4star} ★4**")
    
    return thread, main_msg

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 60)
logger.info("🚀 INICIANDO BOT DE HONKAI STAR RAIL - HILOS POR BANNER")
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

# ============================================
# EVENTOS Y COMANDOS DEL BOT
# ============================================
@bot.event
async def on_ready():
    logger.info(f'✅ {bot.user} ha conectado a Discord!')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🔮 Warps de HSR | !banners"
        )
    )
    
    if TARGET_CHANNEL_ACTUAL or TARGET_CHANNEL_PROXIMO:
        daily_banners.start()
        logger.info(f"📅 Tarea diaria iniciada")

@tasks.loop(hours=24)
async def daily_banners():
    """Actualiza los banners cada 24 horas (creando/actualizando hilos)"""
    await update_banner_threads()

@daily_banners.before_loop
async def before_daily_banners():
    await bot.wait_until_ready()

async def update_banner_threads():
    """Actualiza los hilos de banners"""
    
    all_banners = scraper.get_banners()
    
    if not all_banners:
        logger.warning("No se encontraron banners para actualizar")
        return
    
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
    
    logger.info(f"Clasificación: {len(banners_actuales)} actuales, {len(banners_proximos)} próximos")
    
    if TARGET_CHANNEL_ACTUAL:
        await update_channel_threads(TARGET_CHANNEL_ACTUAL, banners_actuales, "actual")
    
    if TARGET_CHANNEL_PROXIMO:
        await update_channel_threads(TARGET_CHANNEL_PROXIMO, banners_proximos, "proximo")

async def update_channel_threads(channel_id, banners, status):
    """Actualiza los hilos de un canal específico"""
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"❌ No se encontró el canal {channel_id}")
        return
    
    try:
        # Obtener hilos activos en el canal
        active_threads = []
        async for thread in channel.threads:
            active_threads.append(thread)
        
        logger.info(f"Canal {channel.name}: {len(active_threads)} hilos activos")
        
        # Mapear hilos existentes por ID de banner
        existing_threads = {}
        for thread in active_threads:
            for banner in banners:
                if banner.name in thread.name:
                    existing_threads[banner.banner_id] = thread
                    break
        
        # Crear o actualizar hilos
        for banner in banners:
            if banner.banner_id in existing_threads:
                # Actualizar hilo existente - cambiar nombre si es necesario
                thread = existing_threads[banner.banner_id]
                status_emoji = "🔴" if status == "actual" else "🟡"
                type_emoji = {
                    "Personaje": "🦸",
                    "Cono de Luz": "⚔️",
                    "Mixto (Doble)": "🎁"
                }.get(banner.banner_type, "🎯")
                
                new_name = f"{status_emoji} {type_emoji} {banner.name[:90]}"
                
                if thread.name != new_name:
                    try:
                        await thread.edit(name=new_name)
                        logger.info(f"✅ Hilo renombrado: {banner.name}")
                    except Exception as e:
                        logger.error(f"Error renombrando hilo {banner.name}: {e}")
                
                # Enviar mensaje de actualización al hilo
                try:
                    await thread.send(f"🔄 **Actualización {datetime.now().strftime('%d/%m/%Y %H:%M')}**\nTiempo restante: {banner.time_remaining}")
                except:
                    pass
            else:
                # Crear nuevo hilo
                try:
                    thread, main_msg = await create_banner_thread(channel, banner, status)
                    thread_manager.set_thread_id(channel_id, banner.banner_id, thread.id, main_msg.id)
                    logger.info(f"✅ Hilo creado: {banner.name}")
                except Exception as e:
                    logger.error(f"Error creando hilo {banner.name}: {e}")
            
            await asyncio.sleep(1)
        
        # Archivar hilos de banners que ya no existen
        current_ids = {b.banner_id for b in banners}
        for thread in active_threads:
            thread_id = None
            for banner_id, existing_thread in existing_threads.items():
                if existing_thread.id == thread.id and banner_id not in current_ids:
                    try:
                        await thread.edit(archived=True)
                        logger.info(f"📦 Hilo archivado (banner ya no existe)")
                        thread_manager.remove_thread(channel_id, banner_id)
                    except Exception as e:
                        logger.error(f"Error archivando hilo: {e}")
                    break
        
        logger.info(f"✅ Canal {channel.name} actualizado con {len(banners)} hilos")
        
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
        
        response = "## 📊 **Warps de Honkai: Star Rail**\n\n"
        
        if banners_actuales:
            response += "### 🔴 **ACTUALES**\n"
            for banner in banners_actuales:
                type_emoji = {
                    "Personaje": "🦸",
                    "Cono de Luz": "⚔️",
                    "Mixto (Doble)": "🎁"
                }.get(banner.banner_type, "🎯")
                response += f"{type_emoji} **{banner.name}** - {banner.time_remaining}\n"
            response += "\n"
        
        if banners_proximos:
            response += "### 🟡 **PRÓXIMOS**\n"
            for banner in banners_proximos:
                type_emoji = {
                    "Personaje": "🦸",
                    "Cono de Luz": "⚔️",
                    "Mixto (Doble)": "🎁"
                }.get(banner.banner_type, "🎯")
                response += f"{type_emoji} **{banner.name}** - {banner.time_remaining}\n"
        
        await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error en comando banners: {e}")
        await loading_msg.edit(content=f"❌ **Error:** {str(e)[:200]}")

@bot.command(name='threads_refresh')
@commands.has_permissions(administrator=True)
async def threads_refresh(ctx):
    """Fuerza actualización de hilos (solo admins)"""
    await ctx.send("🔄 **Forzando actualización de hilos...**")
    await update_banner_threads()

@bot.command(name='reset_threads')
@commands.has_permissions(administrator=True)
async def reset_threads(ctx, channel_type: str = None):
    """Resetea los hilos de un canal (solo admins)"""
    if not channel_type or channel_type not in ['actual', 'proximo']:
        await ctx.send("❌ **Usa:** `!reset_threads actual` o `!reset_threads proximo`")
        return
    
    channel_id = TARGET_CHANNEL_ACTUAL if channel_type == 'actual' else TARGET_CHANNEL_PROXIMO
    if not channel_id:
        await ctx.send(f"❌ **Canal {channel_type} no configurado**")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send(f"❌ **No se encontró el canal**")
        return
    
    # Archivar todos los hilos del canal
    async for thread in channel.threads:
        try:
            await thread.edit(archived=True)
            await asyncio.sleep(0.5)
        except:
            pass
    
    thread_manager.clear_channel(channel_id)
    
    await ctx.send(f"✅ **Hilos del canal {channel_type} archivados. Se recrearán en la próxima actualización.**")

@bot.command(name='stats')
async def banner_stats(ctx):
    """Muestra estadísticas de los warps"""
    banners = scraper.get_banners()
    
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
            await ctx.send("❌ **El bot no tiene permisos suficientes en este canal.**")
        except:
            pass
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

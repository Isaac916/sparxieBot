import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
import asyncio
from typing import List, Dict, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class Banner:
    def __init__(self, name: str, banner_type: str, time_remaining: str, 
                 featured_5star: List[Dict], featured_4star: List[Dict], 
                 light_cones: List[Dict], duration_text: str = ""):
        self.name = name
        self.type = banner_type
        self.time_remaining = time_remaining
        self.featured_5star = featured_5star  # Lista de dicts con {name, image, element, rarity}
        self.featured_4star = featured_4star  # Lista de dicts con {name, image, element, rarity}
        self.light_cones = light_cones  # Lista de dicts con {name, image, rarity}
        self.duration_text = duration_text

class BannerScraper:
    """Clase para hacer scraping de los banners de Prydwen"""
    
    def __init__(self):
        self.url = "https://www.prydwen.gg/star-rail/warp-events"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def extract_image_url(self, img_tag) -> Optional[str]:
        """Extrae la URL de la imagen del tag de Gatsby"""
        if not img_tag:
            return None
        
        # Buscar en srcset o src
        srcset = img_tag.get('srcset', '')
        if srcset:
            # Tomar la URL de mayor resolución (última)
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
    
    def parse_character_card(self, card) -> Dict:
        """Parsea una tarjeta de personaje"""
        try:
            # Nombre del personaje
            name_tag = card.find('a')
            name = name_tag.get('href', '').split('/')[-1].replace('-', ' ').title() if name_tag else "Unknown"
            
            # Imagen del personaje
            img_tag = card.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Elemento (del floating-element)
            element_tag = card.find('span', class_='floating-element')
            element_img = element_tag.find('img') if element_tag else None
            element = element_img.get('alt', 'Unknown') if element_img else "Unknown"
            
            # Rareza (de la clase)
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
    
    def parse_light_cone(self, cone_div) -> Dict:
        """Parsea un cono de luz"""
        try:
            # Buscar la imagen
            img_tag = cone_div.find('img')
            image_url = self.extract_image_url(img_tag)
            
            # Nombre (del span con clase hsr-set-name)
            name_tag = cone_div.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            # Rareza (de la clase)
            rarity = 5 if 'rarity-5' in str(cone_div) else 4
            
            return {
                'name': name,
                'image': image_url,
                'rarity': rarity
            }
        except Exception as e:
            logger.error(f"Error parseando cono de luz: {e}")
            return None
    
    def get_banners(self) -> List[Banner]:
        """Obtiene todos los banners actuales"""
        banners = []
        
        try:
            logger.info(f"Fetching data from {self.url}")
            response = requests.get(self.url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar todos los accordion-item (banners)
            banner_items = soup.find_all('div', class_='swan accordion-item')
            logger.info(f"Found {len(banner_items)} banner items")
            
            for item in banner_items:
                try:
                    # Nombre del banner
                    name_tag = item.find('div', class_='event-name')
                    banner_name = name_tag.text.strip() if name_tag else "Unknown Banner"
                    
                    # Tiempo restante
                    time_tag = item.find('span', class_='time')
                    time_remaining = time_tag.text.strip() if time_tag else "Unknown"
                    
                    # Duración del evento
                    duration_tag = item.find('p', class_='duration')
                    duration_text = duration_tag.text.strip() if duration_tag else ""
                    
                    # Determinar tipo de banner
                    banner_type = "Personaje"
                    if "Light Cone" in duration_text or "light cone" in str(item).lower():
                        banner_type = "Cono de Luz"
                    
                    # Personajes 5★ destacados
                    featured_5star = []
                    # Personajes 4★ destacados
                    featured_4star = []
                    
                    # Buscar sección de personajes destacados
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
                    
                    # Conos de luz destacados
                    light_cones = []
                    cone_sections = item.find_all('div', class_='featured-cone')
                    for section in cone_sections:
                        cone_items = section.find_all('div', class_='accordion-item')
                        for cone in cone_items:
                            cone_data = self.parse_light_cone(cone)
                            if cone_data:
                                light_cones.append(cone_data)
                    
                    # Crear objeto Banner solo si tiene contenido
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
                        logger.info(f"Added banner: {banner_name} with {len(featured_5star)} 5★, {len(featured_4star)} 4★, {len(light_cones)} cones")
                
                except Exception as e:
                    logger.error(f"Error procesando banner individual: {e}")
                    continue
            
            logger.info(f"Total banners parsed: {len(banners)}")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        return banners

# Instancia del scraper
scraper = BannerScraper()

# Canal donde se publicarán los banners (configurar con variable de entorno)
TARGET_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))

def create_banner_embed(banner: Banner) -> discord.Embed:
    """Crea un embed para un banner específico"""
    
    # Elegir color según tipo
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
    
    # Añadir duración del evento si está disponible
    if banner.duration_text:
        embed.add_field(
            name="📅 Duración del evento",
            value=banner.duration_text,
            inline=False
        )
    
    # Añadir personajes 5★
    if banner.featured_5star:
        chars_text = ""
        for char in banner.featured_5star[:4]:  # Máximo 4 personajes
            element_emoji = get_element_emoji(char['element'])
            chars_text += f"{element_emoji} **{char['name']}** (★5)\n"
        
        if chars_text:
            embed.add_field(name="✨ Personajes 5★ Destacados", value=chars_text, inline=True)
    
    # Añadir personajes 4★
    if banner.featured_4star:
        chars_text = ""
        for char in banner.featured_4star[:4]:
            element_emoji = get_element_emoji(char['element'])
            chars_text += f"{element_emoji} **{char['name']}** (★4)\n"
        
        if chars_text:
            embed.add_field(name="⭐ Personajes 4★ Destacados", value=chars_text, inline=True)
    
    # Añadir conos de luz
    if banner.light_cones:
        cones_text = ""
        for cone in banner.light_cones[:3]:
            rarity_star = "★5" if cone['rarity'] == 5 else "★4"
            cones_text += f"• **{cone['name']}** ({rarity_star})\n"
        
        if cones_text:
            embed.add_field(name="💫 Conos de Luz Destacados", value=cones_text, inline=False)
    
    # Añadir imagen del personaje principal si existe
    if banner.featured_5star and banner.featured_5star[0].get('image'):
        embed.set_thumbnail(url=banner.featured_5star[0]['image'])
    elif banner.light_cones and banner.light_cones[0].get('image'):
        embed.set_thumbnail(url=banner.light_cones[0]['image'])
    
    embed.set_footer(text="Datos obtenidos de Prydwen.gg • Actualizado diariamente")
    
    return embed

def get_element_emoji(element: str) -> str:
    """Devuelve el emoji correspondiente al elemento"""
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

@bot.event
async def on_ready():
    logger.info(f'{bot.user} ha conectado a Discord!')
    logger.info(f'ID del bot: {bot.user.id}')
    
    # Establecer estado personalizado
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="los banners de HSR | !banners"
        )
    )
    
    # Iniciar la tarea de publicación diaria
    if TARGET_CHANNEL_ID:
        daily_banners.start()
        logger.info(f"Tarea diaria iniciada para el canal {TARGET_CHANNEL_ID}")

@tasks.loop(hours=24)
async def daily_banners():
    """Publica los banners automáticamente cada 24 horas"""
    await publish_banners()

async def publish_banners():
    """Función para publicar los banners en el canal configurado"""
    if not TARGET_CHANNEL_ID:
        logger.warning("No se ha configurado DISCORD_CHANNEL_ID")
        return
    
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        logger.error(f"No se pudo encontrar el canal {TARGET_CHANNEL_ID}")
        return
    
    await send_banners(channel)

@bot.command(name='banners')
async def banners_command(ctx):
    """Comando para mostrar los banners actuales"""
    await send_banners(ctx.channel)

async def send_banners(channel):
    """Envía los banners al canal especificado"""
    
    # Enviar mensaje de carga
    loading_msg = await channel.send("🔄 Obteniendo información de los banners...")
    
    try:
        # Obtener banners
        banners = scraper.get_banners()
        
        if not banners:
            await loading_msg.edit(content="❌ No se pudieron obtener los banners. Intenta más tarde.")
            return
        
        # Eliminar mensaje de carga
        await loading_msg.delete()
        
        # Enviar cada banner como embed separado
        for banner in banners:
            embed = create_banner_embed(banner)
            await channel.send(embed=embed)
            await asyncio.sleep(1)  # Pequeña pausa entre embeds
        
        # Mensaje de resumen
        summary = f"✅ Mostrando **{len(banners)}** banners activos.\n📅 Próxima actualización automática en 24h."
        await channel.send(summary)
        
        logger.info(f"Banners enviados correctamente a {channel.name}")
        
    except Exception as e:
        logger.error(f"Error enviando banners: {e}")
        await loading_msg.edit(content=f"❌ Error al obtener los banners: {str(e)[:100]}")

@bot.command(name='refresh_banners')
@commands.has_permissions(administrator=True)
async def refresh_banners(ctx):
    """Comando para forzar la actualización de banners (solo admins)"""
    await ctx.send("🔄 Forzando actualización de banners...")
    await send_banners(ctx.channel)

@bot.command(name='banner_info')
async def banner_info(ctx, *, banner_name: str = None):
    """Muestra información detallada de un banner específico"""
    if not banner_name:
        await ctx.send("❌ Por favor, especifica el nombre del banner. Ejemplo: `!banner_info Deadly Dancer`")
        return
    
    banners = scraper.get_banners()
    
    # Buscar banner por nombre (coincidencia parcial)
    found_banners = [b for b in banners if banner_name.lower() in b.name.lower()]
    
    if not found_banners:
        await ctx.send(f"❌ No se encontró un banner con el nombre '{banner_name}'")
        return
    
    for banner in found_banners:
        embed = create_banner_embed(banner)
        await ctx.send(embed=embed)

# Manejo de errores
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado. Usa `!banners` para ver los banners actuales.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permiso para usar este comando.")
    else:
        logger.error(f"Error en comando: {error}")
        await ctx.send(f"❌ Ocurrió un error: {str(error)[:100]}")

# Obtener token de variables de entorno
TOKEN = os.getenv('DISCORD_TOKEN')

if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ ERROR: No se encontró DISCORD_TOKEN en las variables de entorno")
        logger.info("📝 Configura DISCORD_TOKEN en Railway")
    elif not TARGET_CHANNEL_ID:
        logger.warning("⚠️  No se configuró DISCORD_CHANNEL_ID. Los banners no se publicarán automáticamente.")
        logger.info("📝 Configura DISCORD_CHANNEL_ID en Railway para publicaciones automáticas")
        bot.run(TOKEN)
    else:
        bot.run(TOKEN)

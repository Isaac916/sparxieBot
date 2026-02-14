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
import difflib

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
# BASE DE DATOS DE ÍCONOS DE PERSONAJES
# ============================================

# Tu lista de íconos de Fandom Wiki
CHARACTER_ICONS = [
    {
        "id": "acheron",
        "name": "Acheron",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/24/Character_Acheron_Icon.png",
        "rarity": 5
    },
    {
        "id": "aglaea",
        "name": "Aglaea",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f8/Character_Aglaea_Icon.png",
        "rarity": 5
    },
    {
        "id": "anaxa",
        "name": "Anaxa",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f0/Character_Anaxa_Icon.png",
        "rarity": 5
    },
    {
        "id": "archer",
        "name": "Archer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/8f/Character_Archer_Icon.png",
        "rarity": 5
    },
    {
        "id": "argenti",
        "name": "Argenti",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c0/Character_Argenti_Icon.png",
        "rarity": 5
    },
    {
        "id": "arlan",
        "name": "Arlan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/a9/Character_Arlan_Icon.png",
        "rarity": 4
    },
    {
        "id": "asta",
        "name": "Asta",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/9f/Character_Asta_Icon.png",
        "rarity": 4
    },
    {
        "id": "aventurine",
        "name": "Aventurine",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/da/Character_Aventurine_Icon.png",
        "rarity": 5
    },
    {
        "id": "bailu",
        "name": "Bailu",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/47/Character_Bailu_Icon.png",
        "rarity": 5
    },
    {
        "id": "black-swan",
        "name": "Black Swan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/90/Character_Black_Swan_Icon.png",
        "rarity": 5
    },
    {
        "id": "blade",
        "name": "Blade",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/90/Character_Blade_Icon.png",
        "rarity": 5
    },
    {
        "id": "boothill",
        "name": "Boothill",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/78/Character_Boothill_Icon.png",
        "rarity": 5
    },
    {
        "id": "bronya",
        "name": "Bronya",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/0/0f/Character_Bronya_Icon.png",
        "rarity": 5
    },
    {
        "id": "castorice",
        "name": "Castorice",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/da/Character_Castorice_Icon.png",
        "rarity": 5
    },
    {
        "id": "cerydra",
        "name": "Cerydra",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c9/Character_Cerydra_Icon.png",
        "rarity": 5
    },
    {
        "id": "cipher",
        "name": "Cipher",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/99/Character_Cipher_Icon.png",
        "rarity": 5
    },
    {
        "id": "clara",
        "name": "Clara",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/a4/Character_Clara_Icon.png",
        "rarity": 5
    },
    {
        "id": "cyrene",
        "name": "Cyrene",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/99/Character_Cyrene_Icon.png",
        "rarity": 5
    },
    {
        "id": "dan-heng",
        "name": "Dan Heng",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/1a/Character_Dan_Heng_Icon.png",
        "rarity": 4
    },
    {
        "id": "dan-heng-•-imbibitor-lunae",
        "name": "Dan Heng • Imbibitor Lunae",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/2a/Character_Dan_Heng_%E2%80%A2_Imbibitor_Lunae_Icon.png",
        "rarity": 5
    },
    {
        "id": "dan-heng-•-permansor-terrae",
        "name": "Dan Heng • Permansor Terrae",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/fc/Character_Dan_Heng_%E2%80%A2_Permansor_Terrae_Icon.png",
        "rarity": 5
    },
    {
        "id": "dr-ratio",
        "name": "Dr. Ratio",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/47/Character_Dr._Ratio_Icon.png",
        "rarity": 5
    },
    {
        "id": "evernight",
        "name": "Evernight",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/b/b7/Character_Evernight_Icon.png",
        "rarity": 5
    },
    {
        "id": "feixiao",
        "name": "Feixiao",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/75/Character_Feixiao_Icon.png",
        "rarity": 5
    },
    {
        "id": "firefly",
        "name": "Firefly",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/9e/Character_Firefly_Icon.png",
        "rarity": 5
    },
    {
        "id": "fu-xuan",
        "name": "Fu Xuan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/1a/Character_Fu_Xuan_Icon.png",
        "rarity": 5
    },
    {
        "id": "fugue",
        "name": "Fugue",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c0/Character_Fugue_Icon.png",
        "rarity": 5
    },
    {
        "id": "gallagher",
        "name": "Gallagher",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/12/Character_Gallagher_Icon.png",
        "rarity": 4
    },
    {
        "id": "gepard",
        "name": "Gepard",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/75/Character_Gepard_Icon.png",
        "rarity": 5
    },
    {
        "id": "guinaifen",
        "name": "Guinaifen",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/98/Character_Guinaifen_Icon.png",
        "rarity": 4
    },
    {
        "id": "hanya",
        "name": "Hanya",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/99/Character_Hanya_Icon.png",
        "rarity": 4
    },
    {
        "id": "herta",
        "name": "Herta",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/b/bf/Character_Herta_Icon.png",
        "rarity": 4
    },
    {
        "id": "himeko",
        "name": "Himeko",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/0/00/Character_Himeko_Icon.png",
        "rarity": 5
    },
    {
        "id": "hook",
        "name": "Hook",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/d5/Character_Hook_Icon.png",
        "rarity": 4
    },
    {
        "id": "huohuo",
        "name": "Huohuo",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/6/68/Character_Huohuo_Icon.png",
        "rarity": 5
    },
    {
        "id": "hyacine",
        "name": "Hyacine",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c0/Character_Hyacine_Icon.png",
        "rarity": 5
    },
    {
        "id": "hysilens",
        "name": "Hysilens",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/19/Character_Hysilens_Icon.png",
        "rarity": 5
    },
    {
        "id": "jade",
        "name": "Jade",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/fd/Character_Jade_Icon.png",
        "rarity": 5
    },
    {
        "id": "jiaoqiu",
        "name": "Jiaoqiu",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/48/Character_Jiaoqiu_Icon.png",
        "rarity": 5
    },
    {
        "id": "jing-yuan",
        "name": "Jing Yuan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/88/Character_Jing_Yuan_Icon.png",
        "rarity": 5
    },
    {
        "id": "jingliu",
        "name": "Jingliu",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f9/Character_Jingliu_Icon.png",
        "rarity": 5
    },
    {
        "id": "kafka",
        "name": "Kafka",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/8c/Character_Kafka_Icon.png",
        "rarity": 5
    },
    {
        "id": "lingsha",
        "name": "Lingsha",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/ab/Character_Lingsha_Icon.png",
        "rarity": 5
    },
    {
        "id": "luka",
        "name": "Luka",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c7/Character_Luka_Icon.png",
        "rarity": 4
    },
    {
        "id": "luocha",
        "name": "Luocha",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/20/Character_Luocha_Icon.png",
        "rarity": 5
    },
    {
        "id": "lynx",
        "name": "Lynx",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/6/6c/Character_Lynx_Icon.png",
        "rarity": 4
    },
    {
        "id": "march-7th",
        "name": "March 7th",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/d3/Character_March_7th_Icon.png",
        "rarity": 4
    },
    {
        "id": "march-7th",
        "name": "March 7th",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/7b/Character_March_7th_%28The_Hunt%29_Icon.png",
        "rarity": 4
    },
    {
        "id": "misha",
        "name": "Misha",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/4d/Character_Misha_Icon.png",
        "rarity": 4
    },
    {
        "id": "moze",
        "name": "Moze",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/25/Character_Moze_Icon.png",
        "rarity": 4
    },
    {
        "id": "mydei",
        "name": "Mydei",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Mydei_Icon.png",
        "rarity": 5
    },
    {
        "id": "natasha",
        "name": "Natasha",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/6/61/Character_Natasha_Icon.png",
        "rarity": 4
    },
    {
        "id": "pela",
        "name": "Pela",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c2/Character_Pela_Icon.png",
        "rarity": 4
    },
    {
        "id": "phainon",
        "name": "Phainon",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/e/ef/Character_Phainon_Icon.png",
        "rarity": 5
    },
    {
        "id": "qingque",
        "name": "Qingque",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/2e/Character_Qingque_Icon.png",
        "rarity": 4
    },
    {
        "id": "rappa",
        "name": "Rappa",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/84/Character_Rappa_Icon.png",
        "rarity": 5
    },
    {
        "id": "robin",
        "name": "Robin",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/72/Character_Robin_Icon.png",
        "rarity": 5
    },
    {
        "id": "ruan-mei",
        "name": "Ruan Mei",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/16/Character_Ruan_Mei_Icon.png",
        "rarity": 5
    },
    {
        "id": "saber",
        "name": "Saber",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/43/Character_Saber_Icon.png",
        "rarity": 5
    },
    {
        "id": "sampo",
        "name": "Sampo",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/5/53/Character_Sampo_Icon.png",
        "rarity": 4
    },
    {
        "id": "seele",
        "name": "Seele",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/9a/Character_Seele_Icon.png",
        "rarity": 5
    },
    {
        "id": "serval",
        "name": "Serval",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/7c/Character_Serval_Icon.png",
        "rarity": 4
    },
    {
        "id": "silver-wolf",
        "name": "Silver Wolf",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/a3/Character_Silver_Wolf_Icon.png",
        "rarity": 5
    },
    {
        "id": "sparkle",
        "name": "Sparkle",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/6/6b/Character_Sparkle_Icon.png",
        "rarity": 5
    },
    {
        "id": "sunday",
        "name": "Sunday",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/3/38/Character_Sunday_Icon.png",
        "rarity": 5
    },
    {
        "id": "sushang",
        "name": "Sushang",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/97/Character_Sushang_Icon.png",
        "rarity": 4
    },
    {
        "id": "the-dahlia",
        "name": "The Dahlia",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/71/Character_The_Dahlia_Icon.png",
        "rarity": 5
    },
    {
        "id": "the-herta",
        "name": "The Herta",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/3/39/Character_The_Herta_Icon.png",
        "rarity": 5
    },
    {
        "id": "tingyun",
        "name": "Tingyun",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/4f/Character_Tingyun_Icon.png",
        "rarity": 4
    },
    {
        "id": "topaz-&-numby",
        "name": "Topaz & Numby",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Topaz_%26_Numby_Icon.png",
        "rarity": 5
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Trailblazer_%28Destruction%29_Icon.png",
        "rarity": 5
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c3/Character_Trailblazer_%28Preservation%29_Icon.png",
        "rarity": 5
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/fd/Character_Trailblazer_%28Harmony%29_Icon.png",
        "rarity": 5
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/43/Character_Trailblazer_%28Remembrance%29_Icon.png",
        "rarity": 5
    },
    {
        "id": "tribbie",
        "name": "Tribbie",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f3/Character_Tribbie_Icon.png",
        "rarity": 5
    },
    {
        "id": "welt",
        "name": "Welt",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/11/Character_Welt_Icon.png",
        "rarity": 5
    },
    {
        "id": "xueyi",
        "name": "Xueyi",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/23/Character_Xueyi_Icon.png",
        "rarity": 4
    },
    {
        "id": "yanqing",
        "name": "Yanqing",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/5/57/Character_Yanqing_Icon.png",
        "rarity": 5
    },
    {
        "id": "yukong",
        "name": "Yukong",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/3/32/Character_Yukong_Icon.png",
        "rarity": 4
    },
    {
        "id": "yunli",
        "name": "Yunli",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/43/Character_Yunli_Icon.png",
        "rarity": 5
    },
    {
        "id": "yao-guang",
        "name": "Yao Guang",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/1e/Character_Yao_Guang_Icon.png",
        "rarity": 5
    }
]

# Crear diccionarios para búsqueda rápida
CHARACTER_ICON_MAP = {}
for char in CHARACTER_ICONS:
    # Versión normalizada del nombre (minúsculas, sin espacios extra)
    normalized_name = char['name'].lower().strip()
    CHARACTER_ICON_MAP[normalized_name] = char['image']
    
    # También guardar por id
    CHARACTER_ICON_MAP[char['id'].lower()] = char['image']
    
    # Guardar también versiones sin puntos ni caracteres especiales
    simple_name = re.sub(r'[^a-z0-9]', '', normalized_name)
    CHARACTER_ICON_MAP[simple_name] = char['image']

# Imagen por defecto
DEFAULT_IMAGE = "https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png"

def get_character_icon(character_name):
    """Obtiene el ícono de un personaje por su nombre"""
    if not character_name:
        return DEFAULT_IMAGE
    
    # Normalizar el nombre de búsqueda
    search_name = character_name.lower().strip()
    
    # Búsqueda exacta
    if search_name in CHARACTER_ICON_MAP:
        logger.info(f"✅ Ícono encontrado para {character_name}")
        return CHARACTER_ICON_MAP[search_name]
    
    # Búsqueda por coincidencia parcial
    for key, url in CHARACTER_ICON_MAP.items():
        if search_name in key or key in search_name:
            logger.info(f"✅ Ícono encontrado (coincidencia parcial) para {character_name}: {key}")
            return url
    
    # Búsqueda por similitud (difflib)
    try:
        matches = difflib.get_close_matches(search_name, CHARACTER_ICON_MAP.keys(), n=1, cutoff=0.6)
        if matches:
            logger.info(f"✅ Ícono encontrado (similitud) para {character_name}: {matches[0]}")
            return CHARACTER_ICON_MAP[matches[0]]
    except:
        pass
    
    logger.warning(f"⚠️ No se encontró ícono para {character_name}, usando imagen por defecto")
    return DEFAULT_IMAGE

# ============================================
# CLASE BANNER (modificada para usar íconos)
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
# CLASE PARA GESTIONAR PUBLICACIONES DE FORO
# ============================================
class ForumManager:
    """Gestiona las publicaciones en canales de foro"""
    
    def __init__(self):
        self.posts_file = "forum_posts.json"
        self.posts = self.load_posts()
    
    def load_posts(self):
        """Carga las publicaciones guardadas"""
        try:
            if os.path.exists(self.posts_file):
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando publicaciones: {e}")
        return {}
    
    def save_posts(self):
        """Guarda las publicaciones"""
        try:
            with open(self.posts_file, 'w', encoding='utf-8') as f:
                json.dump(self.posts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando publicaciones: {e}")
    
    def get_post_id(self, channel_id, banner_id):
        """Obtiene el ID de la publicación para un banner específico"""
        key = f"{channel_id}_{banner_id}"
        return self.posts.get(key)
    
    def set_post_id(self, channel_id, banner_id, thread_id):
        """Guarda el ID de la publicación para un banner específico"""
        key = f"{channel_id}_{banner_id}"
        self.posts[key] = thread_id
        self.save_posts()
    
    def remove_post(self, channel_id, banner_id):
        """Elimina una publicación del registro"""
        key = f"{channel_id}_{banner_id}"
        if key in self.posts:
            del self.posts[key]
            self.save_posts()
    
    def clear_channel(self, channel_id):
        """Limpia todas las publicaciones de un canal"""
        keys_to_delete = [k for k in self.posts.keys() if k.startswith(f"{channel_id}_")]
        for key in keys_to_delete:
            del self.posts[key]
        self.save_posts()

# ============================================
# CLASE BANNER SCRAPER (simplificada, sin extracción de imágenes)
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
        
        # Lista de warps reales conocidos (para filtrar)
        self.real_warps = [
            'Deadly Dancer', 'Evil March Strikes Back', 'Full of Malice',
            'Seer Strategist', 'Excalibur!', 'Bone of My Sword'
        ]
        
        # Mapeo de elementos a emojis
        self.element_emojis = {
            'Physical': '💪', 'Fire': '🔥', 'Ice': '❄️',
            'Lightning': '⚡', 'Wind': '💨', 'Quantum': '⚛️',
            'Imaginary': '✨'
        }
    
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
        
        # Verificar por nombre conocido primero
        name_tag = item.find('div', class_='event-name')
        if name_tag:
            banner_name = name_tag.text.strip()
            if any(warp in banner_name for warp in self.real_warps):
                return True
        
        # Si no es conocido, verificar por estructura
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
        """Parsea un personaje de avatar-card (sin imagen)"""
        try:
            a_tag = card.find('a')
            name = "Unknown"
            char_key = ""
            
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                char_key = href.split('/')[-1]
                name = char_key.replace('-', ' ').title()
                logger.debug(f"Parsing character: {name} (key: {char_key})")
            
            element = "Unknown"
            element_tag = card.find('span', class_='floating-element')
            if element_tag:
                element_img = element_tag.find('img')
                if element_img and element_img.get('alt'):
                    element = element_img.get('alt')
                    logger.debug(f"Element found: {element}")
            
            card_html = str(card)
            rarity = 5 if 'rarity-5' in card_html or 'rar-5' in card_html else 4
            
            # Obtener imagen de nuestra base de datos
            image_url = get_character_icon(name)
            
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
                'image': DEFAULT_IMAGE,
                'element': "Unknown",
                'rarity': 4
            }
    
    def parse_light_cone(self, cone_item) -> dict:
        """Parsea un cono de luz (sin imagen)"""
        try:
            name_tag = cone_item.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            logger.debug(f"Parsing light cone: {name}")
            
            cone_html = str(cone_item)
            rarity = 5 if 'rarity-5' in cone_html or 'rar-5' in cone_html else 4
            
            # Para conos usamos imagen por defecto (podríamos expandir después)
            image_url = DEFAULT_IMAGE
            
            return {
                'name': name,
                'image': image_url,
                'rarity': rarity
            }
        except Exception:
            return {
                'name': "Unknown Cone",
                'image': DEFAULT_IMAGE,
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
                    
                    # Filtrar solo warps reales
                    if not any(warp in banner_name for warp in self.real_warps):
                        skipped_count += 1
                        continue
                    
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
forum_manager = ForumManager()

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

async def create_forum_post(forum_channel, banner, status):
    """Crea una publicación en un canal de foro para un banner con imágenes"""
    
    logger.info(f"Creando publicación para banner: {banner.name}")
    logger.info(f"Total personajes: {len(banner.characters_data)}")
    logger.info(f"Total conos: {len(banner.cones_data)}")
    
    # Emoji según el tipo
    type_emoji = {
        "Personaje": "🦸",
        "Cono de Luz": "⚔️",
        "Mixto (Doble)": "🎁"
    }.get(banner.banner_type, "🎯")
    
    status_emoji = "🔴" if status == "actual" else "🟡"
    
    # Título de la publicación
    thread_name = f"{status_emoji} {type_emoji} {banner.name[:90]}"
    
    # Contenido inicial de la publicación
    content = f"""# {status_emoji} **{banner.name}**

## 📋 Información General
**Tipo:** {banner.banner_type}
**⏳ Tiempo restante:** {banner.time_remaining}
**📅 Duración:** {banner.duration_text.replace('Event Duration', '')}

"""
    
    # Añadir personajes destacados CON SUS IMÁGENES
    if banner.featured_5star_char or banner.featured_4star_char:
        content += "## ✨ Personajes Destacados\n\n"
        
        if banner.featured_5star_char:
            content += "### ★5\n"
            for char in banner.featured_5star_char:
                element_emoji = get_element_emoji(char.get('element', 'Unknown'))
                content += f"{element_emoji} **{char['name']}**\n"
            content += "\n"
        
        if banner.featured_4star_char:
            content += "### ★4\n"
            for char in banner.featured_4star_char:
                element_emoji = get_element_emoji(char.get('element', 'Unknown'))
                content += f"{element_emoji} **{char['name']}**\n"
            content += "\n"
    
    # Añadir conos de luz destacados
    if banner.featured_5star_cone or banner.featured_4star_cone:
        content += "## 💫 Conos de Luz Destacados\n\n"
        
        if banner.featured_5star_cone:
            content += "### ★5\n"
            for cone in banner.featured_5star_cone:
                content += f"💫 **{cone['name']}**\n"
            content += "\n"
        
        if banner.featured_4star_cone:
            content += "### ★4\n"
            for cone in banner.featured_4star_cone:
                content += f"📿 **{cone['name']}**\n"
            content += "\n"
    
    # Crear la publicación en el foro
    thread = await forum_channel.create_thread(
        name=thread_name,
        content=content,
        auto_archive_duration=10080  # 7 días
    )
    
    thread_obj = thread[0] if isinstance(thread, tuple) else thread
    
    # Enviar todas las imágenes como mensajes en el hilo
    all_images = []
    
    # Recopilar todas las URLs de imágenes (evitando duplicados)
    for char in banner.characters_data:
        if char.get('image') and char['image'] not in all_images:
            if char['image'] != DEFAULT_IMAGE:
                all_images.append(char['image'])
                logger.info(f"🖼️ Imagen de personaje añadida: {char['name']} - {char['image']}")
            else:
                logger.warning(f"⚠️ Personaje {char['name']} usa imagen por defecto")
    
    for cone in banner.cones_data:
        if cone.get('image') and cone['image'] not in all_images:
            if cone['image'] != DEFAULT_IMAGE:
                all_images.append(cone['image'])
                logger.info(f"🖼️ Imagen de cono añadida: {cone['name']} - {cone['image']}")
            else:
                logger.warning(f"⚠️ Cono {cone['name']} usa imagen por defecto")
    
    logger.info(f"Total imágenes a enviar: {len(all_images)}")
    
    # Enviar imágenes con un mensaje más vistoso
    if all_images:
        await thread_obj.send("## 🖼️ **Galería de Imágenes**")
        
        # Enviar cada imagen individualmente
        for i, img_url in enumerate(all_images[:10], 1):
            try:
                logger.info(f"Enviando imagen {i}: {img_url}")
                
                # Verificar que la URL es accesible
                try:
                    response = requests.head(img_url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✅ URL {i} es accesible")
                    else:
                        logger.warning(f"⚠️ URL {i} devuelve código {response.status_code}")
                except:
                    logger.warning(f"⚠️ No se pudo verificar URL {i}")
                
                # Enviar la imagen directamente
                await thread_obj.send(img_url)
                logger.info(f"✅ Imagen {i} enviada correctamente")
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error enviando imagen {img_url}: {e}")
                # Si falla, intentar con embed
                try:
                    embed = discord.Embed(title=f"Imagen {i}")
                    embed.set_image(url=img_url)
                    await thread_obj.send(embed=embed)
                    logger.info(f"✅ Imagen {i} enviada como embed")
                except:
                    logger.error(f"❌ No se pudo enviar la URL {img_url}")
    else:
        logger.warning("⚠️ No hay imágenes para enviar")
        await thread_obj.send("📸 *No hay imágenes disponibles para este banner*")
    
    # Estadísticas finales
    total_5star = len(banner.featured_5star_char) + len(banner.featured_5star_cone)
    total_4star = len(banner.featured_4star_char) + len(banner.featured_4star_cone)
    
    # Mensaje de resumen
    summary = f"""## 📊 **Resumen**
✨ **{total_5star} ★5**  |  ⭐ **{total_4star} ★4**

*Los personajes y conos destacados aparecen arriba con sus imágenes.*
"""
    await thread_obj.send(summary)
    
    return thread_obj

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 60)
logger.info("🚀 INICIANDO BOT DE HONKAI STAR RAIL - CON ÍCONOS DE FANDOM")
logger.info("=" * 60)

TOKEN = os.environ.get('DISCORD_TOKEN')
FORUM_CHANNEL_ID_ACTUAL = os.environ.get('FORUM_CHANNEL_ACTUAL')
FORUM_CHANNEL_ID_PROXIMO = os.environ.get('FORUM_CHANNEL_PROXIMO')

logger.info(f"🔑 DISCORD_TOKEN: {'✅ ENCONTRADO' if TOKEN else '❌ NO ENCONTRADO'}")
logger.info(f"📢 Canal FORO ACTUAL: {'✅ ' + FORUM_CHANNEL_ID_ACTUAL if FORUM_CHANNEL_ID_ACTUAL else '❌ NO CONFIGURADO'}")
logger.info(f"📢 Canal FORO PRÓXIMO: {'✅ ' + FORUM_CHANNEL_ID_PROXIMO if FORUM_CHANNEL_ID_PROXIMO else '❌ NO CONFIGURADO'}")

TARGET_FORUM_ACTUAL = None
if FORUM_CHANNEL_ID_ACTUAL:
    try:
        TARGET_FORUM_ACTUAL = int(FORUM_CHANNEL_ID_ACTUAL.strip())
        logger.info(f"✅ Foro actual: {TARGET_FORUM_ACTUAL}")
    except ValueError:
        logger.error(f"❌ FORUM_CHANNEL_ACTUAL no es válido: {FORUM_CHANNEL_ID_ACTUAL}")

TARGET_FORUM_PROXIMO = None
if FORUM_CHANNEL_ID_PROXIMO:
    try:
        TARGET_FORUM_PROXIMO = int(FORUM_CHANNEL_ID_PROXIMO.strip())
        logger.info(f"✅ Foro próximo: {TARGET_FORUM_PROXIMO}")
    except ValueError:
        logger.error(f"❌ FORUM_CHANNEL_PROXIMO no es válido: {FORUM_CHANNEL_ID_PROXIMO}")

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
    
    if TARGET_FORUM_ACTUAL or TARGET_FORUM_PROXIMO:
        daily_forum_posts.start()
        logger.info(f"📅 Tarea diaria iniciada")

@tasks.loop(hours=24)
async def daily_forum_posts():
    """Actualiza las publicaciones del foro cada 24 horas"""
    await update_forum_posts()

@daily_forum_posts.before_loop
async def before_daily_forum_posts():
    await bot.wait_until_ready()

async def update_forum_posts():
    """Actualiza las publicaciones del foro"""
    
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
    
    if TARGET_FORUM_ACTUAL:
        await update_forum_channel(TARGET_FORUM_ACTUAL, banners_actuales, "actual")
    
    if TARGET_FORUM_PROXIMO:
        await update_forum_channel(TARGET_FORUM_PROXIMO, banners_proximos, "proximo")

async def update_forum_channel(channel_id, banners, status):
    """Actualiza las publicaciones de un canal de foro específico"""
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"❌ No se encontró el canal {channel_id}")
        return
    
    # Verificar que es un canal de foro
    if not isinstance(channel, discord.ForumChannel):
        logger.error(f"❌ El canal {channel_id} no es un foro (es {type(channel).__name__})")
        return
    
    try:
        # Obtener hilos activos en el foro
        active_threads = []
        
        # Los hilos activos normales (no archivados)
        active_threads.extend(channel.threads)
        
        # Hilos archivados
        async for thread in channel.archived_threads(limit=100):
            active_threads.append(thread)
        
        logger.info(f"Foro {channel.name}: {len(active_threads)} hilos encontrados")
        
        # Mapear hilos existentes por ID de banner
        existing_posts = {}
        for thread in active_threads:
            for banner in banners:
                if banner.name in thread.name:
                    existing_posts[banner.banner_id] = thread
                    break
        
        # Crear o actualizar publicaciones
        for banner in banners:
            if banner.banner_id in existing_posts:
                # Actualizar título del hilo si es necesario
                thread = existing_posts[banner.banner_id]
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
                # Crear nueva publicación en el foro
                try:
                    thread = await create_forum_post(channel, banner, status)
                    forum_manager.set_post_id(channel_id, banner.banner_id, thread.id)
                    logger.info(f"✅ Publicación creada: {banner.name}")
                except Exception as e:
                    logger.error(f"Error creando publicación {banner.name}: {e}")
            
            await asyncio.sleep(1)
        
        # Archivar publicaciones de banners que ya no existen
        current_ids = {b.banner_id for b in banners}
        for thread in active_threads:
            for banner_id, existing_thread in existing_posts.items():
                if existing_thread.id == thread.id and banner_id not in current_ids:
                    try:
                        await thread.edit(archived=True, locked=True)
                        logger.info(f"📦 Hilo archivado (banner ya no existe)")
                        forum_manager.remove_post(channel_id, banner_id)
                    except Exception as e:
                        logger.error(f"Error archivando hilo: {e}")
                    break
        
        logger.info(f"✅ Foro {channel.name} actualizado con {len(banners)} publicaciones")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando foro {channel.name}: {e}")

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
        
        if len(response) > 2000:
            parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error en comando banners: {e}")
        await loading_msg.edit(content=f"❌ **Error:** {str(e)[:200]}")

@bot.command(name='refresh_forum')
@commands.has_permissions(administrator=True)
async def refresh_forum(ctx):
    """Fuerza actualización del foro (solo admins)"""
    await ctx.send("🔄 **Forzando actualización del foro...**")
    await update_forum_posts()

@bot.command(name='reset_forum')
@commands.has_permissions(administrator=True)
async def reset_forum(ctx, channel_type: str = None):
    """Resetea las publicaciones de un foro (solo admins)"""
    if not channel_type or channel_type not in ['actual', 'proximo']:
        await ctx.send("❌ **Usa:** `!reset_forum actual` o `!reset_forum proximo`")
        return
    
    channel_id = TARGET_FORUM_ACTUAL if channel_type == 'actual' else TARGET_FORUM_PROXIMO
    if not channel_id:
        await ctx.send(f"❌ **Foro {channel_type} no configurado**")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send(f"❌ **No se encontró el foro**")
        return
    
    # Archivar todos los hilos del foro
    async for thread in channel.archived_threads(limit=100):
        try:
            await thread.edit(archived=True, locked=True)
            await asyncio.sleep(0.5)
        except:
            pass
    
    for thread in channel.threads:
        try:
            await thread.edit(archived=True, locked=True)
            await asyncio.sleep(0.5)
        except:
            pass
    
    forum_manager.clear_channel(channel_id)
    
    await ctx.send(f"✅ **Foro {channel_type} reseteado. Las publicaciones se recrearán en la próxima actualización.**")

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

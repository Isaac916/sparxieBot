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
# BASE DE DATOS DE ÍCONOS DE PERSONAJES 5★
# ============================================

CHARACTER_ICONS = [
    {
        "id": "acheron",
        "name": "Acheron",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/24/Character_Acheron_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Lightning"
    },
    {
        "id": "aglaea",
        "name": "Aglaea",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f8/Character_Aglaea_Icon.png",
        "rarity": 5,
        "path": "Remembrance",
        "element": "Lightning"
    },
    {
        "id": "anaxa",
        "name": "Anaxa",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f0/Character_Anaxa_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Wind"
    },
    {
        "id": "archer",
        "name": "Archer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/8f/Character_Archer_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "argenti",
        "name": "Argenti",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c0/Character_Argenti_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Physical"
    },
    {
        "id": "aventurine",
        "name": "Aventurine",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/da/Character_Aventurine_Icon.png",
        "rarity": 5,
        "path": "Preservation",
        "element": "Imaginary"
    },
    {
        "id": "bailu",
        "name": "Bailu",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/47/Character_Bailu_Icon.png",
        "rarity": 5,
        "path": "Abundance",
        "element": "Lightning"
    },
    {
        "id": "black-swan",
        "name": "Black Swan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/90/Character_Black_Swan_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Wind"
    },
    {
        "id": "blade",
        "name": "Blade",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/90/Character_Blade_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Wind"
    },
    {
        "id": "boothill",
        "name": "Boothill",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/78/Character_Boothill_Icon.png",
        "rarity": 5,
        "path": "The Hunt",
        "element": "Physical"
    },
    {
        "id": "bronya",
        "name": "Bronya",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/0/0f/Character_Bronya_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Wind"
    },
    {
        "id": "castorice",
        "name": "Castorice",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/da/Character_Castorice_Icon.png",
        "rarity": 5,
        "path": "Remembrance",
        "element": "Quantum"
    },
    {
        "id": "cerydra",
        "name": "Cerydra",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c9/Character_Cerydra_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "cipher",
        "name": "Cipher",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/99/Character_Cipher_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "clara",
        "name": "Clara",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/a4/Character_Clara_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Physical"
    },
    {
        "id": "cyrene",
        "name": "Cyrene",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/99/Character_Cyrene_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "dan-heng-•-imbibitor-lunae",
        "name": "Dan Heng • Imbibitor Lunae",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/2a/Character_Dan_Heng_%E2%80%A2_Imbibitor_Lunae_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Imaginary"
    },
    {
        "id": "dan-heng-•-permansor-terrae",
        "name": "Dan Heng • Permansor Terrae",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/fc/Character_Dan_Heng_%E2%80%A2_Permansor_Terrae_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "dr-ratio",
        "name": "Dr. Ratio",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/47/Character_Dr._Ratio_Icon.png",
        "rarity": 5,
        "path": "The Hunt",
        "element": "Imaginary"
    },
    {
        "id": "evernight",
        "name": "Evernight",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/b/b7/Character_Evernight_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "feixiao",
        "name": "Feixiao",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/75/Character_Feixiao_Icon.png",
        "rarity": 5,
        "path": "The Hunt",
        "element": "Wind"
    },
    {
        "id": "firefly",
        "name": "Firefly",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/9e/Character_Firefly_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Fire"
    },
    {
        "id": "fu-xuan",
        "name": "Fu Xuan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/1a/Character_Fu_Xuan_Icon.png",
        "rarity": 5,
        "path": "Preservation",
        "element": "Quantum"
    },
    {
        "id": "fugue",
        "name": "Fugue",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c0/Character_Fugue_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Fire"
    },
    {
        "id": "gepard",
        "name": "Gepard",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/75/Character_Gepard_Icon.png",
        "rarity": 5,
        "path": "Preservation",
        "element": "Ice"
    },
    {
        "id": "himeko",
        "name": "Himeko",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/0/00/Character_Himeko_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Fire"
    },
    {
        "id": "huohuo",
        "name": "Huohuo",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/6/68/Character_Huohuo_Icon.png",
        "rarity": 5,
        "path": "Abundance",
        "element": "Wind"
    },
    {
        "id": "hyacine",
        "name": "Hyacine",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c0/Character_Hyacine_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "hysilens",
        "name": "Hysilens",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/19/Character_Hysilens_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "jade",
        "name": "Jade",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/fd/Character_Jade_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Quantum"
    },
    {
        "id": "jiaoqiu",
        "name": "Jiaoqiu",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/48/Character_Jiaoqiu_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Fire"
    },
    {
        "id": "jing-yuan",
        "name": "Jing Yuan",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/88/Character_Jing_Yuan_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Lightning"
    },
    {
        "id": "jingliu",
        "name": "Jingliu",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f9/Character_Jingliu_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Ice"
    },
    {
        "id": "kafka",
        "name": "Kafka",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/8c/Character_Kafka_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Lightning"
    },
    {
        "id": "lingsha",
        "name": "Lingsha",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/ab/Character_Lingsha_Icon.png",
        "rarity": 5,
        "path": "Abundance",
        "element": "Fire"
    },
    {
        "id": "luocha",
        "name": "Luocha",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/20/Character_Luocha_Icon.png",
        "rarity": 5,
        "path": "Abundance",
        "element": "Imaginary"
    },
    {
        "id": "mydei",
        "name": "Mydei",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Mydei_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Imaginary"
    },
    {
        "id": "phainon",
        "name": "Phainon",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/e/ef/Character_Phainon_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "rappa",
        "name": "Rappa",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/84/Character_Rappa_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Imaginary"
    },
    {
        "id": "robin",
        "name": "Robin",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/72/Character_Robin_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Physical"
    },
    {
        "id": "ruan-mei",
        "name": "Ruan Mei",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/16/Character_Ruan_Mei_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Ice"
    },
    {
        "id": "saber",
        "name": "Saber",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/43/Character_Saber_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "seele",
        "name": "Seele",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/9/9a/Character_Seele_Icon.png",
        "rarity": 5,
        "path": "The Hunt",
        "element": "Quantum"
    },
    {
        "id": "silver-wolf",
        "name": "Silver Wolf",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/a3/Character_Silver_Wolf_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Quantum"
    },
    {
        "id": "sparkle",
        "name": "Sparkle",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/6/6b/Character_Sparkle_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Quantum"
    },
    {
        "id": "sunday",
        "name": "Sunday",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/3/38/Character_Sunday_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Imaginary"
    },
    {
        "id": "the-dahlia",
        "name": "The Dahlia",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/71/Character_The_Dahlia_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    },
    {
        "id": "the-herta",
        "name": "The Herta",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/3/39/Character_The_Herta_Icon.png",
        "rarity": 5,
        "path": "Erudition",
        "element": "Ice"
    },
    {
        "id": "topaz-&-numby",
        "name": "Topaz & Numby",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Topaz_%26_Numby_Icon.png",
        "rarity": 5,
        "path": "The Hunt",
        "element": "Fire"
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/8/89/Character_Trailblazer_%28Destruction%29_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Physical"
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/c3/Character_Trailblazer_%28Preservation%29_Icon.png",
        "rarity": 5,
        "path": "Preservation",
        "element": "Fire"
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/fd/Character_Trailblazer_%28Harmony%29_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Imaginary"
    },
    {
        "id": "trailblazer",
        "name": "Trailblazer",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/43/Character_Trailblazer_%28Remembrance%29_Icon.png",
        "rarity": 5,
        "path": "Remembrance",
        "element": "Ice"
    },
    {
        "id": "tribbie",
        "name": "Tribbie",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/f/f3/Character_Tribbie_Icon.png",
        "rarity": 5,
        "path": "Harmony",
        "element": "Quantum"
    },
    {
        "id": "welt",
        "name": "Welt",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/11/Character_Welt_Icon.png",
        "rarity": 5,
        "path": "Nihility",
        "element": "Imaginary"
    },
    {
        "id": "yanqing",
        "name": "Yanqing",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/5/57/Character_Yanqing_Icon.png",
        "rarity": 5,
        "path": "The Hunt",
        "element": "Ice"
    },
    {
        "id": "yunli",
        "name": "Yunli",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/4/43/Character_Yunli_Icon.png",
        "rarity": 5,
        "path": "Destruction",
        "element": "Physical"
    },
    {
        "id": "yao-guang",
        "name": "Yao Guang",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/1e/Character_Yao_Guang_Icon.png",
        "rarity": 5,
        "path": "Elation",
        "element": "Physical"
    },
    {
        "id": "march-7th-evernight",
        "name": "March 7th Evernight",
        "image": "https://static.wikia.nocookie.net/houkai-star-rail/images/b/b7/Character_Evernight_Icon.png",
        "rarity": 5,
        "path": "Unknown",
        "element": "Unknown"
    }
]

# Crear diccionarios para búsqueda rápida (solo personajes 5★)
CHARACTER_ICON_MAP = {}
CHARACTER_INFO_MAP = {}

for char in CHARACTER_ICONS:
    # Solo incluir personajes 5★ en el mapa
    if char['rarity'] == 5:
        # Versión normalizada del nombre
        normalized_name = char['name'].lower().strip()
        CHARACTER_ICON_MAP[normalized_name] = char['image']
        CHARACTER_INFO_MAP[normalized_name] = {
            'path': char['path'],
            'element': char['element'],
            'rarity': char['rarity']
        }
        
        # También por id
        char_id = char['id'].lower()
        CHARACTER_ICON_MAP[char_id] = char['image']
        CHARACTER_INFO_MAP[char_id] = {
            'path': char['path'],
            'element': char['element'],
            'rarity': char['rarity']
        }
        
        # Versión sin caracteres especiales
        simple_name = re.sub(r'[^a-z0-9]', '', normalized_name)
        CHARACTER_ICON_MAP[simple_name] = char['image']
        CHARACTER_INFO_MAP[simple_name] = {
            'path': char['path'],
            'element': char['element'],
            'rarity': char['rarity']
        }

DEFAULT_IMAGE = "https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png"

def get_character_info(character_name):
    """Obtiene información SOLO de personajes 5★"""
    if not character_name:
        return None
    
    # Normalizar el nombre de búsqueda
    search_name = character_name.lower().strip()
    
    # PASO 1: Búsqueda exacta
    if search_name in CHARACTER_INFO_MAP:
        logger.info(f"✅ Coincidencia exacta para 5★: {character_name}")
        return {
            'name': character_name,
            'image': CHARACTER_ICON_MAP[search_name],
            'path': CHARACTER_INFO_MAP[search_name]['path'],
            'element': CHARACTER_INFO_MAP[search_name]['element'],
            'rarity': 5
        }
    
    # PASO 2: Búsqueda por nombre simplificado
    search_simple = re.sub(r'[^a-z0-9]', '', search_name)
    for key, info in CHARACTER_INFO_MAP.items():
        key_simple = re.sub(r'[^a-z0-9]', '', key)
        if search_simple == key_simple:
            logger.info(f"✅ Coincidencia simplificada para 5★: {character_name}")
            return {
                'name': character_name,
                'image': CHARACTER_ICON_MAP[key],
                'path': info['path'],
                'element': info['element'],
                'rarity': 5
            }
    
    # PASO 3: Búsqueda por coincidencia parcial (solo si es claramente el mismo personaje)
    for key, info in CHARACTER_INFO_MAP.items():
        # Evitar coincidencias cortas como "Hanya" con "Anaxa"
        if len(key) >= 4 and len(search_name) >= 4:
            if key in search_name or search_name in key:
                # Verificar que no sea una coincidencia falsa
                if key not in ['hanya', 'pela', 'qingque']:  # Excluir nombres 4★ conocidos
                    logger.info(f"✅ Coincidencia parcial para 5★: {character_name} con {key}")
                    return {
                        'name': character_name,
                        'image': CHARACTER_ICON_MAP[key],
                        'path': info['path'],
                        'element': info['element'],
                        'rarity': 5
                    }
    
    # No es un personaje 5★ conocido
    logger.info(f"⏩ {character_name} no es un personaje 5★ reconocido")
    return None

# ============================================
# CLASE ENDGAME CONTENT
# ============================================
class EndgameContent:
    def __init__(self, name: str, version: str, time_remaining: str, content_type: str):
        self.name = name
        self.version = version
        self.time_remaining = time_remaining
        self.content_type = content_type  # Memory of Chaos, Pure Fiction, Apocalyptic Shadow

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
# CLASE PARA GESTIONAR PUBLICACIONES DE FORO
# ============================================
class ForumManager:
    """Gestiona las publicaciones en canales de foro"""
    
    def __init__(self):
        self.posts_file = "forum_posts.json"
        self.posts = self.load_posts()
    
    def load_posts(self):
        try:
            if os.path.exists(self.posts_file):
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando publicaciones: {e}")
        return {}
    
    def save_posts(self):
        try:
            with open(self.posts_file, 'w', encoding='utf-8') as f:
                json.dump(self.posts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando publicaciones: {e}")
    
    def get_post_id(self, channel_id, content_id):
        key = f"{channel_id}_{content_id}"
        return self.posts.get(key)
    
    def set_post_id(self, channel_id, content_id, thread_id):
        key = f"{channel_id}_{content_id}"
        self.posts[key] = thread_id
        self.save_posts()
    
    def remove_post(self, channel_id, content_id):
        key = f"{channel_id}_{content_id}"
        if key in self.posts:
            del self.posts[key]
            self.save_posts()
    
    def clear_channel(self, channel_id):
        keys_to_delete = [k for k in self.posts.keys() if k.startswith(f"{channel_id}_")]
        for key in keys_to_delete:
            del self.posts[key]
            self.save_posts()

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
        
        # Lista de warps reales conocidos
        self.real_warps = [
            'Deadly Dancer', 'Evil March Strikes Back', 'Full of Malice',
            'Seer Strategist', 'Excalibur!', 'Bone of My Sword'
        ]
        
        # Lista de contenido End Game
        self.endgame_modes = ['Memory of Chaos', 'Pure Fiction', 'Apocalyptic Shadow']
    
    def parse_date_from_duration(self, duration_text):
        if not duration_text:
            return None, None
        
        start_date = None
        end_date = None
        
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
        html = str(item)
        
        name_tag = item.find('div', class_='event-name')
        if name_tag:
            banner_name = name_tag.text.strip()
            if any(warp in banner_name for warp in self.real_warps):
                return True
        
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
    
    def is_endgame_content(self, item) -> bool:
        """Determina si un accordion-item es contenido End Game"""
        name_tag = item.find('div', class_='event-name')
        if not name_tag:
            return False
        
        name = name_tag.text.strip()
        
        # Verificar si el nombre contiene alguno de los modos End Game
        for mode in self.endgame_modes:
            if mode in name:
                return True
        
        return False
    
   def extract_endgame_content(self, item):
    """Extrae información del contenido End Game con tiempo correcto"""
    name_tag = item.find('div', class_='event-name')
    name = name_tag.text.strip() if name_tag else ""
    
    # Extraer versión (lo que está entre paréntesis)
    version_match = re.search(r'\(([^)]+)\)', name)
    version = version_match.group(1) if version_match else ""
    
    # Extraer tiempo restante del countdown
    time_tag = item.find('span', class_='time')
    time_remaining = time_tag.text.strip() if time_tag else "Tiempo desconocido"
    
    # Limpiar el tiempo (a veces viene con espacios extras)
    time_remaining = re.sub(r'\s+', ' ', time_remaining).strip()
    
    # CORRECCIÓN: Restar 2 días y 5 horas del tiempo extraído
    corrected_time = self.subtract_time(time_remaining, days=2, hours=5)
    
    logger.info(f"⏱️ Tiempo original para {content_type}: {time_remaining} -> Corregido: {corrected_time}")
    
    # Determinar el tipo
    content_type = ""
    for mode in self.endgame_modes:
        if mode in name:
            content_type = mode
            break
    
    return EndgameContent(name, version, corrected_time, content_type)

def subtract_time(self, time_str, days=0, hours=0):
    """Resta días y horas de una cadena de tiempo como 'Xd Xh'"""
    if time_str == "Tiempo desconocido":
        return time_str
    
    try:
        # Extraer días y horas actuales
        current_days = 0
        current_hours = 0
        
        # Buscar patrones como "Xd" y "Xh"
        days_match = re.search(r'(\d+)d', time_str)
        if days_match:
            current_days = int(days_match.group(1))
        
        hours_match = re.search(r'(\d+)h', time_str)
        if hours_match:
            current_hours = int(hours_match.group(1))
        
        # Restar días y horas
        new_days = current_days - days
        new_hours = current_hours - hours
        
        # Ajustar si las horas quedan negativas
        if new_hours < 0:
            new_days -= 1
            new_hours += 24
        
        # Ajustar si los días quedan negativos
        if new_days < 0:
            new_days = 0
            new_hours = 0
        
        # Construir nueva cadena de tiempo
        if new_days > 0 and new_hours > 0:
            return f"{new_days}d {new_hours}h"
        elif new_days > 0:
            return f"{new_days}d"
        elif new_hours > 0:
            return f"{new_hours}h"
        else:
            return "Terminado"
            
    except Exception as e:
        logger.error(f"Error restando tiempo: {e}")
        return time_str
    
    def parse_character(self, card) -> dict:
        try:
            a_tag = card.find('a')
            name = "Unknown"
            char_key = ""
            
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                char_key = href.split('/')[-1]
                name = char_key.replace('-', ' ').title()
            
            # Intentar obtener elemento del HTML
            element = "Unknown"
            element_tag = card.find('span', class_='floating-element')
            if element_tag:
                element_img = element_tag.find('img')
                if element_img and element_img.get('alt'):
                    element = element_img.get('alt')
            
            # Determinar rareza por el HTML
            card_html = str(card)
            html_rarity = 5 if 'rarity-5' in card_html or 'rar-5' in card_html else 4
            
            return {
                'name': name,
                'element': element,
                'rarity': html_rarity,
                'char_key': char_key
            }
        except Exception as e:
            logger.error(f"Error parseando personaje: {e}")
            return None
    
    def extract_characters(self, item):
        featured_5star_char = []
        featured_4star_char = []
        
        char_sections = item.find_all('div', class_='featured-characters')
        for section in char_sections:
            prev_p = section.find_previous('p', class_='featured')
            is_five_star_section = prev_p and '5★' in prev_p.text if prev_p else False
            
            cards = section.find_all('div', class_='avatar-card')
            for card in cards:
                char_data = self.parse_character(card)
                if char_data:
                    # Solo añadir a la lista correspondiente según la rareza del HTML
                    if char_data['rarity'] == 5:
                        featured_5star_char.append(char_data)
                    else:
                        featured_4star_char.append(char_data)
        
        return featured_5star_char, featured_4star_char
    
    def extract_light_cones(self, item):
        featured_5star_cone = []
        featured_4star_cone = []
        
        cone_sections = item.find_all('div', class_='featured-cone')
        for section in cone_sections:
            prev_p = section.find_previous('p', class_='featured')
            is_five_star = prev_p and '5★' in prev_p.text if prev_p else False
            
            cone_items = section.find_all('div', class_='accordion-item')
            for cone in cone_items:
                # Por ahora, simplificamos los conos
                name_tag = cone.find('span', class_='hsr-set-name')
                name = name_tag.text.strip() if name_tag else "Unknown"
                
                cone_html = str(cone)
                rarity = 5 if 'rarity-5' in cone_html or 'rar-5' in cone_html else 4
                
                cone_data = {
                    'name': name,
                    'rarity': rarity
                }
                
                if is_five_star or rarity == 5:
                    featured_5star_cone.append(cone_data)
                else:
                    featured_4star_cone.append(cone_data)
        
        return featured_5star_cone, featured_4star_cone
    
    def classify_banner_type(self, item, chars5, chars4, cones5, cones4) -> str:
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
                    
                    if not any(warp in banner_name for warp in self.real_warps):
                        skipped_count += 1
                        continue
                    
                    banner_id = re.sub(r'[^a-zA-Z0-9]', '', banner_name.lower())
                    
                    time_tag = item.find('span', class_='time')
                    time_remaining = time_tag.text.strip() if time_tag else "Tiempo desconocido"
                    
                    duration_tag = item.find('p', class_='duration')
                    duration_text = duration_tag.text.strip() if duration_tag else ""
                    
                    start_date, end_date = self.parse_date_from_duration(duration_text)
                    
                    featured_5star_char, featured_4star_char = self.extract_characters(item)
                    featured_5star_cone, featured_4star_cone = self.extract_light_cones(item)
                    
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
                    
                    logger.info(f"✅ Warp {warp_count}: {banner_name}")
                    logger.info(f"   - Personajes 5★: {[c['name'] for c in featured_5star_char]}")
                    
                except Exception as e:
                    logger.error(f"Error procesando banner: {e}")
                    continue
            
            logger.info(f"✅ WARPS REALES ENCONTRADOS: {len(banners)}")
            logger.info(f"📊 Items que no son warps: {skipped_count}")
            return banners
            
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return []
    
    def get_endgame_content(self):
        """Obtiene todo el contenido End Game"""
        try:
            response = self.session.get(self.url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            all_items = soup.find_all('div', class_='accordion-item')
            
            endgame_list = []
            
            for item in all_items:
                if self.is_endgame_content(item):
                    content = self.extract_endgame_content(item)
                    if content:
                        endgame_list.append(content)
                        logger.info(f"✅ End Game encontrado: {content.name} - Versión: {content.version} - Tiempo: {content.time_remaining}")
            
            return endgame_list
            
        except Exception as e:
            logger.error(f"Error obteniendo End Game content: {e}")
            return []

# ============================================
# INSTANCIAS GLOBALES
# ============================================
scraper = BannerScraper()
forum_manager = ForumManager()

# ============================================
# FUNCIONES AUXILIARES
# ============================================
def get_path_emoji(path: str) -> str:
    """Devuelve el emoji de la Vía"""
    path_emojis = {
        'Abundance': '🌿',
        'Destruction': '💥',
        'Erudition': '📚',
        'Harmony': '🎵',
        'Nihility': '🌑',
        'Preservation': '🛡️',
        'The Hunt': '🏹',
        'Remembrance': '📖',
        'Elation': '🎭',
        'Unknown': '❓'
    }
    return path_emojis.get(path, '❓')

def get_element_emoji(element: str) -> str:
    """Devuelve el emoji del elemento"""
    element_emojis = {
        'Physical': '💪',
        'Fire': '🔥',
        'Ice': '❄️',
        'Lightning': '⚡',
        'Wind': '💨',
        'Quantum': '⚛️',
        'Imaginary': '✨',
        'Unknown': '❓'
    }
    return element_emojis.get(element, '❓')

async def create_character_post(forum_channel, character_name, character_info, banner_info, status):
    """Crea una publicación en el foro para un personaje 5★"""
    
    status_emoji = "🔴" if status == "actual" else "🟡"
    
    # Título: nombre del personaje
    thread_name = f"{status_emoji} {character_name}"
    
    # Crear la publicación con la imagen como contenido principal
    thread = await forum_channel.create_thread(
        name=thread_name,
        content=character_info['image'],
        auto_archive_duration=10080
    )
    
    thread_obj = thread[0] if isinstance(thread, tuple) else thread
    
    # Formatear la información del personaje incluyendo la duración
    duration_clean = banner_info['duration_text'].replace('Event Duration', '').strip()
    
    info_text = (
        f"**{character_name}**\n"
        f"{get_path_emoji(character_info['path'])} {character_info['path']}\n"
        f"{get_element_emoji(character_info['element'])} {character_info['element']}\n"
        f"⏳ **Duración:** {duration_clean}"
    )
    
    await thread_obj.send(info_text)
    
    logger.info(f"✅ Publicación creada para personaje 5★: {character_name}")
    
    return thread_obj

async def create_endgame_post(forum_channel, endgame_content):
    """Crea una publicación en el foro para contenido End Game con tiempo visible en la tarjeta"""
    
    # Extraer el tiempo correcto del countdown
    time_remaining = endgame_content.time_remaining
    
    # Título: nombre del modo + versión + tiempo (visible desde fuera)
    thread_name = f"⚔️ {endgame_content.content_type} {endgame_content.version} - {time_remaining}"
    
    # Crear un embed con la imagen y el tiempo
    embed = discord.Embed(
        title=f"{endgame_content.content_type} {endgame_content.version}",
        description=f"⏳ **Tiempo restante:** {time_remaining}",
        color=discord.Color.orange()
    )
    
    # Aquí pondrás la URL de tu imagen (cámbiala por la que quieras usar)
    # Puedes usar imágenes diferentes para cada modo
    # IMPORTANTE: Reemplaza estas URLs con las imágenes que quieras usar
    image_urls = {
        'Memory of Chaos': 'https://ejemplo.com/moc.jpg',
        'Pure Fiction': 'https://ejemplo.com/pf.jpg', 
        'Apocalyptic Shadow': 'https://ejemplo.com/as.jpg'
    }
    
    image_url = image_urls.get(endgame_content.content_type, 'https://ejemplo.com/default.jpg')
    embed.set_image(url=image_url)
    embed.set_footer(text="Actualización diaria automática")
    
    # Crear la publicación con el embed como contenido principal
    thread = await forum_channel.create_thread(
        name=thread_name,
        embed=embed,
        auto_archive_duration=10080
    )
    
    thread_obj = thread[0] if isinstance(thread, tuple) else thread
    
    logger.info(f"✅ Publicación creada para End Game: {endgame_content.content_type} {endgame_content.version} - {time_remaining}")
    
    return thread_obj

async def update_forum_posts():
    """Actualiza las publicaciones del foro por personaje (solo 5★) y End Game"""
    
    all_banners = scraper.get_banners()
    all_endgame = scraper.get_endgame_content()
    
    now = datetime.now()
    
    # Procesar cada canal por separado
    if TARGET_FORUM_ACTUAL:
        await update_character_posts(TARGET_FORUM_ACTUAL, all_banners, now, "actual")
    
    if TARGET_FORUM_PROXIMO:
        await update_character_posts(TARGET_FORUM_PROXIMO, all_banners, now, "proximo")
    
    if TARGET_FORUM_ENDGAME:
        await update_endgame_posts(TARGET_FORUM_ENDGAME, all_endgame)

async def update_character_posts(channel_id, banners, now, status):
    """Actualiza las publicaciones de personajes 5★ en un canal específico"""
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"❌ No se encontró el canal {channel_id}")
        return
    
    if not isinstance(channel, discord.ForumChannel):
        logger.error(f"❌ El canal {channel_id} no es un foro")
        return
    
    try:
        # Recopilar todos los personajes 5★ de los banners con su información
        characters_to_post = []
        processed_names = set()  # Para evitar duplicados
        
        for banner in banners:
            # Determinar si el banner es actual o próximo
            is_current = False
            if banner.end_date and banner.end_date > now:
                if banner.start_date and banner.start_date <= now:
                    is_current = True
                elif banner.start_date and banner.start_date > now:
                    is_current = False
                else:
                    is_current = True
            
            # Solo procesar banners del estado correspondiente
            if (status == "actual" and not is_current) or (status == "proximo" and is_current):
                continue
            
            # Procesar personajes 5★
            for char_data in banner.featured_5star_char:
                char_name = char_data['name']
                
                # Evitar duplicados
                if char_name in processed_names:
                    continue
                
                # Obtener información completa del personaje
                char_info = get_character_info(char_name)
                
                if char_info:
                    characters_to_post.append({
                        'name': char_name,
                        'info': char_info,
                        'banner_info': {
                            'time_remaining': banner.time_remaining,
                            'duration_text': banner.duration_text
                        }
                    })
                    processed_names.add(char_name)
                    logger.info(f"📌 Personaje 5★ encontrado: {char_name}")
                else:
                    logger.info(f"⏩ {char_name} no es 5★ o no está en la base de datos")
        
        logger.info(f"Foro {channel.name}: {len(characters_to_post)} personajes 5★ únicos para publicar")
        
        # Obtener hilos activos
        active_threads = []
        active_threads.extend(channel.threads)
        async for thread in channel.archived_threads(limit=100):
            active_threads.append(thread)
        
        # Mapear hilos existentes por nombre de personaje
        existing_posts = {}
        for thread in active_threads:
            for char_data in characters_to_post:
                if char_data['name'] in thread.name:
                    char_id = re.sub(r'[^a-zA-Z0-9]', '', char_data['name'].lower())
                    existing_posts[char_id] = thread
                    break
        
        # Crear nuevas publicaciones para personajes que no existen
        for char_data in characters_to_post:
            char_name = char_data['name']
            char_id = re.sub(r'[^a-zA-Z0-9]', '', char_name.lower())
            
            if char_id in existing_posts:
                logger.info(f"⏩ Hilo ya existe para: {char_name}")
            else:
                # Crear nueva publicación
                try:
                    thread = await create_character_post(
                        channel, 
                        char_name, 
                        char_data['info'], 
                        char_data['banner_info'], 
                        status
                    )
                    if thread:
                        forum_manager.set_post_id(channel_id, char_id, thread.id)
                        logger.info(f"✅ Publicación creada: {char_name}")
                except Exception as e:
                    logger.error(f"Error creando publicación {char_name}: {e}")
            
            await asyncio.sleep(1)
        
        logger.info(f"✅ Foro {channel.name} actualizado con {len(characters_to_post)} personajes 5★")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando foro {channel.name}: {e}")

async def update_endgame_posts(channel_id, endgame_list):
    """Actualiza las publicaciones de End Game en un canal específico"""
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"❌ No se encontró el canal {channel_id}")
        return
    
    if not isinstance(channel, discord.ForumChannel):
        logger.error(f"❌ El canal {channel_id} no es un foro")
        return
    
    try:
        logger.info(f"Foro End Game: {len(endgame_list)} modos encontrados")
        
        # Obtener hilos activos
        active_threads = []
        active_threads.extend(channel.threads)
        async for thread in channel.archived_threads(limit=100):
            active_threads.append(thread)
        
        # Mapear hilos existentes por nombre del modo
        existing_posts = {}
        for thread in active_threads:
            for content in endgame_list:
                content_id = f"{content.content_type}_{content.version}".lower().replace(' ', '_')
                if content.content_type in thread.name:
                    existing_posts[content_id] = thread
                    break
        
        # Crear o actualizar publicaciones
        for content in endgame_list:
            content_id = f"{content.content_type}_{content.version}".lower().replace(' ', '_')
            time_remaining = content.time_remaining
            
            if content_id in existing_posts:
                # Actualizar título y enviar mensaje de actualización
                thread = existing_posts[content_id]
                new_title = f"⚔️ {content.content_type} {content.version} - {time_remaining}"
                
                try:
                    if thread.name != new_title:
                        await thread.edit(name=new_title)
                    
                    # Enviar mensaje de actualización
                    await thread.send(f"🔄 **Actualización**\n⏳ Tiempo restante: {time_remaining}")
                    logger.info(f"✅ Hilo actualizado: {content.content_type} {content.version}")
                except Exception as e:
                    logger.error(f"Error actualizando hilo: {e}")
            else:
                # Crear nueva publicación
                try:
                    thread = await create_endgame_post(channel, content)
                    forum_manager.set_post_id(channel_id, content_id, thread.id)
                    logger.info(f"✅ Publicación creada: {content.content_type} {content.version}")
                except Exception as e:
                    logger.error(f"Error creando publicación: {e}")
            
            await asyncio.sleep(1)
        
        logger.info(f"✅ Foro End Game actualizado con {len(endgame_list)} modos")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando foro End Game: {e}")

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 60)
logger.info("🚀 INICIANDO BOT DE HONKAI STAR RAIL - CON END GAME")
logger.info("=" * 60)

TOKEN = os.environ.get('DISCORD_TOKEN')
FORUM_CHANNEL_ID_ACTUAL = os.environ.get('FORUM_CHANNEL_ACTUAL')
FORUM_CHANNEL_ID_PROXIMO = os.environ.get('FORUM_CHANNEL_PROXIMO')
FORUM_CHANNEL_ID_ENDGAME = os.environ.get('FORUM_CHANNEL_ENDGAME')

logger.info(f"🔑 DISCORD_TOKEN: {'✅ ENCONTRADO' if TOKEN else '❌ NO ENCONTRADO'}")
logger.info(f"📢 Canal FORO ACTUAL: {'✅ ' + FORUM_CHANNEL_ID_ACTUAL if FORUM_CHANNEL_ID_ACTUAL else '❌ NO CONFIGURADO'}")
logger.info(f"📢 Canal FORO PRÓXIMO: {'✅ ' + FORUM_CHANNEL_ID_PROXIMO if FORUM_CHANNEL_ID_PROXIMO else '❌ NO CONFIGURADO'}")
logger.info(f"📢 Canal FORO ENDGAME: {'✅ ' + FORUM_CHANNEL_ID_ENDGAME if FORUM_CHANNEL_ID_ENDGAME else '❌ NO CONFIGURADO'}")

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

TARGET_FORUM_ENDGAME = None
if FORUM_CHANNEL_ID_ENDGAME:
    try:
        TARGET_FORUM_ENDGAME = int(FORUM_CHANNEL_ID_ENDGAME.strip())
        logger.info(f"✅ Foro endgame: {TARGET_FORUM_ENDGAME}")
    except ValueError:
        logger.error(f"❌ FORUM_CHANNEL_ENDGAME no es válido: {FORUM_CHANNEL_ID_ENDGAME}")

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
            name="🔮 HSR | !personajes"
        )
    )
    
    if TARGET_FORUM_ACTUAL or TARGET_FORUM_PROXIMO or TARGET_FORUM_ENDGAME:
        daily_forum_posts.start()
        logger.info(f"📅 Tarea diaria iniciada")

@tasks.loop(hours=24)
async def daily_forum_posts():
    await update_forum_posts()

@daily_forum_posts.before_loop
async def before_daily_forum_posts():
    await bot.wait_until_ready()

@bot.command(name='personajes', aliases=['banners', 'warps', '5★'])
async def personajes_command(ctx):
    """Muestra los personajes 5★ en banner actualmente"""
    
    loading_msg = await ctx.send("🔮 **Escaneando personajes 5★ en banner...**")
    
    try:
        all_banners = scraper.get_banners()
        
        if not all_banners:
            await loading_msg.edit(content="❌ **No se encontraron personajes en banner.**")
            return
        
        now = datetime.now()
        personajes_actuales = []
        personajes_proximos = []
        processed_names = set()
        
        for banner in all_banners:
            is_current = False
            if banner.end_date and banner.end_date > now:
                if banner.start_date and banner.start_date <= now:
                    is_current = True
                elif banner.start_date and banner.start_date > now:
                    is_current = False
                else:
                    is_current = True
            
            target_list = personajes_actuales if is_current else personajes_proximos
            
            # Solo personajes 5★ y sin duplicados
            for char in banner.featured_5star_char:
                if char['name'] not in processed_names:
                    target_list.append({
                        'name': char['name'],
                        'time': banner.time_remaining
                    })
                    processed_names.add(char['name'])
        
        await loading_msg.delete()
        
        response = "## 📊 **Personajes 5★ en Banner**\n\n"
        
        if personajes_actuales:
            response += "### 🔴 **ACTUALES**\n"
            for p in personajes_actuales:
                response += f"✨ **{p['name']}** - {p['time']}\n"
            response += "\n"
        
        if personajes_proximos:
            response += "### 🟡 **PRÓXIMOS**\n"
            for p in personajes_proximos:
                response += f"✨ **{p['name']}** - {p['time']}\n"
        
        if len(response) > 2000:
            parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error en comando personajes: {e}")
        await loading_msg.edit(content=f"❌ **Error:** {str(e)[:200]}")

@bot.command(name='endgame')
async def endgame_command(ctx):
    """Muestra el contenido End Game actual"""
    
    loading_msg = await ctx.send("⚔️ **Escaneando contenido End Game...**")
    
    try:
        endgame_list = scraper.get_endgame_content()
        
        if not endgame_list:
            await loading_msg.edit(content="❌ **No se encontró contenido End Game.**")
            return
        
        await loading_msg.delete()
        
        response = "## ⚔️ **Contenido End Game**\n\n"
        
        for content in endgame_list:
            response += f"### {content.content_type} {content.version}\n"
            response += f"⏳ **Tiempo restante:** {content.time_remaining}\n\n"
        
        if len(response) > 2000:
            parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error en comando endgame: {e}")
        await loading_msg.edit(content=f"❌ **Error:** {str(e)[:200]}")

@bot.command(name='refresh_forum')
@commands.has_permissions(administrator=True)
async def refresh_forum(ctx):
    await ctx.send("🔄 **Forzando actualización del foro...**")
    await update_forum_posts()

@bot.command(name='reset_forum')
@commands.has_permissions(administrator=True)
async def reset_forum(ctx, channel_type: str = None):
    if not channel_type or channel_type not in ['actual', 'proximo', 'endgame']:
        await ctx.send("❌ **Usa:** `!reset_forum actual`, `!reset_forum proximo` o `!reset_forum endgame`")
        return
    
    if channel_type == 'actual':
        channel_id = TARGET_FORUM_ACTUAL
    elif channel_type == 'proximo':
        channel_id = TARGET_FORUM_PROXIMO
    else:
        channel_id = TARGET_FORUM_ENDGAME
    
    if not channel_id:
        await ctx.send(f"❌ **Foro {channel_type} no configurado**")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send(f"❌ **No se encontró el foro**")
        return
    
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
    banners = scraper.get_banners()
    endgame = scraper.get_endgame_content()
    
    now = datetime.now()
    banners_actuales = 0
    banners_proximos = 0
    total_personajes_5star = 0
    personajes_set = set()
    
    for banner in banners:
        if banner.end_date and banner.end_date > now:
            if banner.start_date and banner.start_date <= now:
                banners_actuales += 1
            elif banner.start_date and banner.start_date > now:
                banners_proximos += 1
            else:
                banners_actuales += 1
        
        for char in banner.featured_5star_char:
            if char['name'] not in personajes_set:
                total_personajes_5star += 1
                personajes_set.add(char['name'])
    
    embed = discord.Embed(
        title="📊 **Estadísticas**",
        description="Resumen del juego",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🔴 Banners actuales", value=str(banners_actuales), inline=True)
    embed.add_field(name="🟡 Banners próximos", value=str(banners_proximos), inline=True)
    embed.add_field(name="✨ Personajes 5★ únicos", value=str(total_personajes_5star), inline=True)
    embed.add_field(name="⚔️ Modos End Game", value=str(len(endgame)), inline=True)
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Comando no encontrado.** Usa `!personajes` o `!endgame`.")
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

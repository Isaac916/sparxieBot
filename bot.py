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
    normalized_name = char['name'].lower().strip()
    CHARACTER_ICON_MAP[normalized_name] = char['image']
    CHARACTER_ICON_MAP[char['id'].lower()] = char['image']
    simple_name = re.sub(r'[^a-z0-9]', '', normalized_name)
    CHARACTER_ICON_MAP[simple_name] = char['image']

DEFAULT_IMAGE = "https://static.wikia.nocookie.net/houkai-star-rail/images/8/83/Site-logo.png"

def get_character_icon(character_name):
    """Obtiene el ícono de un personaje por su nombre"""
    if not character_name:
        return DEFAULT_IMAGE
    
    search_name = character_name.lower().strip()
    
    if search_name in CHARACTER_ICON_MAP:
        logger.info(f"✅ Ícono encontrado para {character_name}")
        return CHARACTER_ICON_MAP[search_name]
    
    for key, url in CHARACTER_ICON_MAP.items():
        if search_name in key or key in search_name:
            logger.info(f"✅ Ícono encontrado (coincidencia parcial) para {character_name}: {key}")
            return url
    
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
    
    def get_post_id(self, channel_id, character_id):
        key = f"{channel_id}_{character_id}"
        return self.posts.get(key)
    
    def set_post_id(self, channel_id, character_id, thread_id):
        key = f"{channel_id}_{character_id}"
        self.posts[key] = thread_id
        self.save_posts()
    
    def remove_post(self, channel_id, character_id):
        key = f"{channel_id}_{character_id}"
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
        
        self.element_emojis = {
            'Physical': '💪', 'Fire': '🔥', 'Ice': '❄️',
            'Lightning': '⚡', 'Wind': '💨', 'Quantum': '⚛️',
            'Imaginary': '✨'
        }
    
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
    
    def parse_character(self, card) -> dict:
        try:
            a_tag = card.find('a')
            name = "Unknown"
            char_key = ""
            
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href', '')
                char_key = href.split('/')[-1]
                name = char_key.replace('-', ' ').title()
            
            element = "Unknown"
            element_tag = card.find('span', class_='floating-element')
            if element_tag:
                element_img = element_tag.find('img')
                if element_img and element_img.get('alt'):
                    element = element_img.get('alt')
            
            card_html = str(card)
            rarity = 5 if 'rarity-5' in card_html or 'rar-5' in card_html else 4
            
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
        try:
            name_tag = cone_item.find('span', class_='hsr-set-name')
            name = name_tag.text.strip() if name_tag else "Unknown"
            
            cone_html = str(cone_item)
            rarity = 5 if 'rarity-5' in cone_html or 'rar-5' in cone_html else 4
            
            return {
                'name': name,
                'image': DEFAULT_IMAGE,
                'rarity': rarity
            }
        except Exception:
            return {
                'name': "Unknown Cone",
                'image': DEFAULT_IMAGE,
                'rarity': 4
            }
    
    def extract_characters(self, item):
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
    elements = {
        'Physical': '💪', 'Fire': '🔥', 'Ice': '❄️',
        'Lightning': '⚡', 'Wind': '💨', 'Quantum': '⚛️',
        'Imaginary': '✨', 'physical': '💪', 'fire': '🔥',
        'ice': '❄️', 'lightning': '⚡', 'wind': '💨',
        'quantum': '⚛️', 'imaginary': '✨'
    }
    return elements.get(element, elements.get(element.lower(), '🔮'))

async def create_character_post(forum_channel, character, banner_info, status):
    """Crea una publicación en el foro para un personaje específico"""
    
    status_emoji = "🔴" if status == "actual" else "🟡"
    
    # Título: nombre del personaje
    thread_name = f"{status_emoji} {character['name']}"
    
    # Contenido: solo tiempo y duración
    content = f"""**⏳ Tiempo restante:** {banner_info['time_remaining']}
**📅 Duración:** {banner_info['duration_text'].replace('Event Duration', '')}"""
    
    # Crear la publicación con la imagen como banner
    thread = await forum_channel.create_thread(
        name=thread_name,
        content=content,
        auto_archive_duration=10080
    )
    
    thread_obj = thread[0] if isinstance(thread, tuple) else thread
    
    # Establecer la imagen del personaje como la imagen de la publicación
    # Nota: Discord no permite establecer imagen de publicación directamente,
    # pero podemos enviarla como mensaje inicial
    try:
        # Enviar la imagen como mensaje inicial
        await thread_obj.send(character['image'])
        logger.info(f"✅ Imagen enviada para {character['name']}")
    except Exception as e:
        logger.error(f"Error enviando imagen: {e}")
    
    logger.info(f"✅ Publicación creada para personaje: {character['name']}")
    
    return thread_obj

async def update_forum_posts():
    """Actualiza las publicaciones del foro por personaje"""
    
    all_banners = scraper.get_banners()
    
    if not all_banners:
        logger.warning("No se encontraron banners para actualizar")
        return
    
    now = datetime.now()
    
    # Procesar cada canal por separado
    if TARGET_FORUM_ACTUAL:
        await update_character_posts(TARGET_FORUM_ACTUAL, all_banners, now, "actual")
    
    if TARGET_FORUM_PROXIMO:
        await update_character_posts(TARGET_FORUM_PROXIMO, all_banners, now, "proximo")

async def update_character_posts(channel_id, banners, now, status):
    """Actualiza las publicaciones de personajes en un canal específico"""
    
    channel = bot.get_channel(channel_id)
    if not channel:
        logger.error(f"❌ No se encontró el canal {channel_id}")
        return
    
    if not isinstance(channel, discord.ForumChannel):
        logger.error(f"❌ El canal {channel_id} no es un foro")
        return
    
    try:
        # Recopilar todos los personajes de los banners con su información
        characters_with_banner = []
        
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
            
            banner_info = {
                'time_remaining': banner.time_remaining,
                'duration_text': banner.duration_text
            }
            
            # Añadir personajes 5★
            for char in banner.featured_5star_char:
                characters_with_banner.append({
                    'character': char,
                    'banner_info': banner_info
                })
            
            # Añadir personajes 4★
            for char in banner.featured_4star_char:
                characters_with_banner.append({
                    'character': char,
                    'banner_info': banner_info
                })
        
        logger.info(f"Foro {channel.name}: {len(characters_with_banner)} personajes encontrados")
        
        # Obtener hilos activos
        active_threads = []
        active_threads.extend(channel.threads)
        async for thread in channel.archived_threads(limit=100):
            active_threads.append(thread)
        
        # Mapear hilos existentes por nombre de personaje
        existing_posts = {}
        for thread in active_threads:
            for item in characters_with_banner:
                if item['character']['name'] in thread.name:
                    # Crear ID único para el personaje
                    char_id = re.sub(r'[^a-zA-Z0-9]', '', item['character']['name'].lower())
                    existing_posts[char_id] = thread
                    break
        
        # Crear o actualizar publicaciones
        for item in characters_with_banner:
            char = item['character']
            banner_info = item['banner_info']
            
            char_id = re.sub(r'[^a-zA-Z0-9]', '', char['name'].lower())
            
            if char_id in existing_posts:
                # Actualizar contenido del hilo
                thread = existing_posts[char_id]
                
                new_content = f"""**⏳ Tiempo restante:** {banner_info['time_remaining']}
**📅 Duración:** {banner_info['duration_text'].replace('Event Duration', '')}"""
                
                try:
                    # Enviar mensaje de actualización
                    await thread.send(f"🔄 **Actualización**\n{new_content}")
                    logger.info(f"✅ Hilo actualizado: {char['name']}")
                except Exception as e:
                    logger.error(f"Error actualizando hilo {char['name']}: {e}")
            else:
                # Crear nueva publicación
                try:
                    thread = await create_character_post(channel, char, banner_info, status)
                    forum_manager.set_post_id(channel_id, char_id, thread.id)
                    logger.info(f"✅ Publicación creada: {char['name']}")
                except Exception as e:
                    logger.error(f"Error creando publicación {char['name']}: {e}")
            
            await asyncio.sleep(1)
        
        logger.info(f"✅ Foro {channel.name} actualizado con {len(characters_with_banner)} personajes")
        
    except Exception as e:
        logger.error(f"❌ Error actualizando foro {channel.name}: {e}")

# ============================================
# VARIABLES DE ENTORNO
# ============================================
logger.info("=" * 60)
logger.info("🚀 INICIANDO BOT DE HONKAI STAR RAIL - FORO POR PERSONAJE")
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
            name="🔮 Personajes en banner | !personajes"
        )
    )
    
    if TARGET_FORUM_ACTUAL or TARGET_FORUM_PROXIMO:
        daily_forum_posts.start()
        logger.info(f"📅 Tarea diaria iniciada")

@tasks.loop(hours=24)
async def daily_forum_posts():
    await update_forum_posts()

@daily_forum_posts.before_loop
async def before_daily_forum_posts():
    await bot.wait_until_ready()

@bot.command(name='personajes', aliases=['banners', 'warps'])
async def personajes_command(ctx):
    """Muestra los personajes en banner actualmente"""
    
    loading_msg = await ctx.send("🔮 **Escaneando personajes en banner...**")
    
    try:
        all_banners = scraper.get_banners()
        
        if not all_banners:
            await loading_msg.edit(content="❌ **No se encontraron personajes en banner.**")
            return
        
        now = datetime.now()
        personajes_actuales = []
        personajes_proximos = []
        
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
            
            for char in banner.featured_5star_char + banner.featured_4star_char:
                target_list.append({
                    'name': char['name'],
                    'time': banner.time_remaining,
                    'type': '★5' if char['rarity'] == 5 else '★4'
                })
        
        await loading_msg.delete()
        
        response = "## 📊 **Personajes en Banner**\n\n"
        
        if personajes_actuales:
            response += "### 🔴 **ACTUALES**\n"
            for p in personajes_actuales:
                response += f"{p['type']} **{p['name']}** - {p['time']}\n"
            response += "\n"
        
        if personajes_proximos:
            response += "### 🟡 **PRÓXIMOS**\n"
            for p in personajes_proximos:
                response += f"{p['type']} **{p['name']}** - {p['time']}\n"
        
        if len(response) > 2000:
            parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(response)
        
    except Exception as e:
        logger.error(f"Error en comando personajes: {e}")
        await loading_msg.edit(content=f"❌ **Error:** {str(e)[:200]}")

@bot.command(name='refresh_forum')
@commands.has_permissions(administrator=True)
async def refresh_forum(ctx):
    await ctx.send("🔄 **Forzando actualización del foro...**")
    await update_forum_posts()

@bot.command(name='reset_forum')
@commands.has_permissions(administrator=True)
async def reset_forum(ctx, channel_type: str = None):
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
    
    now = datetime.now()
    banners_actuales = 0
    banners_proximos = 0
    total_personajes = 0
    
    for banner in banners:
        if banner.end_date and banner.end_date > now:
            if banner.start_date and banner.start_date <= now:
                banners_actuales += 1
            elif banner.start_date and banner.start_date > now:
                banners_proximos += 1
            else:
                banners_actuales += 1
        
        total_personajes += len(banner.featured_5star_char) + len(banner.featured_4star_char)
    
    embed = discord.Embed(
        title="📊 **Estadísticas**",
        description="Resumen de personajes en banner",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🔴 Banners actuales", value=str(banners_actuales), inline=True)
    embed.add_field(name="🟡 Banners próximos", value=str(banners_proximos), inline=True)
    embed.add_field(name="👥 Personajes totales", value=str(total_personajes), inline=True)
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Comando no encontrado.** Usa `!personajes` para ver los personajes en banner.")
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

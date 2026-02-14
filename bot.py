def extract_endgame_content(self, item):
    """Extrae información del contenido End Game con tiempo correcto"""
    name_tag = item.find('div', class_='event-name')
    name = name_tag.text.strip() if name_tag else ""
    
    # Extraer versión (lo que está entre paréntesis)
    version_match = re.search(r'\(([^)]+)\)', name)
    version = version_match.group(1) if version_match else ""
    
    # Extraer tiempo restante del countdown - ¡ESTA ES LA PARTE CLAVE!
    time_tag = item.find('span', class_='time')
    time_remaining = time_tag.text.strip() if time_tag else "Tiempo desconocido"
    
    # Limpiar el tiempo (a veces viene con espacios extras)
    time_remaining = re.sub(r'\s+', ' ', time_remaining).strip()
    
    # Ajuste de zona horaria: -2 días y 5 horas para End Game
    time_offset = relativedelta(days=-2, hours=-5)
    
    # Intentar parsear el tiempo restante si es necesario
    # Si contiene una fecha, aplicar el offset
    try:
        # Buscar patrón de fecha en time_remaining
        date_pattern = r'(\d{4}/\d{2}/\d{2}(?:\s+\d{2}:\d{2})?)'
        date_match = re.search(date_pattern, time_remaining)
        if date_match:
            parsed_date = parser.parse(date_match.group(1), fuzzy=True)
            adjusted_date = parsed_date + time_offset
            # Reemplazar la fecha original con la ajustada en el texto
            time_remaining = time_remaining.replace(date_match.group(1), adjusted_date.strftime('%Y/%m/%d %H:%M'))
    except:
        pass
    
    # Determinar el tipo
    content_type = ""
    for mode in self.endgame_modes:
        if mode in name:
            content_type = mode
            break
    
    logger.info(f"⏱️ Tiempo extraído para {content_type}: {time_remaining}")
    
    return EndgameContent(name, version, time_remaining, content_type)

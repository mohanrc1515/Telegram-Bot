import re

# Define patterns for extracting metadata
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)')
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)')
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d+)\s*[)\]>}]?)')
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
patternX = re.compile(r'(\d+)')

# Quality Patterns 
pattern5 = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)\]>}]?', re.IGNORECASE)
pattern11 = re.compile(r'[([<{]?\s*8k\s*[)\]>}]?', re.IGNORECASE) # Added 8K support
pattern12 = re.compile(r'[([<{]?\s*UHD\s*[)\]>}]?|\bUHD\b', re.IGNORECASE) # Added UHD support
pattern13 = re.compile(r'[([<{]?\s*HQ\s*[)\]>}]?|\bHQ\b', re.IGNORECASE) # Added HQ support
pattern14 = re.compile(r'[([<{]?\s*FHD\s*[)\]>}]?|\bFHD\b', re.IGNORECASE) # Added FHD support

# Season Patterns 
pattern11 = re.compile(r'S(\d+)(?:Season|S)(\d+)')
pattern12 = re.compile(r'S(\d+)\s*(?:Season|S|-\s*S)(\d+)')
pattern13 = re.compile(r'(?:[([<{]?\s*(?:Season|S)\s*(\d+)\s*[)\]>}]?)')
pattern13_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern14 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
patterny = re.compile(r'(\d+)')

# Audio Language Patterns
pattern_lang1 = re.compile(r'\b(?:Dual|Dub|Sub)\b', re.IGNORECASE)
pattern_lang2 = re.compile(r'\b(?:Hindi|Hin|English|Eng|Tamil|Tam|Telugu|Tel|Russian|Rus|Indonesian|Ind|Malayalam|Mal|Urdu|Urd|Spanish|Spa|French|Fre|German|Ger|Japanese|Jpn|Korean|Kor|Italian|Ita|Chinese|Chi|Portuguese|Por|Jap)\b', re.IGNORECASE)
pattern_lang3 = re.compile(r'\b(?:Hin\s*-\s*Eng|Eng\s*-\s*Hin)\b', re.IGNORECASE)
pattern_lang4 = re.compile(r'\b(?:Dual\s*Audio|Multi\s*Audio)\b', re.IGNORECASE)
pattern_lang5 = re.compile(r'\b(?:HinEng|EngHin)\b', re.IGNORECASE)
pattern_lang_brackets = re.compile(r'[([{]\s*(?:Dual|Dub|Sub|Hindi|Hin|English|Eng|Tamil|Tam|Telugu|Tel|Russian|Rus|Indonesian|Ind|Malayalam|Mal|Urdu|Urd|Spanish|Spa|French|Fre|German|Ger|Japanese|Jpn|Korean|Kor|Italian|Ita|Chinese|Chi|Portuguese|Por|Jap)\s*[)\]}]', re.IGNORECASE)
pattern_lang_combined = re.compile(r'\b(?:Dual|Dub|Sub|Hindi|Hin|English|Eng|Tamil|Tam|Telugu|Tel|Russian|Rus|Indonesian|Ind|Malayalam|Mal|Urdu|Urd|Spanish|Spa|French|Fre|German|Ger|Japanese|Jpn|Korean|Kor|Italian|Ita|Chinese|Chi|Portuguese|Por|Jap)(?:\s*-\s*(?:Dual|Dub|Sub|Hindi|Hin|English|Eng|Tamil|Tam|Telugu|Tel|Russian|Rus|Indonesian|Ind|Malayalam|Mal|Urdu|Urd|Spanish|Spa|French|Fre|German|Ger|Japanese|Jpn|Korean|Kor|Italian|Ita|Chinese|Chi|Portuguese|Por|Jap))?\b', re.IGNORECASE)

# Define patterns for extracting chapter numbers
pattern_ch1 = re.compile(r'\b(?:C|Ch|Chap|Chapter)\s*(\d+(\.\d+)?)', re.IGNORECASE)
pattern_ch2 = re.compile(r'\b(?:C|Ch|Chap|Chapter)[^\d]*(\d+(\.\d+)?)', re.IGNORECASE)
pattern_ch3 = re.compile(r'(?:[([<{]?\s*(?:C|Ch|Chap|Chapter)\s*(\d+(\.\d+)?)\s*[)\]>}]?)', re.IGNORECASE)
pattern_ch4 = re.compile(r'(?:\s*-\s*(\d+(\.\d+)?)\s*)', re.IGNORECASE)

# Define patterns for extracting volume numbers
pattern_vol1 = re.compile(r'\b(?:V|Vol|Volume)\s*(\d+(\.\d+)?)', re.IGNORECASE)
pattern_vol2 = re.compile(r'\b(?:V|Vol|Volume)[^\d]*(\d+(\.\d+)?)', re.IGNORECASE)
pattern_vol3 = re.compile(r'(?:[([<{]?\s*(?:V|Vol|Volume)\s*(\d+(\.\d+)?)\s*[)\]>}]?)', re.IGNORECASE)
pattern_vol4 = re.compile(r'(?:\s*-\s*(\d+(\.\d+)?)\s*)', re.IGNORECASE)

def extract_volume_number(filename):
    match = re.search(pattern_vol1, filename)
    if match:
        return match.group(1)
    match = re.search(pattern_vol2, filename)
    if match:
        return match.group(1)
    match = re.search(pattern_vol3, filename)
    if match:
        return match.group(1)
    match = re.search(pattern_vol4, filename)
    if match:
        return match.group(1)
    return None
    

def extract_chapter_number(filename):
    match = re.search(pattern_ch1, filename)
    if match:
        return match.group(1)
    match = re.search(pattern_ch2, filename)
    if match:
        return match.group(1)
    match = re.search(pattern_ch3, filename)
    if match:
        return match.group(1)
    match = re.search(pattern_ch4, filename)
    if match:
        return match.group(1)
    return None

def extract_title(filename):
    # Remove any @username mentions and content within brackets
    filename = re.sub(r'@\S+', '', filename)
    filename = re.sub(r'\[.*?\]', '', filename)
    
    # Remove standalone 'S', 's', 'E' or followed by a number, also remove season-episode patterns like S01E01
    filename = re.sub(r'\b[SsE](\d+)\b', '', filename)
    filename = re.sub(r'\bS\d+\s*E\d+\b', '', filename)
    
    # Remove quality patterns like 1080p, 720p, 4K, etc.
    quality_patterns = [r'\b\d{3,4}[^\dp]*p\b', r'\b4k\b', r'\b2k\b', r'\b8k\b', r'\bHQ\b', r'\bHD\b', r'\bFHD\b', r'\bUHD\b']
    for pattern in quality_patterns:
        filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
    
    # Remove audio language patterns like Dual Audio, English, Hindi, etc.
    audio_patterns = [
        r'\b(?:Dual|Dub|Sub)\b',
        r'\b(?:Hindi|Hin|English|Eng|Tamil|Tam|Telugu|Tel|Russian|Rus|Indonesian|Ind|Malayalam|Mal|Urdu|Urd|Spanish|Spa|French|Fre|German|Ger|Japanese|Jpn|Korean|Kor|Italian|Ita|Chinese|Chi|Portuguese|Por|Jap)\b',
        r'\b(?:Hin\s*-\s*Eng|Eng\s*-\s*Hin)\b',
        r'\b(?:Dual\s*Audio|Multi\s*Audio)\b',
        r'\b(?:HinEng|EngHin)\b'
    ]
    for pattern in audio_patterns:
        filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
    
    # Remove chapter and volume indicators
    chapter_volume_patterns = [
        r'\b(?:chapter|chap|ch|volume|vol|v|c)\b'
    ]
    for pattern in chapter_volume_patterns:
        filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
    
    # Remove any remaining digits
    filename = re.sub(r'\d+', '', filename)
    
    # Remove special characters except for underscores and spaces
    filename = re.sub(r'[^\w\s_]', '', filename)
    
    # Clean up extra spaces and return the result
    filename = ' '.join(filename.split()).strip() 
    return filename
    

def extract_quality(filename):
    match5 = re.search(pattern5, filename)
    if match5:
        return match5.group(1) or match5.group(2)
    match6 = re.search(pattern6, filename)
    if match6:
        return "4k"
    match7 = re.search(pattern7, filename)
    if match7:
        return "2k"
    match8 = re.search(pattern8, filename)
    if match8:
        return "HdRip"
    match9 = re.search(pattern9, filename)
    if match9:
        return "4kX264"
    match10 = re.search(pattern10, filename)
    if match10:
        return "4kx265"
    match11 = re.search(pattern11, filename) # Added 8K support
    if match11:
        return "8k"
    match12 = re.search(pattern12, filename) # Added UHD support
    if match12:
        return "UHD"
    match13 = re.search(pattern13, filename) # Added HQ support
    if match13:
        return "HQ"
    match14 = re.search(pattern14, filename) # Added FHD support
    if match14:
        return "FHD"
    return "Unknown"

def extract_episode_number(filename):    
    match = re.search(pattern1, filename)
    if match:
        return match.group(2)
    match = re.search(pattern2, filename)
    if match:
        return match.group(2)
    match = re.search(pattern3, filename)
    if match:
        return match.group(1)
    match = re.search(pattern3_2, filename)
    if match:
        return match.group(1)
    match = re.search(pattern4, filename)
    if match:
        return match.group(2)
    matches = re.findall(patternX, filename)
    if matches:
        filtered_matches = [match for match in matches if not re.search(r'p$', match, re.IGNORECASE)]
        if filtered_matches:
            return filtered_matches[0]
    return None

def extract_season(filename):
    match11 = re.search(pattern11, filename)
    if match11:
        return match11.group(2)
    match12 = re.search(pattern12, filename)
    if match12:
        return match12.group(2)
    match13 = re.search(pattern13, filename)
    if match13:
        return match13.group(1)
    match13_2 = re.search(pattern13_2, filename)
    if match13_2:
        return match13_2.group(1)
    match14 = re.search(pattern14, filename)
    if match14:
        return match14.group(2)
    return None

def extract_audio_language(filename):
    match_lang1 = re.search(pattern_lang1, filename)
    if match_lang1:
        return match_lang1.group()
    match_lang2 = re.search(pattern_lang2, filename)
    if match_lang2:
        return match_lang2.group()
    match_lang3 = re.search(pattern_lang3, filename)
    if match_lang3:
        return match_lang3.group()
    match_lang4 = re.search(pattern_lang4, filename)
    if match_lang4:
        return match_lang4.group()
    match_lang5 = re.search(pattern_lang5, filename)
    if match_lang5:
        return match_lang5.group()
    match_lang_brackets = re.search(pattern_lang_brackets, filename)
    if match_lang_brackets:
        return match_lang_brackets.group()
    match_lang_combined = re.search(pattern_lang_combined, filename)
    if match_lang_combined:
        return match_lang_combined.group()
    return "Unknown"
    

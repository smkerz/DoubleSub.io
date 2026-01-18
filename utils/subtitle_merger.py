"""
Logique de fusion de sous-titres
Réutilise le code du plugin Emby
"""

import re
from datetime import timedelta


class SubtitleCue:
    """Représente un sous-titre"""

    def __init__(self, index, start, end, text):
        self.index = index
        self.start = start  # timedelta
        self.end = end  # timedelta
        self.text = text.strip()

    def __repr__(self):
        return f"<Cue {self.index}: {self.start} -> {self.end}>"


class SubtitleMerger:
    """Fusionne deux fichiers SRT en dual-langue"""

    def merge(self, srt1_path, srt2_path, output_path, mode='all', tolerance_ms=700,
              offset1_ms=0, offset2_ms=0, color1=None, color2=None):
        """
        Fusionne deux fichiers SRT

        Args:
            srt1_path: Chemin du premier SRT (haut)
            srt2_path: Chemin du deuxième SRT (bas)
            output_path: Chemin du fichier de sortie
            mode: 'all', 'overlapping', ou 'primary'
            tolerance_ms: Tolérance pour détecter les chevauchements (ms)
            offset1_ms: Décalage en ms pour le premier SRT
            offset2_ms: Décalage en ms pour le deuxième SRT
            color1: Couleur HTML pour le premier SRT (ex: '#FFFFFF')
            color2: Couleur HTML pour le deuxième SRT (ex: '#FFFF00')

        Returns:
            dict avec 'success', 'cue_count', 'preview', optionnellement 'error'
        """
        try:
            # Charger les sous-titres
            cues1 = self.parse_srt(srt1_path)
            cues2 = self.parse_srt(srt2_path)

            # Appliquer les offsets
            if offset1_ms != 0:
                offset1 = timedelta(milliseconds=offset1_ms)
                for cue in cues1:
                    cue.start = max(timedelta(0), cue.start + offset1)
                    cue.end = max(timedelta(0), cue.end + offset1)

            if offset2_ms != 0:
                offset2 = timedelta(milliseconds=offset2_ms)
                for cue in cues2:
                    cue.start = max(timedelta(0), cue.start + offset2)
                    cue.end = max(timedelta(0), cue.end + offset2)

            # Stocker les couleurs pour l'utilisation dans merge
            self.color1 = color1
            self.color2 = color2

            if not cues1 or not cues2:
                return {
                    'success': False,
                    'error': 'Impossible de parser les fichiers SRT'
                }

            # Fusionner selon le mode
            if mode == 'all':
                merged = self.merge_all(cues1, cues2, tolerance_ms)
            elif mode == 'overlapping':
                merged = self.merge_overlapping(cues1, cues2, tolerance_ms)
            else:  # primary
                merged = self.merge_primary(cues1, cues2, tolerance_ms)

            # Écrire le résultat
            self.write_srt(merged, output_path)

            # Générer un aperçu (10 premiers sous-titres)
            preview = []
            for cue in merged[:10]:
                preview.append({
                    'index': cue.index,
                    'start': self.format_timestamp(cue.start),
                    'end': self.format_timestamp(cue.end),
                    'text': cue.text
                })

            return {
                'success': True,
                'cue_count': len(merged),
                'preview': preview
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def parse_srt(self, filepath):
        """Parse un fichier SRT"""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Essayer avec d'autres encodages
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except:
                    continue
            else:
                raise Exception(f"Impossible de lire le fichier {filepath}")

        cues = []
        # Pattern SRT: numéro, timing, texte (peut être multiligne)
        pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\n\n|\n*$)'

        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            index = int(match.group(1))
            start = self.parse_timestamp(match.group(2))
            end = self.parse_timestamp(match.group(3))
            text = match.group(4).strip()

            if start and end and text:
                cues.append(SubtitleCue(index, start, end, text))

        return cues

    def parse_timestamp(self, timestamp):
        """Parse un timestamp SRT (HH:MM:SS,mmm)"""
        try:
            # Format: 00:01:23,456
            time_part, ms_part = timestamp.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)

            return timedelta(hours=h, minutes=m, seconds=s, milliseconds=ms)
        except:
            return None

    def format_timestamp(self, td):
        """Formate un timedelta en timestamp SRT"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = td.microseconds // 1000

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def apply_color(self, text, color):
        """Applique une couleur HTML au texte (format SRT avec balises font)"""
        if color:
            return f'<font color="{color}">{text}</font>'
        return text

    def merge_all(self, cues1, cues2, tolerance_ms):
        """Fusionne tous les sous-titres"""
        tolerance = timedelta(milliseconds=tolerance_ms)
        merged = []
        i, j = 0, 0

        while i < len(cues1) or j < len(cues2):
            c1 = cues1[i] if i < len(cues1) else None
            c2 = cues2[j] if j < len(cues2) else None

            if c1 and c2:
                # Vérifier le chevauchement
                overlap = self.check_overlap(c1, c2, tolerance)

                if overlap:
                    # Fusionner avec couleurs
                    text1 = self.apply_color(c1.text, self.color1)
                    text2 = self.apply_color(c2.text, self.color2)
                    merged_cue = SubtitleCue(
                        len(merged) + 1,
                        min(c1.start, c2.start),
                        max(c1.end, c2.end),
                        f"{text1}\n{text2}"
                    )
                    merged.append(merged_cue)
                    i += 1
                    j += 1
                elif c1.start < c2.start:
                    # c1 vient avant
                    text1 = self.apply_color(c1.text, self.color1)
                    merged.append(SubtitleCue(len(merged) + 1, c1.start, c1.end, text1))
                    i += 1
                else:
                    # c2 vient avant
                    text2 = self.apply_color(c2.text, self.color2)
                    merged.append(SubtitleCue(len(merged) + 1, c2.start, c2.end, text2))
                    j += 1
            elif c1:
                text1 = self.apply_color(c1.text, self.color1)
                merged.append(SubtitleCue(len(merged) + 1, c1.start, c1.end, text1))
                i += 1
            elif c2:
                text2 = self.apply_color(c2.text, self.color2)
                merged.append(SubtitleCue(len(merged) + 1, c2.start, c2.end, text2))
                j += 1

        return merged

    def merge_overlapping(self, cues1, cues2, tolerance_ms):
        """Ne garde que les sous-titres qui se chevauchent"""
        tolerance = timedelta(milliseconds=tolerance_ms)
        merged = []

        for c1 in cues1:
            for c2 in cues2:
                if self.check_overlap(c1, c2, tolerance):
                    text1 = self.apply_color(c1.text, self.color1)
                    text2 = self.apply_color(c2.text, self.color2)
                    merged_cue = SubtitleCue(
                        len(merged) + 1,
                        min(c1.start, c2.start),
                        max(c1.end, c2.end),
                        f"{text1}\n{text2}"
                    )
                    merged.append(merged_cue)
                    break

        return merged

    def merge_primary(self, cues1, cues2, tolerance_ms):
        """Donne priorité au premier sous-titre"""
        tolerance = timedelta(milliseconds=tolerance_ms)
        merged = []

        for c1 in cues1:
            # Chercher un match dans cues2
            matched = False
            for c2 in cues2:
                if self.check_overlap(c1, c2, tolerance):
                    text1 = self.apply_color(c1.text, self.color1)
                    text2 = self.apply_color(c2.text, self.color2)
                    merged_cue = SubtitleCue(
                        len(merged) + 1,
                        c1.start,
                        c1.end,
                        f"{text1}\n{text2}"
                    )
                    merged.append(merged_cue)
                    matched = True
                    break

            if not matched:
                # Pas de match, garder juste c1
                text1 = self.apply_color(c1.text, self.color1)
                merged.append(SubtitleCue(len(merged) + 1, c1.start, c1.end, text1))

        return merged

    def check_overlap(self, c1, c2, tolerance):
        """Vérifie si deux sous-titres se chevauchent (avec tolérance)"""
        # Ajouter la tolérance
        c1_start = c1.start - tolerance
        c1_end = c1.end + tolerance
        c2_start = c2.start - tolerance
        c2_end = c2.end + tolerance

        # Chevauchement si: (c1_start <= c2_end) ET (c2_start <= c1_end)
        return (c1_start <= c2_end) and (c2_start <= c1_end)

    def write_srt(self, cues, output_path):
        """Écrit les sous-titres au format SRT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, cue in enumerate(cues, 1):
                f.write(f"{i}\n")
                f.write(f"{self.format_timestamp(cue.start)} --> {self.format_timestamp(cue.end)}\n")
                f.write(f"{cue.text}\n\n")

import asyncio
import discord 
from discord import Intents
from discord.ext import commands
import os
import re
import json
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# Affichage de la version de Discord.py
print(discord.__version__)

# Déclaration de la variable "nom_commande"
nom_commande = None

# Initialisation des intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Création du bot avec les intents
bot = commands.Bot(command_prefix='!', description='Bot Discord pour envoyer des images', intents=intents)

# Ensemble des images déjà envoyées
deja_envoyees = set()

# Flag synchrone : une seule commande !image à la fois (évite race + doublons)
_image_command_running = False

# Chargement des commandes personnalisées depuis le fichier JSON
try:
    with open("commandes_personnalisees.json", "r") as fichier:
        commandes_personnalisees = json.load(fichier)
except FileNotFoundError:
    print("Le fichier commandes_personnalisees.json n'existe pas encore.")
    commandes_personnalisees = {}

# Evénement "on_ready"
@bot.event
async def on_ready():
    print('DIUFF bot est prêt!')

    # Chargement de la liste des images déjà envoyées
    try:
        with open("images_envoyees.txt", "r") as fichier:
            for filename in fichier:
                deja_envoyees.add(filename.strip())  # Supprimer les espaces éventuels
    except FileNotFoundError:
        print("Le fichier images_envoyees.txt n'existe pas encore.")

# Fonction de compression d'image
def compresser_image(filepath, max_size=8 * 1024 * 1024):
    """Compresse l'image pour qu'elle respecte la limite Discord (max_size en octets)."""
    try:
        with Image.open(filepath) as img:
            # Vérifier si l'image dépasse la taille maximale
            current_size = os.path.getsize(filepath)
            if current_size <= max_size:
                return filepath  # Pas besoin de compression

            # Créer le nom du fichier compressé
            file_name, file_ext = os.path.splitext(filepath)
            output_path = f"{file_name}_compressed.jpg"  # Toujours utiliser .jpg pour la sortie

            # Convertir en RGB si nécessaire
            if img.mode in ('RGBA', 'P'):
                # Créer un fond blanc
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # 3 est le canal alpha
                else:
                    background.paste(img)
                img = background

            # Réduire la qualité jusqu'à ce que la taille soit acceptable
            quality = 95
            img.save(output_path, "JPEG", quality=quality)
            current_size = os.path.getsize(output_path)
            
            while current_size > max_size and quality > 10:
                img.save(output_path, "JPEG", quality=quality)
                current_size = os.path.getsize(output_path)
                quality -= 5

            if current_size <= max_size:
                return output_path
            else:
                if os.path.exists(output_path):
                    os.remove(output_path)
                return None

    except Exception as e:
        print(f"Erreur lors de la compression de {filepath}: {str(e)}")
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        return None


def _parse_yyyymmdd_hhmmss(name):
    """Extrait date/heure au format compact YYYYMMDD puis optionnellement HHMMSS ou HHMM."""
    timestamps = []
    # Bloc 8 chiffres = YYYYMMDD
    for m in re.finditer(r'(?<!\d)(\d{8})(?!\d)', name):
        s = m.group(1)
        y, mo, d = int(s[0:4]), int(s[4:6]), int(s[6:8])
        if 1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
            try:
                hh, mm, ss = 0, 0, 0
                rest = name[m.end():]
                hm_match = re.match(r'[-_](\d{6})(?!\d)', rest)
                if hm_match:
                    t = hm_match.group(1)
                    hh, mm, ss = int(t[0:2]), int(t[2:4]), int(t[4:6])
                    if 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59:
                        pass
                    else:
                        hh, mm, ss = 0, 0, 0
                else:
                    hm_match = re.match(r'[-_](\d{4})(?!\d)', rest)
                    if hm_match:
                        t = hm_match.group(1)
                        hh, mm = int(t[0:2]), int(t[2:4])
                        if 0 <= hh <= 23 and 0 <= mm <= 59:
                            ss = 0
                        else:
                            hh, mm, ss = 0, 0, 0
                dt = datetime(y, mo, d, hh, mm, ss)
                timestamps.append(dt.timestamp())
            except ValueError:
                pass
    return timestamps


def _parse_triplet_dates(name):
    """Extrait dates des triplets avec séparateurs (-, _, .) ; tous ordres Y/M/D ; heure optionnelle."""
    timestamps = []
    for m in re.finditer(r'(\d{1,4})[-_.](\d{1,2})[-_.](\d{1,2})', name):
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        def is_year(x):
            return (1900 <= x <= 2100) or (0 <= x <= 99)
        def norm_year(x):
            if 0 <= x <= 99:
                return 2000 + x if x < 50 else 1900 + x
            return x
        hh, mm, ss = 0, 0, 0
        rest = name[m.end():]
        time_m = re.match(r'[-_.](\d{2})[-_.h]?(\d{2})(?:[-_.]?(\d{2}))?(?!\d)', rest)
        if time_m:
            hh = int(time_m.group(1))
            mm = int(time_m.group(2))
            ss = int(time_m.group(3)) if time_m.group(3) else 0
            if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
                hh, mm, ss = 0, 0, 0
        for y, mo, d in [
            (a, b, c), (a, c, b), (b, a, c), (b, c, a), (c, a, b), (c, b, a)
        ]:
            if not is_year(y):
                continue
            yr = norm_year(y) if y <= 99 else y
            if 1 <= mo <= 12 and 1 <= d <= 31:
                try:
                    dt = datetime(yr, mo, d, hh, mm, ss)
                    timestamps.append(dt.timestamp())
                    break
                except ValueError:
                    pass
    return timestamps


def _parse_yyyymmdd_underscore_hhmmss(name):
    """Format strict prefix_YYYYMMDD_HHMMSS (ex. ets2_20201106_185539_00) : priorité pour le tri."""
    timestamps = []
    for m in re.finditer(r'(?<!\d)(\d{8})_(\d{6})(?!\d)', name):
        try:
            s, t = m.group(1), m.group(2)
            y, mo, d = int(s[0:4]), int(s[4:6]), int(s[6:8])
            hh, mm, ss = int(t[0:2]), int(t[2:4]), int(t[4:6])
            if 1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
                if 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59:
                    timestamps.append(datetime(y, mo, d, hh, mm, ss).timestamp())
        except (ValueError, IndexError):
            pass
    return timestamps


def extraire_date_heure_nom(filename):
    """
    Extrait la date/heure la plus ancienne trouvée dans le nom de fichier (sans extension).
    Retourne un timestamp (float) ou None si aucune date valide.
    Ne lève jamais : en cas d’exception, retourne None.
    """
    try:
        name, _ = os.path.splitext(filename)
        if not name:
            return None
        all_ts = []
        all_ts.extend(_parse_yyyymmdd_underscore_hhmmss(name))
        all_ts.extend(_parse_yyyymmdd_hhmmss(name))
        all_ts.extend(_parse_triplet_dates(name))
        if not all_ts:
            return None
        return min(all_ts)
    except BaseException:
        return None


def extraire_date_heure_exif(filepath):
    """
    Extrait la date/heure EXIF (DateTimeOriginal, DateTime, etc.) du fichier image.
    Retourne un timestamp (float) ou None si absent/erreur.
    Ne tente pas getexif() sur les PNG (PIL charge tout le fichier et peut crasher le décodeur).
    """
    if filepath.lower().endswith(".png"):
        return None
    try:
        with Image.open(filepath) as img:
            exif = img.getexif()
            if not exif:
                return None
            # 36867 = DateTimeOriginal, 306 = DateTime, 36868 = DateTimeDigitized
            for tag in (36867, 306, 36868):
                val = exif.get(tag)
                if not val:
                    continue
                if isinstance(val, bytes):
                    val = val.decode('utf-8', errors='ignore')
                # Format EXIF typique: "YYYY:MM:DD HH:MM:SS"
                m = re.match(r'(\d{4}):(\d{2}):(\d{2})\s+(\d{2}):(\d{2}):(\d{2})', str(val).strip())
                if m:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    hh, mm, ss = int(m.group(4)), int(m.group(5)), int(m.group(6))
                    if 1900 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
                        if 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59:
                            dt = datetime(y, mo, d, hh, mm, ss)
                            return dt.timestamp()
            return None
    except BaseException:
        return None


def date_tri_fichier(filepath, filename):
    """
    Calcule la date de tri (la plus ancienne parmi création, modification, nom, EXIF).
    Retourne un float (timestamp).
    """
    ts_creation = os.path.getctime(filepath)
    ts_modification = os.path.getmtime(filepath)
    candidates = [ts_creation, ts_modification]
    ts_nom = extraire_date_heure_nom(filename)
    if ts_nom is not None:
        candidates.append(ts_nom)
    ts_exif = extraire_date_heure_exif(filepath)
    if ts_exif is not None:
        candidates.append(ts_exif)
    return min(candidates)


@bot.command()
async def image(ctx):
    global _image_command_running
    if _image_command_running:
        await ctx.send("⏳ Une commande !image est déjà en cours. Attendez la fin avant d'en lancer une autre.")
        return
    _image_command_running = True
    try:
        await _image_command_impl(ctx)
    finally:
        _image_command_running = False


async def _image_command_impl(ctx):
    commande = ctx.message.content.split(' ')[1]

    if commande not in commandes_personnalisees:
        await ctx.send(f"Commande inconnue : {commande}")
        return

    # Compter le nombre total d'images dans les dossiers
    total_images = 0
    for dossier in commandes_personnalisees[commande]:
        for root, _, files in os.walk(dossier):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    total_images += 1

    status_message = await ctx.send("🔍 Initialisation de la recherche...")

    # 1. Collecte : toutes les images non encore envoyées
    candidats = []
    for dossier in commandes_personnalisees[commande]:
        await status_message.edit(content=f"🔍 Recherche des images dans le dossier : `{dossier}` ...")
        for root, _, files in os.walk(dossier):
            for filename in files:
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    continue
                if filename.lower() in deja_envoyees:
                    continue
                filepath = os.path.join(root, filename)
                candidats.append((filepath, filename))

    # 2. Date de tri et tri : plus ancienne en premier, plus récente en dernier (en executor pour ne pas bloquer le heartbeat Discord)
    await status_message.edit(content="🔍 Tri des images (de la plus ancienne à la plus récente)...")
    def _compute_avec_date_tri():
        result = []
        for fp, fn in candidats:
            try:
                dt = date_tri_fichier(fp, fn)
                result.append((dt, fp, fn))
            except BaseException:
                try:
                    dt = min(os.path.getctime(fp), os.path.getmtime(fp))
                    result.append((dt, fp, fn))
                except BaseException:
                    result.append((0.0, fp, fn))
        return result
    loop = asyncio.get_event_loop()
    avec_date_tri = await loop.run_in_executor(None, _compute_avec_date_tri)
    avec_date_tri.sort(key=lambda x: (x[0], x[2]))

    nb_images_envoyees = 0
    for date_tri, filepath, filename in avec_date_tri:
        filename_lower = filename.lower()
        compressed_path = compresser_image(filepath)

        if compressed_path is None:
            await ctx.send(f"❌ Impossible de compresser l'image : {filepath}")
            continue

        try:
            await ctx.send(file=discord.File(compressed_path))
            deja_envoyees.add(filename_lower)
            with open("images_envoyees.txt", "a") as fichier:
                fichier.write(filename_lower + "\n")
            if compressed_path != filepath and os.path.exists(compressed_path):
                os.remove(compressed_path)
                print(f"Le fichier compressé {compressed_path} a été supprimé après l'envoi.")
            nb_images_envoyees += 1
        except Exception as e:
            await ctx.send(f"⚠️ Erreur lors de l'envoi de {filename}: {e}")
            if compressed_path != filepath and os.path.exists(compressed_path):
                os.remove(compressed_path)

    if nb_images_envoyees == 0:
        await status_message.edit(content=f"❌ Aucune nouvelle image à envoyer pour la commande : {commande}.")
    else:
        await status_message.edit(content=f"✅ Recherche terminée : {nb_images_envoyees} image(s) envoyée(s).")

    images_restantes = total_images - len([img for img in deja_envoyees if any(img.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif'))])
    print(f"[INFO] Il reste {images_restantes} images à poster pour la commande {commande}")

    resume = f"📊 **Envoi terminé. Résumé de la commande `{commande}`**\n"
    resume += f"• Images envoyées : {nb_images_envoyees}\n"
    await ctx.send(resume)

# Commande "!ajouter"
@bot.command()
async def ajouter(ctx):
    try:
        # Demande du nom de la commande
        await ctx.send("Entrez le nom de la commande :")
        nom_commande_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=30)
        nom_commande = nom_commande_msg.content.strip()

        # Demande du chemin du dossier
        await ctx.send("Entrez le chemin du dossier :")
        dossier_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=30)
        dossier = dossier_msg.content.strip()

        # Vérification de l'existence du dossier
        if not os.path.isdir(dossier):
            await ctx.send(f"Le dossier n'existe pas : {dossier}")
            return

        # Ajout du dossier à la liste des commandes personnalisées
        if nom_commande not in commandes_personnalisees:
            commandes_personnalisees[nom_commande] = []
        commandes_personnalisees[nom_commande].append(dossier)

        # Enregistrement des commandes personnalisées dans le fichier JSON
        with open("commandes_personnalisees.json", "w") as fichier:
            json.dump(commandes_personnalisees, fichier, indent=4)

        # Message de confirmation
        await ctx.send(f"Le dossier a été ajouté à la commande : {nom_commande}")

    except asyncio.TimeoutError:
        await ctx.send("Temps écoulé, veuillez réessayer.")

# Lancement du bot
load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))

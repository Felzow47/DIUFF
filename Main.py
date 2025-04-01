import discord 
from discord import Intents
from discord.ext import commands
import os
import json
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
    with Image.open(filepath) as img:
        # Vérifier si l'image dépasse la taille maximale
        current_size = os.path.getsize(filepath)
        if current_size <= max_size:
            return filepath  # Pas besoin de compression

        # Créer le nom du fichier compressé
        file_name, file_ext = os.path.splitext(filepath)
        output_path = f"{file_name}_compressed{file_ext}"

        # Réduire la qualité jusqu'à ce que la taille soit acceptable
        quality = 95
        while current_size > max_size and quality > 10:
            img.save(output_path, "JPEG", quality=quality)
            current_size = os.path.getsize(output_path)
            quality -= 5

        return output_path if current_size <= max_size else None

@bot.command()
async def image(ctx):
    commande = ctx.message.content.split(' ')[1]

    if commande not in commandes_personnalisees:
        await ctx.send(f"Commande inconnue : {commande}")
        return

    status_message = await ctx.send("🔍 Initialisation de la recherche...")
    nb_images_envoyees = 0

    for dossier in commandes_personnalisees[commande]:
        await status_message.edit(content=f"🔍 Recherche des images dans le dossier : `{dossier}` ...")

        for root, _, files in os.walk(dossier):
            for filename in files:
                filepath = os.path.join(root, filename)
                filename_lower = filename.lower()

                if filename_lower not in deja_envoyees:
                    # Compresser l'image si nécessaire
                    compressed_path = compresser_image(filepath)

                    if compressed_path is None:
                        await ctx.send(f"❌ Impossible de compresser l'image : {filepath}")
                        continue

                    try:
                        # Envoi de l'image
                        await ctx.send(file=discord.File(compressed_path))

                        # Ajout de l'image à la liste des images envoyées
                        deja_envoyees.add(filename_lower)

                        # Enregistrement dans la liste des images envoyées
                        with open("images_envoyees.txt", "a") as fichier:
                            fichier.write(filename_lower + "\n")

                        # Supprimer le fichier compressé si ce n'est pas le fichier original
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

import discord
from discord import Intents
from discord.ext import commands
import os
import json

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
    print('DIUFF bot es prêt! ')

    # Chargement de la liste des images déjà envoyées
    try:
        with open("images_envoyees.txt", "r") as fichier:
            for filename in fichier:
                deja_envoyees.add(filename.strip())  # Supprimer les espaces éventuels
    except FileNotFoundError:
        print("Le fichier images_envoyees.txt n'existe pas encore.")

# Commande "!image"
@bot.command()
async def image(ctx):
    # Découpage du message en arguments
    commande = ctx.message.content.split(' ')[1]

    # Vérification de la validité de la commande
    if commande not in commandes_personnalisees:
        await ctx.send(f"Commande inconnue : {commande}")
        return

    # Envoi des images des dossiers liés à la commande
    nb_images_envoyees = 0
    for dossier in commandes_personnalisees[commande]:
        for filename in os.listdir(dossier):
            filename = filename.lower()
            if filename not in deja_envoyees:
                deja_envoyees.add(filename)
                await ctx.send(file=discord.File(os.path.join(dossier, filename)))
                nb_images_envoyees += 1

                # Enregistrement du nom de l'image déjà envoyée dans un fichier texte
                with open("images_envoyees.txt", "a") as fichier:
                    fichier.write(filename + "\n")

    # Message d'information si aucune image n'a été envoyée
    if nb_images_envoyees == 0:
        await ctx.send(f"Aucune nouvelle image à envoyer pour la commande : {commande}")

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
bot.run('YOUR TOKEN HERE')

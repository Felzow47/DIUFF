import discord
from discord import Intents
import os

intents = Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

deja_envoyees = set()  # Ensemble des images déjà envoyées (initialisé à l'extérieur de la fonction)

@client.event
async def on_ready():
    print('Le bot est prêt !')

    # Charger la liste des images déjà envoyées à partir du fichier texte
    try:
        with open("images_envoyees.txt", "r") as fichier:
            for filename in fichier:
                deja_envoyees.add(filename.strip())  # Supprimer les espaces éventuels
    except FileNotFoundError:
        print("Le fichier images_envoyees.txt n'existe pas encore.")

@client.event
async def on_message(message):
    if message.content.startswith('!image'):
        image_path = os.path.join(r"C:\Users\Felzow47\Desktop\Temp")
        nb_images_envoyées = 0
        for filename in os.listdir(image_path):
            filename = filename.lower()  # Conversion en minuscules pour éviter les problèmes de casse
            if filename not in deja_envoyees:
                deja_envoyees.add(filename)
                await message.channel.send(file=discord.File(os.path.join(image_path, filename)))
                nb_images_envoyées += 1

        # Envoyer un message si aucune image n'a été envoyée
        if nb_images_envoyées == 0:
            await message.channel.send("Aucune nouvelle image à envoyer !")

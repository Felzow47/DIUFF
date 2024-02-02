import discord

client = discord.Client()

@client.event
async def on_ready():
    print('Le bot est prêt !')

@client.event
async def on_message(message):
    if message.content.startswith('!image'):
        # Remplacer "votre_dossier_images" par le chemin réel de votre dossier
        image_path = os.path.join("votre_dossier_images", random.choice(os.listdir("votre_dossier_images")))
        await message.channel.send(file=discord.File(image_path))

client.run('votre_token_bot')

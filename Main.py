import discord
from discord import Intents
import os

intents = Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Le bot est prêt !')

@client.event
async def on_message(message):
    if message.content.startswith('!image'):
        image_path = os.path.join(r"C:\Users\Felzow47\Desktop\Temp")
        for filename in os.listdir(image_path):
            await message.channel.send(file=discord.File(os.path.join(image_path, filename)))

client.run('Bot Token')

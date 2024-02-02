import discord
from discord import Intents
import os 
import random

intents = Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Le bot est prêt !')

@client.event
async def on_message(message):
    if message.content.startswith('!image'):
        image_path = os.path.join(r"C:\Users\Felzow47\Desktop\Temp", random.choice(os.listdir(r"C:\Users\Felzow47\Desktop\Temp")))
        await message.channel.send(file=discord.File(image_path))

client.run('MTIwMzA3ODkzOTY5NDcyNzE5OQ.GsMqme.2HxsUJBlaAin8p9t-cdnqU4V27UTvJPLceWIPQ')

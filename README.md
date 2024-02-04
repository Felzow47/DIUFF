# DIUFF
![Sans titre](https://github.com/Felzow47/DIUFF/assets/49567056/7519cdde-0943-48ca-b8de-13f6609f9af7.png)


Discord **!image** upload from a folder

## What you'll need

* A folder where screenshots are stored
* A [discord bot token](https://discord.com/developers/applications)
* This Bot Script
* Python with discord.py

## Getting started

* You'll need to [download and install Python](https://www.python.org/downloads/),

* download [Main.py](https://github.com/Felzow47/DIUFF/releases/download/Release/Main.py) or clone the repo 

* Create a bot on [discord dev portal](https://discord.com/developers/applications)

* Add the bot to your discord server 

* Replace path in `image_path = os.path.join(r"YOUR FOLDER HERE")` with your folder with your image
* Replace with your Discord bot token in `client.run('YOUR TOKEN HERE')` 

* Run `Pip install discord` in cmd

* Run `python .\Main.py`

## Usage

send !ajouter (yeah in french) and follow what the bot tell you(the bot is not translated yet so it's only in french but if the bot get ""popular"" probaly i will translate it)  the bot will ask you for the name of the command and the folder path 

send `!image <name of the custom command you created earlier with !ajouter>` in the channel where you want the image to be posted and wait ^^ 

## Limitations/bugs
* Only files ending jpg, gif or png are uploaded.
* if the folder does't exist the bot won't add in the .json file

## Troubleshooting

if you have bugs or problem open an [issue](https://github.com/Felzow47/DIUFF/issues/new)


import discord
from discord.ext import commands
import asyncio
import aiosqlite
import random
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True

# Set command prefix
bot = commands.Bot(command_prefix="!", intents=intents)

class ProfileView(discord.ui.View):
    def __init__(self, name, role, stats, inventory):
        super().__init__()
        self.name = name
        self.role = role
        self.stats = stats
        self.inventory = inventory
        self.current_display = 'main_info'
        self.update_embed()

    def update_embed(self):
        if self.current_display == 'main_info':
            self.embed = discord.Embed(title=f"{self.name} ({self.role})", color=0x000000)
            self.embed.set_image(url="https://media.discordapp.net/attachments/1082714872955031604/1356574341323821096/serverbannerstats.png?ex=67ed0fce&is=67ebbe4e&hm=beb91417025b9b6db92d5113aedff29f829f2f48fd8d5e75427c36b56d809921&=&format=webp&quality=lossless")
            self.embed.add_field(name="Stats", value=self.stats, inline=False)
        elif self.current_display == 'inventory':
            formatted_inventory = "\n".join([f"{item} x{count}" if count > 1 else item for item, count in self.inventory.items()]) if self.inventory else "Empty"
            self.embed = discord.Embed(title=f"{self.name}'s Inventory", color=0x000000)
            self.embed.set_image(url="https://media.discordapp.net/attachments/1082714872955031604/1356574023110230096/serverbannerinventory.png?ex=67ed0f83&is=67ebbe03&hm=c4ab3b1199f8053e646a1a7d7a2f942f47c89e3acf2d0158e50f99ae95c1608a&=&format=webp&quality=lossless")
            self.embed.add_field(name="Inventory", value=formatted_inventory, inline=False)
        self.embed.set_footer(text="Use the buttons below to switch views")

    @discord.ui.button(label="Main Info", style=discord.ButtonStyle.primary, custom_id="main_info")
    async def show_main_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_display = 'main_info'
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="Inventory", style=discord.ButtonStyle.secondary, custom_id="inventory")
    async def show_inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_display = 'inventory'
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user}")
    await initialize_database()  # Ensure the database exists

# Database setup (runs when bot starts)
async def initialize_database():
    async with aiosqlite.connect("profiles.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER,
            name TEXT,
            role TEXT,
            stats TEXT,
            inventory TEXT,
            PRIMARY KEY (user_id, name, role)
        )
        """)
        await db.commit()

# D20 SYSTEM
@bot.command()
async def roll(ctx, dice: str = "1d20"):
    """Rolls a dice in NdX format and pings the user."""
    try:
        num, sides = map(int, dice.lower().split("d"))
        if num <= 0 or sides <= 0:
            await ctx.send("Please enter a valid dice format, e.g., 1d20.")
            return

        rolls = [random.randint(1, sides) for _ in range(num)]
        total = sum(rolls)
        roll_results = ", ".join(map(str, rolls))

        # Send a normal message with proper formatting
        await ctx.send(f"🎲 ┃ {ctx.author.mention} rolled **{roll_results}**")

    except ValueError:
        await ctx.send("Invalid format! Use NdX (e.g., 1d20, 2d6).")

# FLIP COIN
@bot.command(name="coinflip")
async def coinflip(ctx):
    """Flips a coin, shows a GIF, then reveals the result."""
    flip_gif = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHZ4bGRucng3ZThqdDVlNzM3anU1ZXo2czFhenVrZnMxZWw1NmJxMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/MOsuJf3qp3b1fQx2Iv/giphy.gif"  # Coin flip GIF link
    result = random.choice(["🪙 ┃ Heads!", "🪙 ┃ Tails!"])

    # Create an embed with the GIF
    embed = discord.Embed(title="Flipping the coin...", color=0x000000)
    embed.set_image(url=flip_gif)

    # Send the embed first
    gif_message = await ctx.send(embed=embed)

    # Wait 2 seconds, then reveal the result
    await asyncio.sleep(1)
    await gif_message.edit(embed=None, content=result)

# PROFILES
# Database setup (runs when bot starts)
async def initialize_database():
    async with aiosqlite.connect("profiles.db") as db:
        # Create profiles table if it doesn't exist
        await db.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER,
            name TEXT,
            role TEXT,
            stats TEXT,
            inventory TEXT,
            PRIMARY KEY (user_id, name, role)  -- This ensures unique combinations of user_id, name, and role
        )
        """)
        await db.commit()

# CREATE PROFILES
@bot.command(name="createprofile")
async def create_profile(ctx, name: str, role: str):
    """Allows a user to create a profile with a name and role."""

    if role.lower() not in ["survivor", "killer"]:
        await ctx.send("❌ Role must be 'survivor' or 'killer'.")
        return

    default_stats = "Hunting: 0\nScavenging: 0\nFishing: 0\nForaging: 0"
    default_inventory = json.dumps({})

    async with aiosqlite.connect("profiles.db") as db:
        try:
            await db.execute("""
                INSERT OR REPLACE INTO profiles (user_id, name, role, stats, inventory)
                VALUES (?, ?, ?, ?, ?)
            """, (ctx.author.id, name, role.capitalize(), default_stats, default_inventory))
            await db.commit()
        except Exception as e:
            await ctx.send(f"Database error: {str(e)}")
            return

    await ctx.send(f"Profile created for **{name}** as a **{role.capitalize()}**.")

@bot.command(name="listprofiles")
async def list_profiles(ctx):
    """Lists all profiles of the user."""

    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT name, role FROM profiles WHERE user_id = ?", (ctx.author.id,)) as cursor:
            profiles = await cursor.fetchall()

    if not profiles:
        await ctx.send("❌ You don't have any profiles yet.")
        return

    embed = discord.Embed(title=f"{ctx.author.name}'s Profiles", color=0x000000)

    for profile in profiles:
        name, role = profile
        embed.add_field(name=f"**{name}**", value=f"Role: {role.capitalize()}", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="deleteprofile")
async def delete_profile(ctx, name: str, role: str):
    """Deletes the user's profile with the given name and role from the database."""

    if role.lower() not in ["survivor", "killer"]:
        await ctx.send("❌ Role must be 'survivor' or 'killer'.")
        return

    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT name, role FROM profiles WHERE user_id = ?", (ctx.author.id,)) as cursor:
            profiles = await cursor.fetchall()

            if (name, role) not in [(profile[0], profile[1]) for profile in profiles]:
                await ctx.send(f"❌ You don't have a **{role}** profile with the name **{name}**!")
                return

            cursor = await db.execute("DELETE FROM profiles WHERE user_id = ? AND name = ? AND role = ?",
                                      (ctx.author.id, name, role))
            await db.commit()

            if cursor.rowcount > 0:
                await ctx.send(f"🗑️ Your **{role}** profile **{name}** has been deleted, {ctx.author.mention}.")
            else:
                await ctx.send("❌ No matching profile was found to delete.")

@bot.command(name="openprofile")
async def open_profile(ctx, name: str):
    """Opens the user's profile with the given name from the database."""

    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT role, stats, inventory FROM profiles WHERE user_id = ? AND name = ?",
                              (ctx.author.id, name)) as cursor:
            profile = await cursor.fetchone()

    if not profile:
        await ctx.send(f"❌ You don't have a profile with the name **{name}**!")
        return

    role, stats, inventory = profile
    try:
        inventory = json.loads(inventory) if inventory else {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        await ctx.send(f"❌ Error reading inventory data for profile **{name}**.")
        inventory = {}

    view = ProfileView(name, role, stats, inventory)
    await ctx.send(embed=view.embed, view=view)

@bot.command(name="updatestats")
async def update_stats(ctx, name: str, *, stats: str):
    """Updates the stats for the user's profile with the given name."""

    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT stats FROM profiles WHERE user_id = ? AND name = ?",
                              (ctx.author.id, name)) as cursor:
            profile = await cursor.fetchone()

        if not profile:
            await ctx.send(f"❌ You don't have a profile with the name **{name}**!")
            return

        current_stats = profile[0]

        # Parse current stats into a dictionary
        stats_dict = {}
        for line in current_stats.split("\n"):
            if line:
                key, value = line.split(": ")
                stats_dict[key.strip()] = int(value.strip())

        # Parse new stats and update the dictionary
        for stat in stats.split(","):
            if stat:
                key, value = stat.split()
                stats_dict[key.strip()] += int(value.strip())

        # Convert the updated stats dictionary back to the string format
        updated_stats = "\n".join([f"{key}: {value}" for key, value in stats_dict.items()])

        cursor = await db.execute("UPDATE profiles SET stats = ? WHERE user_id = ? AND name = ?",
                                  (updated_stats, ctx.author.id, name))
        await db.commit()

    if cursor.rowcount > 0:
        await ctx.send(f"✅ Stats for **{name}** have been updated.")
    else:
        await ctx.send(f"❌ No matching profile found to update stats.")

@bot.command(name="additem")
async def add_item(ctx, name: str, *, item: str):
    """Adds an item to the inventory of the user's profile with the given name."""

    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT inventory FROM profiles WHERE user_id = ? AND name = ?",
                              (ctx.author.id, name)) as cursor:
            profile = await cursor.fetchone()

        if not profile:
            await ctx.send(f"❌ You don't have a profile with the name **{name}**!")
            return

        try:
            inventory = json.loads(profile[0]) if profile[0] else {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await ctx.send(f"❌ Error reading inventory data for profile **{name}**.")
            inventory = {}

        if item in inventory:
            inventory[item] += 1
        else:
            inventory[item] = 1

        new_inventory = json.dumps(inventory)

        cursor = await db.execute("UPDATE profiles SET inventory = ? WHERE user_id = ? AND name = ?",
                                  (new_inventory, ctx.author.id, name))
        await db.commit()

    if cursor.rowcount > 0:
        await ctx.send(f"✅ Added **{item}** to the inventory of **{name}**.")
    else:
        await ctx.send(f"❌ No matching profile found to add item.")

@bot.command(name="removeitem")
async def remove_item(ctx, name: str, *, item: str):
    """Removes an item from the inventory of the user's profile with the given name."""

    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT inventory FROM profiles WHERE user_id = ? AND name = ?",
                              (ctx.author.id, name)) as cursor:
            profile = await cursor.fetchone()

        if not profile:
            await ctx.send(f"❌ You don't have a profile with the name **{name}**!")
            return

        try:
            inventory = json.loads(profile[0]) if profile[0] else {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await ctx.send(f"❌ Error reading inventory data for profile **{name}**.")
            inventory = {}

        if item not in inventory:
            await ctx.send(f"❌ Item **{item}** not found in the inventory of **{name}**.")
            return

        if inventory[item] > 1:
            inventory[item] -= 1
        else:
            del inventory[item]

        new_inventory = json.dumps(inventory)

        cursor = await db.execute("UPDATE profiles SET inventory = ? WHERE user_id = ? AND name = ?",
                                  (new_inventory, ctx.author.id, name))
        await db.commit()

    if cursor.rowcount > 0:
        await ctx.send(f"✅ Removed **{item}** from the inventory of **{name}**.")
    else:
        await ctx.send(f"❌ No matching profile found to remove item.")

async def show_profiles():
    async with aiosqlite.connect("profiles.db") as db:
        async with db.execute("SELECT * FROM profiles") as cursor:
            rows = await cursor.fetchall()
            logger.info(rows)

asyncio.run(show_profiles())

# HUNTING, SAV. ETC.
# Define possible outcomes for each activity
HUNTING_OUTCOMES = [
    "blighted frog", "blighted frog", "blighted frog", "frog", "frog", "frog",
    "frog", "frog", "frog", "frog", "frog", "frog", "frog", "frog", "blighted rat",
    "blighted rat", "blighted rat", "rat", "rat", "rat", "rat", "rat", "rat", "rat",
    "rat", "rat", "rat", "rat", "blighted crow", "blighted crow", "crow", "crow",
    "crow", "crow", "crow", "crow", "crow", "crow", "crow", "crow", "blighted rabbit",
    "blighted rabbit", "rabbit", "rabbit", "rabbit", "rabbit", "rabbit", "rabbit",
    "rabbit", "rabbit", "rabbit", "rabbit", "rabbit", "opossum", "opossum", "opossum",
    "opossum", "opossum", "opossum", "blighted opossum", "blighted opossum", "skunk",
    "skunk", "skunk", "skunk", "skunk", "blighted skunk", "blighted skunk", "mink",
    "mink", "mink", "mink", "mink", "blighted mink", "blighted deer", "blighted deer",
    "deer", "deer", "deer", "deer", "deer", "deer", "deer", "deer", "deer", "deer",
    "blighted pheasant", "blighted pheasant", "pheasant", "pheasant", "pheasant",
    "pheasant", "pheasant", "pheasant", "pheasant", "pheasant", "pheasant", "pheasant",
    "blighted fox", "fox", "fox", "fox", "fox", "blighted boar", "boar", "boar",
    "blighted boar", "boar", "boar", "golden stag, it's pelt is silky to the touch and the venison tastes like honey",
    "deer with two heads", "ram with horns made of stone, its fur glimmers with silver veins",
    "hyena, it's voice echoes with the words of the dead", "coyote", "coyote",
    "blighted coyote", "wolf, a crown of horns adorn its skull", "lion, its head is humanoid and its tail ends in a poisoned barb",
    "quail", "quail", "quail", "quail", "quail", "quail", "quail", "quail", "quail",
    "quail", "blighted quail", "blighted quail", "squirrel", "squirrel", "squirrel",
    "squirrel", "squirrel", "squirrel", "squirrel", "squirrel", "squirrel", "squirrel",
    "blighted squirrel", "blighted squirrel", "raccoon", "raccoon", "raccoon", "raccoon",
    "raccoon", "raccoon", "raccoon", "raccoon", "raccoon", "raccoon", "blighted raccoon",
    "blighted raccoon", "mountain lion", "mountain lion", "mountain lion", "mountain lion",
    "blighted mountain lion", "wolf", "wolf", "wolf", "wolf", "blighted wolf", "bear",
    "bear", "bear", "bear", "blighted bear", "wolverine", "duck", "duck", "duck",
    "duck", "duck", "duck", "duck", "duck", "duck", "duck", "duck", "blighted duck",
    "blighted duck", "snake", "snake", "snake", "snake", "snake", "snake", "snake",
    "snake", "snake", "snake", "snake", "blighted snake", "blighted snake", "beaver",
    "beaver", "beaver", "beaver", "beaver", "beaver", "beaver", "beaver", "beaver",
    "beaver", "blighted beaver"
]

SCAVENGING_OUTCOMES = [
    "small item", "small item", "small item", "small item", "small item",
    "small item", "small item", "small item", "small item", "small item",
    "small item", "small item", "small item", "small item", "small item",
    "small item", "small item", "small item", "small item", "small item",
    "small item", "small item", "small item", "small item", "small item",
    "small item", "small item", "small item", "medium item", "medium item",
    "medium item", "medium item", "medium item", "medium item", "medium item",
    "medium item", "medium item", "medium item", "medium item", "medium item",
    "medium item", "medium item", "medium item", "medium item", "medium item",
    "medium item", "large item", "large item", "large item", "large item",
    "large item", "large item", "large item", "large item", "large item",
    "large item", "large item", "strange relic made of twisted wood, it emanates an orange glow and feels warm to the touch",
    "old leather pouch, the inside smells of lavender and is filled with dice made of knucklebones",
    "old handwritten book, scribed in unknown symbols", "worn photograph, the face is blurred but it still shows someone you once knew",
    "worn leather bound messenger bag, it's contents are various mysterious inks",
    "broken shard of red amber, blood fills the stones core", "leather map, depicting a layout of your home town",
    "relic of your past", "garden gnome", "garden gnome", "garden gnome", "garden gnome", "garden gnome", "rusty axe",
    "rusty axe", "rusty axe", "broken knife", "broken knife", "broken knife", "item of the past, now twisted by time and memory",
    "fishing string", "fishing string", "fishing string", "fishing string", "fishing string", "arrows", "arrows", "arrows",
    "arrows", "arrows", "bear trap", "bear trap", "bear trap"
]

FISHING_OUTCOMES = [
    "crayfish", "crayfish", "crayfish", "crayfish", "crayfish", "crayfish", "crayfish", "crayfish", "crayfish", "crayfish",
    "crayfish", "blighted crayfish", "blighted crayfish", "eel", "eel", "eel", "eel", "eel", "eel", "eel", "eel", "eel", "eel",
    "blighted eel", "blighted eel", "blighted eel", "trout (small)", "trout (small)", "trout (small)", "trout (small)",
    "trout (small)", "blighted trout (small)", "pike (small)", "pike (small)", "pike (small)", "pike (small)", "pike (small)",
    "pike (small)", "blighted pike (small)", "blighted pike (small)", "blighted pike (small)", "walleye (med)", "walleye (med)",
    "walleye (med)", "walleye (med)", "walleye (med)", "blighted walleye (med)", "trout (med)", "trout (med)", "trout (med)",
    "trout (med)", "trout (med)", "blighted trout (med)", "pike (med)", "pike (med)", "pike (med)", "pike (med)", "pike (med)",
    "blighted pike (med)", "goliath tigerfish", "goliath tigerfish", "blighted goliath tigerfish", "sturgeon", "sturgeon",
    "blighted sturgeon", "catfish", "catfish", "blighted catfish", "monkfish", "monkfish", "monkfish", "monkfish", "monkfish",
    "blighted monkfish", "waterlogged boot", "waterlogged boot", "water damaged book", "water damaged book", "old bone", "old bone",
    "coelacanth made of flesh and stone", "eel which drips vile black ink", "barreleye, its head is made of glass", "giant isopod",
    "giant isopod", "blighted giant isopod", "vampire squid", "vampire squid", "blighted vampire squid", "skate", "skate", "skate",
    "skate", "skate", "blighted skate", "blighted skate", "giant spider crab", "giant spider crab", "blighted giant spider crab",
    "viperfish", "viperfish", "blighted viperfish", "wolf eel", "wolf eel", "blighted wolf eel", "goblin shark, it thrashes and wildly bites",
    "hammerhead shark, its body is covered in dark ink", "void touched sturgeon, it's skeleton is visible beneath translucent skin",
    "hagfish", "hagfish", "hagfish", "hagfish", "blighted hagfish", "alligator gar", "alligator gar", "alligator gar", "alligator gar",
    "crab", "crab", "crab", "crab", "crab", "crab", "crab", "crab", "crab", "crab", "blighted crab", "blighted crab",
    "salmon (med)", "salmon (med)", "salmon (med)", "salmon (med)", "salmon (med)", "salmon (med)", "salmon (med)", "salmon (med)",
    "salmon (med)", "blighted salmon (med)", "blighted salmon (med)", "lobster", "lobster", "lobster", "lobster", "lobster",
    "lobster", "blighted lobster"
]

FORAGING_OUTCOMES = [
    "dandelions", "dandelions", "dandelions", "dandelions", "dandelions", "dandelions", "dandelions",
    "blighted dandelions", "blighted dandelions", "nettle", "nettle", "nettle", "nettle", "nettle", "nettle", "nettle", "nettle",
    "nettle", "nettle", "blighted nettle", "blighted nettle", "yarrow", "yarrow", "yarrow", "yarrow", "yarrow", "yarrow", "yarrow",
    "yarrow", "yarrow", "blighted yarrow", "blighted yarrow", "chickweed", "chickweed", "chickweed", "chickweed", "chickweed",
    "chickweed", "chickweed", "chickweed", "chickweed", "chickweed", "blighted chickweed", "blighted chickweed", "pines", "pines",
    "pines", "pines", "pines", "pines", "pines", "pines", "pines", "blighted pines", "blighted pines", "blighted pines",
    "fiddleheads", "fiddleheads", "fiddleheads", "blighted fiddleheads", "juniper berries", "juniper berries", "juniper berries",
    "juniper berries", "juniper berries", "juniper berries", "blighted juniper berries", "cherries", "cherries", "cherries",
    "cherries", "cherries", "blighted cherries", "garlic", "garlic", "garlic", "garlic", "garlic", "blighted garlic", "chiltepin",
    "chiltepin", "chiltepin", "chiltepin", "blighted chiltepin", "mint", "mint", "mint", "mint", "mint", "blighted mint", "ginger",
    "ginger", "ginger", "ginger", "ginger", "blighted ginger", "sagebrush", "sagebrush", "sagebrush", "blighted sagebrush",
    "oyster mushrooms", "oyster mushrooms", "oyster mushrooms", "oyster mushrooms", "blighted oyster mushrooms",
    "chicken of the woods", "chicken of the woods", "chicken of the woods", "chicken of the woods", "chicken of the woods",
    "blighted chicken of the woods", "corn", "corn", "corn", "corn", "corn", "corn", "corn", "corn", "corn", "corn", "corn", "corn",
    "blighted corn", "morel mushrooms", "morel mushrooms", "morel mushrooms", "morel mushrooms", "morel mushrooms",
    "blighted morel mushrooms", "a pustula flower", "honey", "honey", "honey", "honey", "honey", "giant puffball mushrooms",
    "giant puffball mushrooms", "giant puffball mushrooms", "giant puffball mushrooms", "giant puffball mushrooms",
    "giant puffball mushrooms", "a flower with an eye in its stalk", "devil's tooth mushrooms, touching them produces black ink",
    "foxglove", "foxglove", "foxglove", "wolfsbane", "wolfsbane", "wolfsbane", "willow bark", "willow bark", "willow bark",
    "willow bark", "raspberries", "raspberries", "raspberries", "raspberries", "raspberries", "raspberries", "raspberries",
    "raspberries", "blighted raspberries"
]

@bot.command(name="hunting")
async def hunting(ctx):
    """Simulates a hunting activity and returns a random outcome."""
    outcome = random.choice(HUNTING_OUTCOMES)
    await ctx.send(f"🏹 ┃ You found a **{outcome}**.")

@bot.command(name="scavenging")
async def scavenging(ctx):
    """Simulates a scavenging activity and returns a random outcome."""
    outcome = random.choice(SCAVENGING_OUTCOMES)
    await ctx.send(f"🔍 ┃ You found a **{outcome}**.")

@bot.command(name="fishing")
async def fishing(ctx):
    """Simulates a fishing activity and returns a random outcome."""
    outcome = random.choice(FISHING_OUTCOMES)
    await ctx.send(f"🎣 ┃ You caught a **{outcome}**.")

@bot.command(name="foraging")
async def foraging(ctx):
    """Simulates a foraging activity and returns a random outcome."""
    outcome = random.choice(FORAGING_OUTCOMES)
    await ctx.send(f"🌿 ┃ You found a **{outcome}**.")

# Define the list of locations
LOCATIONS = [
    "MacMillan Estate", "Autohaven Wreckers", "Coldwind Farms", "Crotus Prenn", "Haddonfield", "Backwater Swamp",
    "Lery's Memorial Hospital", "Red Forest", "Springwood", "Gideon Meat Plant", "Yamaoka Estate", "Ormond",
    "Hawkins National Institute", "Grave of Glenvale", "Midwich Elementary School", "Raccoon City (Police station, NEST facility)",
    "Forsaken Boneyard", "The Withered Isle (Garden of Joy, Greenville)", "The Decimated Borgo", "Dvarka Deepwood (Toba's Landing, Nostromo)",
    "Lost in the fog", "Edge of the void", "Abandoned shack", "Amelie's Beach", "Norton Hospital", "Mateo Estate", "Duamont Village",
    "Survivor Campfire", "The Gates of the Underworld", "Shelter Woods", "Fortress of Steel", "Izu Pacific Resort", "Victoriano Estate"
]

@bot.command(name="foglocation")
async def foglocation(ctx):
    """Simulates walking around in the fog and returns a random location."""
    location = random.choice(LOCATIONS)
    await ctx.send(f"🌫️ ┃ The fog sends you to **{location}**.")

# BEASTIARY ENCOUNTERS
ENCOUNTERS = [
    "nothing", "nothing", "nothing", "nothing", "nothing", "nothing", "nothing", "nothing", "nothing", "nothing",
    "Shuck", "Diomedes", "Wight", "Wyrm", "Syclla", "Sovereign Of Rats", "Lamia"
]

# Store the encounter result in a global variable for simplicity
current_encounter_result = None
failed_attempts = 0

class EncounterView(discord.ui.View):
    def __init__(self, encounter_result):
        super().__init__()
        self.encounter_result = encounter_result

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.secondary)
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You fled safely.")
        global current_encounter_result
        global failed_attempts
        current_encounter_result = None
        failed_attempts = 0
        self.stop()

    @discord.ui.button(label="Fight", style=discord.ButtonStyle.danger)
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You chose to fight the **{self.encounter_result}**! \nUse the command `!fight` to roll a die.")
        global current_encounter_result
        current_encounter_result = self.encounter_result
        self.stop()

class SecondEncounterView(discord.ui.View):
    def __init__(self, encounter_result):
        super().__init__()
        self.encounter_result = encounter_result

    @discord.ui.button(label="Flee", style=discord.ButtonStyle.secondary)
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You managed to flee, but suffered injuries in the process!")
        global current_encounter_result
        global failed_attempts
        current_encounter_result = None
        failed_attempts = 0
        self.stop()

    @discord.ui.button(label="Fight", style=discord.ButtonStyle.danger)
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You chose to continue fighting the **{self.encounter_result}**! \nUse the command `!fight` to roll a die.")
        global current_encounter_result
        current_encounter_result = self.encounter_result
        self.stop()

@bot.command(name="encounter")
async def encounter(ctx):
    """Simulates a Beastiary Encounter and returns the result."""
    encounter_result = random.choice(ENCOUNTERS)
    if encounter_result == "nothing":
        await ctx.send("You encountered nothing.")
    else:
        embed = discord.Embed(title="Beastiary Encounter", description=f"You encountered a **{encounter_result}**!", color=0x7d2122)
        view = EncounterView(encounter_result)
        await ctx.send(embed=embed, view=view)

@bot.command(name="fight")
async def fight(ctx, dice: str = "1d20"):
    """Rolls a dice in NdN format."""
    global current_encounter_result
    global failed_attempts
    if not current_encounter_result:
        await ctx.send('There is no active encounter. \nUse the `!encounter` command to start an encounter.')
        return

    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    total = sum(int(num) for num in result.split(', '))
    await ctx.send(f'You rolled **{result}** ')

    if rolls == 1 and limit == 20:
        roll_value = total
        beast_roll_value = random.randint(1, 20)
        survival_threshold = random.randint(10, 20)  # Random threshold to beat

        if roll_value == beast_roll_value:
            await ctx.send(f"The Enemy rolled **{beast_roll_value}** as well.\n\n**The {current_encounter_result} changed it's mind and fled!**")
            current_encounter_result = None  # Reset encounter result
            failed_attempts = 0
        elif roll_value > survival_threshold:
            await ctx.send(f"The Enemy rolled **{survival_threshold}** \n\n🏆 ┃ **You defeated the {current_encounter_result}!** \n-# You can scavenge once more today. ")
            current_encounter_result = None  # Reset encounter result
            failed_attempts = 0
        else:
            failed_attempts += 1
            if failed_attempts == 1:
                await ctx.send(f"The Enemy rolled **{survival_threshold}**")
                embed = discord.Embed(title="Beastiary Encounter", description=f"You've been injured! Do you want to **fight** on or **flee**?\n *Continuing to fight may lead to your muse’s death*.", color=0x7d2122)
                view = SecondEncounterView(current_encounter_result)
                await ctx.send(embed=embed, view=view)
            elif failed_attempts >= 2:
                await ctx.send(f"The Enemy rolled **{survival_threshold}** \n\n🪦 ┃ **Your muse got killed by the {current_encounter_result}**.")
                current_encounter_result = None  # Reset encounter result
                failed_attempts = 0

# Replace with your bot's token
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
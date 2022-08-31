# libraries that do kind things for me like make me not have to do code
import json
from datetime import date
import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import get
import csv
import os

# important stuff unrleated to discord api
GUILD = None # constant for holding the guild
STARTED = False

# constants for discord bot stuff
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=';', intents=intents)

# current directory
CWD = os.getcwd()

# Get the token for the server
token = None
tokenfile = "token.txt"
with open(tokenfile) as t:
    token = t.readline()

# points credit dict {userid -> points}
memberPoints = {}
# roles dict {points -> role}
roles = {}
#top role and number of people who can attain it
toprole = None
topmembers = 0
roleholders = []
###########################################################
# Helper/Misc Functions

# Finds to see if a user is in the server
async def find_user(target, ctx):
    guild = ctx.guild
    for member in guild.members:
        # print(member.name)
        if member.name == target:
            # print("Member found: " + member.name)
            # print(member.id)
            return member

    return False

# Checks for data, returns true if found
# otherwise makes data and returns false
def check_for_data(user):
    userid = user.id
    global memberPoints
    if userid in memberPoints:
        print(f"{userid} already in dict. Value: {memberPoints[userid]}")
        return True
    else:
        print(f"adding {user.name} to dict")
        memberPoints[userid] = 0
        return False

async def update_top_members(ctx):
    global toprole, topmembers, roleholders
    sorted_members = sorted(memberPoints.items(), key=lambda x: x[1], reverse=True)
    if topmembers > len(sorted_members):
        ctx.send("Error in updating top rank: More members allocated than have points")
    else:
        #TODO: assign role based on role dict, remove top role
        for user in roleholders:
            user.remove_roles(toprole)

        for i in range(0, topmembers - 1):
            userid = sorted_members[i][0]
            user = bot.fetch_user(int(userid))
            user.add_roles(toprole)

async def update_roles(ctx, user: discord.member):
    global roles, memberPoints

    member = await discord.ext.commands.converter.MemberConverter().convert(ctx, str(user.id))

    userroles = member.roles
    userpoints = memberPoints[user.id]

    for amount in roles.keys():
        role = roles[amount]

        if userpoints >= amount:
            if not role in member.roles:
                await member.add_roles(role)
        else:
            if role in member.roles:
                await member.remove_roles(role)

    if userroles != member.roles:
        await ctx.send(f"{user.mention} has had their roles updated")

###########################################################
# Commands

# Admin help command
@bot.command()
async def commands(ctx, *args):
    if not STARTED:
        return

    if len(args) == 0:
        await ctx.send("Server point **ADMIN** commands: \n"
                       "```add      [user] [amount] -> adds [amount] point(s) to [user]'s account\n"
                       "remove   [user] [amount] -> subtracts [amount] from [user]'s points\n"
                       "bankroll    [WIP]        -> prints out EVERYONE'S points```\n"
                       "Server point **USER** commands:\n"
                       "```check                    -> prints out your current point balance\n"
                       "roles       [WIP]        -> prints out all the roles and points needed to reach them\n"
                       "leaderboard [WIP]        -> prints out top (TBD) users and their points\n"
                       "pay [user]  [WIP]        -> pay a user with your points.  Implementation TBD```")


@bot.command(name="add")
@has_permissions(administrator=True)
async def add_points(ctx, amount: int, mention:str):
    if not STARTED:
        return

    global memberPoints

    #get user from mention
    userid = mention.replace("@","")
    userid = userid[1:][:len(userid) - 2]
    user = await bot.fetch_user(int(userid))

    if not user:
        print("No user")
        await ctx.send("Invalid user or self mention")
    else:
        check_for_data(user)
        memberPoints[user.id] = memberPoints[user.id] + amount
        await ctx.send(f"{user.mention} has been awarded {amount} points.  Congratulations!\n"
                       f"They now have {memberPoints[user.id]} points.")
        await update_roles(ctx, user)

@bot.command(name="remove")
@has_permissions(administrator=True)
async def remove_points(ctx, amount: int, mention:str):
    if not STARTED:
        return

    global memberPoints

    #get user from mention
    userid = mention.replace("@","")
    userid = userid[1:][:len(userid) - 2]
    user = await bot.fetch_user(int(userid))

    if not user:
        print("No user")
        await ctx.send("Invalid user or self mention")
    else:
        check_for_data(user)
        memberPoints[user.id] = memberPoints[user.id] - amount
        await ctx.send(f"{user.mention} has had {amount} points revoked. They now have {memberPoints[user.id]} points.")
        await update_roles(ctx, user)


@bot.command()
@has_permissions(administrator = True)
async def giverole(ctx, user : discord.Member, *, role : discord.role = None):
    if not STARTED:
        return

    if role in user.roles:
        await ctx.send(f"{user.mention} already has the role {role}!")
    else:
        await user.add_roles(role)
        await ctx.send(f"{role} added to {user.mention} !!")


@giverole.error
async def role_error(self, ctx, error):
    if not STARTED:
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Nice try, pal")


@bot.command(name="setmaxrole")
@has_permissions(administrator = True)
async def set_max_role(ctx, name : str, amount : int = 1):
    if not STARTED:
        return

    global toprole, topmembers

    rolename = name.replace("_", " ")
    role = get(GUILD.roles, name=rolename)
    if role is None:
        print("NO ROLE")
        await ctx.send("role does not exist")
    else:
        toprole = role
        topmembers = amount
        await ctx.send(f"{role} now set as max role, with {amount} people allowed to hold it")


@bot.command(name="addrole")
@has_permissions(administrator = True)
async def add_role(ctx, name : str, amount : int):
    if not STARTED:
        return

    global roles
    rolename = name.replace("_", " ")
    role = get(GUILD.roles, name=rolename)

    if role is None:
        print("NO ROLE")
        print(name)
        print(GUILD.roles)
        await ctx.send("role does not exist")
    else:
        if amount:
            print(f"{role} adding for {amount}")
            roles[amount] = role
            await ctx.send(f"{role} added, achieved at {amount} points")

@bot.command(name="save")
@has_permissions(administrator=True)
async def save(ctx):
    if not STARTED:
        return

    #TODO: save points

    #TODO: save settings

# non-admin commands
@bot.command(name="check")
async def check_points(ctx, *args):
    if not STARTED:
        return
    user = ctx.author
    check_for_data(user)
    print(memberPoints)
    amount = memberPoints[user.id]
    await ctx.send(f"{user.mention} you have {amount} points")

# Setup/initialization commands

# init: use when setting up bot for server.  Also usable as reset.
@bot.command()
async def init(ctx, *args):
    guild = ctx.guild
    i = 0
    for member in guild.members:
        if (member == bot) or member.bot:
            continue
        else:
            memberPoints[member.id] = 0
        i += 1
    ctx.send("Initialized data for " + str(i) + " users")

# setup: use after bot restart
@bot.command()
async def start(ctx):
    global GUILD, STARTED
    GUILD = ctx.guild
    STARTED = True
    print("Bot started")

# Run the bot
@bot.event
async def on_ready():
    print("Ready!")

bot.run(token)
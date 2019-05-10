from disco.bot.command import CommandLevels

def level_getter(bot, actor):
    if actor.id == 80351110224678912:
        return CommandLevels.OWNER

    hydr0 = bot.client.state.guilds.get(102942166011084800)
    if hydr0 and actor.id in hydr0.members:
        return CommandLevels.TRUSTED

    return CommandLevels.DEFAULT

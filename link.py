import discord
from discord import app_commands
from discord.ext import commands

TARGET_CHANNEL_ID = 1403389648452980870

class LinkCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="link", description="Upload an image and get a copyable branded link.")
    @app_commands.describe(image="Attach your image here")
    async def link(self, interaction: discord.Interaction, image: discord.Attachment):
        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.response.send_message("Please upload a valid image file.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            channel = self.bot.get_channel(TARGET_CHANNEL_ID)
            if not channel:
                await interaction.followup.send("Target channel not found.", ephemeral=True)
                return

            sent_msg = await channel.send(file=await image.to_file())
            if not sent_msg.attachments:
                await interaction.followup.send("Image failed to upload.", ephemeral=True)
                return

            image_url = sent_msg.attachments[0].url

            embed = discord.Embed(
                title="Your Link from .gg/esigns ",
                description=f"Here’s your copyable link from [**.gg/esigns**](https://discord.gg/esigns) \n\n`{image_url}`",
                color=discord.Color.purple()
            )
            embed.set_footer(text=".gg/esigns • Join the original fansign community!")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LinkCommand(bot))

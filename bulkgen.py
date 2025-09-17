import discord
from discord import app_commands
from discord.ext import commands
from pathlib import Path
import importlib
import sys
import re

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "fonts"
STYLES_DIR = BASE_DIR / "commands" / "styles"

class BulkFanSign(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_available_fonts(self):
        return [f.stem for f in FONTS_DIR.iterdir() if f.suffix.lower() in {'.ttf', '.otf'}]

    def get_available_styles(self):
        styles = [
            f.stem for f in STYLES_DIR.iterdir()
            if f.is_file() and f.suffix == ".py" and not f.stem.startswith("__")
        ]
        return sorted(styles, key=self.style_sort_key)

    def style_sort_key(self, style_name: str):
        match = re.search(r'(\d+)', style_name)
        number = int(match.group(1)) if match else 99999
        return (number, style_name)

    def import_style_module(self, style_name: str):
        module_path = f"commands.styles.{style_name}"
        if module_path in sys.modules:
            return sys.modules[module_path]
        return importlib.import_module(module_path)

    @app_commands.command(name="bulkgen", description="Generate multiple fansigns with different styles.")
    @app_commands.describe(
        text="Text to display (max 14 characters)",
        font="Font to use (from fonts folder)",
        style1="First style (required)",
        style2="Second style (optional)",
        style3="Third style (optional)",
        style4="Fourth style (optional)",
        style5="Fifth style (optional)",
        style6="Sixth style (optional)",
        style7="Seventh style (optional)",
        style8="Eighth style (optional)",
        style9="Ninth style (optional)",
        style10="Tenth style (optional)",
    )
    @app_commands.checks.cooldown(1, 10.0)
    async def bulkgen(
        self,
        interaction: discord.Interaction,
        text: str,
        font: str,
        style1: str,
        style2: str = None,
        style3: str = None,
        style4: str = None,
        style5: str = None,
        style6: str = None,
        style7: str = None,
        style8: str = None,
        style9: str = None,
        style10: str = None,
    ):
        if len(text) > 14:
            embed = discord.Embed(
                title="Error",
                description="The text can only be 14 characters or less.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        available_fonts = self.get_available_fonts()
        if font not in available_fonts:
            embed = discord.Embed(
                title="Error",
                description=f"Invalid font. Available fonts: {', '.join(available_fonts)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        style_inputs = [
            style1, style2, style3, style4, style5,
            style6, style7, style8, style9, style10
        ]
        styles = [s.lower() for s in style_inputs if s]

        available_styles = self.get_available_styles()
        if len(set(styles)) != len(styles):
            embed = discord.Embed(
                title="Error",
                description="You cannot choose the same style more than once.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        for style in styles:
            if style not in available_styles:
                embed = discord.Embed(
                    title="Error",
                    description=f"Invalid style: {style}. Available styles: {', '.join(available_styles)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

        await interaction.response.defer()

        try:
            files = []
            embeds = []

            for i, style in enumerate(styles, start=1):
                style_module = self.import_style_module(style)
                func_name = f"generate_fansign_{style}"
                if not hasattr(style_module, func_name):
                    embed = discord.Embed(
                        title="Error",
                        description=f"Style {style} missing function {func_name}.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
                    return

                generate_func = getattr(style_module, func_name)
                out_path = await generate_func(interaction.user.id, text, font)

                file = discord.File(str(out_path), filename=out_path.name)
                files.append(file)

                embed = discord.Embed(
                    title="Your Fansign from .gg/esigns ",
                    description="Generated with love from [**.gg/esigns**](https://discord.gg/esigns) \nJoin us now at **.gg/esigns**!",
                    color=discord.Color.purple()
                )
                embed.add_field(name="Text", value=text, inline=True)
                embed.add_field(name="Font", value=font, inline=True)
                embed.add_field(name="Style", value=style + "\n\n[**.gg/esigns**](https://discord.gg/esigns)", inline=True)
                embed.set_image(url=f"attachment://{out_path.name}")
                embed.set_footer(text=".gg/esigns • Join the original fansign community!")
                embeds.append(embed)

            for i in range(0, len(embeds), 5):
                await interaction.user.send(embeds=embeds[i:i+5], files=files[i:i+5])

            await interaction.followup.send("Check your DMs for your fansigns.", ephemeral=True)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="Couldn't DM you. Please enable DMs from server members.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in bulkgen: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An unexpected error occurred: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

    @bulkgen.autocomplete("font")
    async def font_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        fonts = self.get_available_fonts()
        return [
            app_commands.Choice(name=f, value=f)
            for f in fonts if current.lower() in f.lower()
        ][:25]

    @bulkgen.autocomplete("style1")
    @bulkgen.autocomplete("style2")
    @bulkgen.autocomplete("style3")
    @bulkgen.autocomplete("style4")
    @bulkgen.autocomplete("style5")
    @bulkgen.autocomplete("style6")
    @bulkgen.autocomplete("style7")
    @bulkgen.autocomplete("style8")
    @bulkgen.autocomplete("style9")
    @bulkgen.autocomplete("style10")
    async def bulk_style_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        styles = self.get_available_styles()

        focused_option = interaction.data.get('options')
        chosen_styles = set()
        if focused_option:
            for opt in focused_option:
                if opt.get('value'):
                    chosen_styles.add(opt['value'].lower())

        focused_name = interaction.data.get('data', {}).get('name', '')

        filtered_styles = []
        for style in styles:
            if style in chosen_styles and style != (interaction.data.get('data', {}).get('options', [{}])[0].get('value', '') or '').lower():
                continue
            if current.lower() in style.lower():
                filtered_styles.append(app_commands.Choice(name=style, value=style))
            if len(filtered_styles) >= 25:
                break
        return filtered_styles

async def setup(bot):
    await bot.add_cog(BulkFanSign(bot))

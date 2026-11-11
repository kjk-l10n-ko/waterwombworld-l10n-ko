using System;
using System.IO;
using System.Linq;
using UndertaleModLib.Models;
using UndertaleModLib.Util;

EnsureDataLoaded();

void injectFont(string fontName, string texPngPath, string glyphCsvPath)
{
    var font = Data.Fonts.ByName(fontName);
    if (font == null)
    {
        Console.WriteLine("NOT FOUND: " + fontName);
        return;
    }

    // Read new texture PNG
    var pngBytes = File.ReadAllBytes(texPngPath);
    var newImg = GMImage.FromPng(pngBytes);

    // Create new EmbeddedTexture for this font
    var newET = new UndertaleEmbeddedTexture();
    newET.TextureData.Image = newImg;
    Data.EmbeddedTextures.Add(newET);

    // Point font's texture page item at the new texture
    var pti = font.Texture;
    pti.SourceX = 0;
    pti.SourceY = 0;
    pti.SourceWidth = (ushort)newImg.Width;
    pti.SourceHeight = (ushort)newImg.Height;
    pti.TexturePage = newET;

    // Read and apply glyph CSV
    var csvContent = File.ReadAllText(glyphCsvPath);
    var lines = csvContent.Split("\n");
    font.Glyphs.Clear();
    int count = 0;
    for (int i = 1; i < lines.Length; i++)
    {
        string line = lines[i].Trim();
        if (line.Length == 0) continue;
        var parts = line.Split(";");
        if (parts.Length < 7) continue;

        var g = new UndertaleFont.Glyph();
        g.Character = (ushort)int.Parse(parts[0]);
        g.SourceX = (ushort)int.Parse(parts[1]);
        g.SourceY = (ushort)int.Parse(parts[2]);
        g.SourceWidth = (ushort)int.Parse(parts[3]);
        g.SourceHeight = (ushort)int.Parse(parts[4]);
        g.Shift = (short)int.Parse(parts[5]);
        g.Offset = (short)int.Parse(parts[6]);
        font.Glyphs.Add(g);
        count++;
    }
    Console.WriteLine(fontName + ": " + count + " glyphs injected");
}

// Resolve working directory
string fw = Environment.GetEnvironmentVariable("FONTWORK_DIR");
if (fw == null) fw = "/tmp/water/font_export";

// All 17 fonts with their generated texture and glyph files
string[][] fontDefs = new string[][] {
    new string[] { "fnt_dialogue",         fw + "/fnt_dialogue_new.png",         fw + "/fnt_dialogue_new_glyphs.csv" },
    new string[] { "fnt_button",           fw + "/fnt_button_new.png",           fw + "/fnt_button_new_glyphs.csv" },
    new string[] { "fnt_computer",         fw + "/fnt_computer_new.png",         fw + "/fnt_computer_new_glyphs.csv" },
    new string[] { "fnt_smallcomputer",    fw + "/fnt_smallcomputer_new.png",    fw + "/fnt_smallcomputer_new_glyphs.csv" },
    new string[] { "fnt_gm_15",            fw + "/fnt_gm_15_new.png",            fw + "/fnt_gm_15_new_glyphs.csv" },
    new string[] { "fnt_gm_20",            fw + "/fnt_gm_20_new.png",            fw + "/fnt_gm_20_new_glyphs.csv" },
    new string[] { "fnt_gm_30",            fw + "/fnt_gm_30_new.png",            fw + "/fnt_gm_30_new_glyphs.csv" },
    new string[] { "fnt_gothic",           fw + "/fnt_gothic_new.png",           fw + "/fnt_gothic_new_glyphs.csv" },
    new string[] { "fnt_biggothic",        fw + "/fnt_biggothic_new.png",        fw + "/fnt_biggothic_new_glyphs.csv" },
    new string[] { "fnt_gothic_patron_1",  fw + "/fnt_gothic_patron_1_new.png",  fw + "/fnt_gothic_patron_1_new_glyphs.csv" },
    new string[] { "fnt_gothic_patron_2",  fw + "/fnt_gothic_patron_2_new.png",  fw + "/fnt_gothic_patron_2_new_glyphs.csv" },
    new string[] { "fnt_gothic_patron_3",  fw + "/fnt_gothic_patron_3_new.png",  fw + "/fnt_gothic_patron_3_new_glyphs.csv" },
    new string[] { "fnt_gothic_patron_4",  fw + "/fnt_gothic_patron_4_new.png",  fw + "/fnt_gothic_patron_4_new_glyphs.csv" },
    new string[] { "fntMain",              fw + "/fntMain_new.png",              fw + "/fntMain_new_glyphs.csv" },
    new string[] { "fntTop",               fw + "/fntTop_new.png",               fw + "/fntTop_new_glyphs.csv" },
    new string[] { "fntValue",             fw + "/fntValue_new.png",             fw + "/fntValue_new_glyphs.csv" },
    new string[] { "fnt_debug",            fw + "/fnt_debug_new.png",            fw + "/fnt_debug_new_glyphs.csv" },
};

// Inject every font
for (int i = 0; i < fontDefs.Length; i++)
    injectFont(fontDefs[i][0], fontDefs[i][1], fontDefs[i][2]);

// Verification: count Hangul vs Latin glyphs per font
Console.WriteLine("");
Console.WriteLine("=== Verification ===");
foreach (var font in Data.Fonts)
{
    int hangul = 0, latin = 0;
    foreach (var g in font.Glyphs)
    {
        int cp = (int)g.Character;
        if (cp >= 0xAC00 && cp <= 0xD7A3)
            hangul++;
        else if ((cp >= 0x20 && cp <= 0x7F) || (cp >= 0xA0 && cp <= 0xFF))
            latin++;
    }
    Console.WriteLine(font.Name.Content + ": " + hangul + " Hangul, " + latin + " Latin (total " + font.Glyphs.Count + ")");
}

Console.WriteLine("");
Console.WriteLine("Done. Save with -o");
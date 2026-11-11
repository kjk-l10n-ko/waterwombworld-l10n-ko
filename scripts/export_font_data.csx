using System;
using System.IO;
using System.Linq;
using UndertaleModLib;
using UndertaleModLib.Models;
using UndertaleModLib.Util;

EnsureDataLoaded();

string OUT = Environment.GetEnvironmentVariable("FONTWORK_DIR") ?? "/tmp/water/font_export";
Directory.CreateDirectory(OUT);
Directory.CreateDirectory(OUT + "/EmbeddedTextures");

// Export glyph tables for every font with texture data
foreach (var font in Data.Fonts)
{
    string name = font.Name.Content;
    string csvPath = OUT + "/" + name + "_glyphs.csv";
    
    Console.WriteLine("Font: " + name
        + " em=" + font.EmSize
        + " asc=" + font.Ascender
        + " lineH=" + font.LineHeight
        + " sdf=" + font.SDFSpread
        + " glyphs=" + font.Glyphs.Count);
    
    var pti = font.Texture;
    if (pti == null) { Console.WriteLine("  -> no PageItem, skip"); continue; }
    
    var et = pti.TexturePage;
    int texi = et == null ? -1 : Data.EmbeddedTextures.IndexOf(et);
    
    Console.WriteLine("  -> pageitem src=(" + pti.SourceX + "," + pti.SourceY + "," + pti.SourceWidth + "x" + pti.SourceHeight
        + ") tgt=(" + pti.TargetX + "," + pti.TargetY + "," + pti.TargetWidth + "x" + pti.TargetHeight
        + ") tex" + texi + " " + (et == null ? "null" : (et.Name?.Content ?? "?") + " " + et.TextureWidth + "x" + et.TextureHeight));
    
    // Export pageitem info
    File.WriteAllText(OUT + "/" + name + "_pageitem.txt",
        pti.SourceX + ";" + pti.SourceY + ";" + pti.SourceWidth + ";" + pti.SourceHeight + ";"
        + pti.TargetX + ";" + pti.TargetY + ";" + pti.TargetWidth + ";" + pti.TargetHeight + ";"
        + texi + ";" + (et == null ? "0" : "" + et.TextureWidth) + ";" + (et == null ? "0" : "" + et.TextureHeight));
    
    // Export glyph CSV
    using (var w = new StreamWriter(csvPath))
    {
        w.WriteLine("char;srcX;srcY;srcW;srcH;shift;offset");
        foreach (var g in font.Glyphs)
            w.WriteLine("" + (int)g.Character + ";" + g.SourceX + ";" + g.SourceY + ";" + g.SourceWidth + ";" + g.SourceHeight + ";" + g.Shift + ";" + g.Offset);
    }
    
    // Export texture reference (full page)
    if (et?.TextureData?.Image != null)
    {
        string texPath = OUT + "/EmbeddedTextures/" + name + "_texture.png";
        using (var fs = File.Create(texPath))
            et.TextureData.Image.SavePng(fs);
        Console.WriteLine("  -> saved " + texPath);
    }
}

// Also export raw textures by index
Console.WriteLine("\n=== Raw embedded textures ===");
for (int i = 0; i < Data.EmbeddedTextures.Count; i++)
{
    var et = Data.EmbeddedTextures[i];
    if (et?.TextureData?.Image == null) { Console.WriteLine("T" + i + " no image"); continue; }
    string path = OUT + "/EmbeddedTextures/tex" + i + ".png";
    using (var fs = File.Create(path))
        et.TextureData.Image.SavePng(fs);
    Console.WriteLine("T" + i + " " + (et.Name?.Content ?? "?") + " " + et.TextureWidth + "x" + et.TextureHeight + " -> " + path + " (" + et.TextureData.Image.Width + "x" + et.TextureData.Image.Height + ")");
}
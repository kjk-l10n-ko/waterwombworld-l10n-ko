using System;
using System.Linq;

EnsureDataLoaded();

int totalHangul = 0, totalLatin = 0, totalGlyphs = 0, fontCount = 0;

Console.WriteLine("Font Hangul Verification");
Console.WriteLine("========================");
Console.WriteLine("");

foreach (var font in Data.Fonts)
{
    int hangul = 0, latin = 0, other = 0;
    int minCp = int.MaxValue, maxCp = -1;
    fontCount++;

    foreach (var g in font.Glyphs)
    {
        int cp = (int)g.Character;
        if (cp < minCp) minCp = cp;
        if (cp > maxCp) maxCp = cp;
        if (cp >= 0xAC00 && cp <= 0xD7A3)
            hangul++;
        else if ((cp >= 0x20 && cp <= 0x7F) || (cp >= 0xA0 && cp <= 0xFF))
            latin++;
        else
            other++;
    }

    totalHangul += hangul;
    totalLatin += latin;
    totalGlyphs += font.Glyphs.Count;

    string status = "OK";
    if (hangul == 0 && font.Glyphs.Count > 0) status = "NO HANGUL";
    else if (font.Glyphs.Count == 0) status = "EMPTY";

    Console.WriteLine(font.Name.Content);
    Console.WriteLine("  Glyphs: " + font.Glyphs.Count + " total (" + hangul + " Hangul, " + latin + " Latin, " + other + " other)");
    Console.WriteLine("  Range: U+" + minCp.ToString("X") + "..U+" + maxCp.ToString("X"));
    Console.WriteLine("  Status: " + status);
    Console.WriteLine("");
}

Console.WriteLine("========================");
Console.WriteLine("Summary: " + fontCount + " fonts, " + totalGlyphs + " total glyphs, " + totalHangul + " Hangul syllables, " + totalLatin + " Latin chars");

if (totalHangul == 0)
{
    Console.WriteLine("WARNING: No Hangul glyphs found in any font!");
}
else
{
    Console.WriteLine("SUCCESS: Hangul glyphs present.");
}
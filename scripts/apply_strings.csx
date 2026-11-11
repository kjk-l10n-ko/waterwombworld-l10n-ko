using System;
using UndertaleModLib.Models;

EnsureDataLoaded();

// Patch display strings in STRG by index
// Index-only patch: only change entries confirmed to be display text
string[][] patches = new string[][] {
    new string[] { "1602", "워터 움브 월드에 오신 것을 환영합니다. 300,000년의 개발 끝에, 기다린 보람이 있기를 바랍니다. 이 버전의 워터 움브 월드에는 Yames의 해설이 포함되어 있습니다. 해설 노드를 시작하려면 게임 창 오른쪽 상단의 해설 제목을 찾아 왼쪽 버튼을 클릭하세요. 일부 해설 노드는 특정 지점을 더 잘 설명하거나 삭제된 콘텐츠를 보여주기 위해 이미지를 표시할 수 있습니다. 해설 노드가 활성화된 동안에도 게임은 완전히 플레이 가능합니다. 연구실을 나가거나 들어가는 등의 일부 행동이 해설 노드를 조기에 종료시킬 수 있습니다." },  // Welcome to Water Womb World...
    new string[] { "1306", "해설 재생 : " },        // PLAY COMMENTARY :
    new string[] { "1318", "해설 : " },             // COMMENTARY :
    new string[] { "1604", "해설 노드를 중단하려면 게임 창 왼쪽 상단의 해설 텍스트를 왼쪽 클릭하거나 해설이 끝날 때까지 기다리세요. 해설 노드는 시간과 장소에 따라 다르게 나타납니다. 모두 찾아보세요! 플레이해 보신 뒤 소감을 알려 주세요. yames@yames.info 로 연락하실 수 있습니다. 감사합니다, 재미있게 즐기세요!" },
    new string[] { "1661", "사 이 버  교 리 문 답  -  버 전  1 . 0 " },  // C Y B E R  C A T E C H I S M  -  V E R S I O N  1 . 0
    new string[] { "1662", "아담족 두개골" },        // ADAMITE SKULL
    new string[] { "1663", "부분적으로 화석화된 아담의 아들의 유해. 조상의 타락 5%를 함유. 대략적인 계산에 따르면 이 인간은 약 천 년을 살았으며, 원초적 타락으로부터 10세대 뒤에 태어났다. 높은 골밀도는 수생 생활을 시사한다." },
    new string[] { "1664", "잠수용 마스크" },        // DIVE MASK
    new string[] { "1665", "제작 시기: 20세기 중반. 고무 스커트가 달린 잠수용 마스크로, 각종 그리스도 문자와 성경 문구로 장식되어 있다." },
    new string[] { "1666", "고대 물고기" },          // ANCIENT FISH
    new string[] { "1667", "탄소 연대 측정 추정치: 10,000년. 레이저 생체 해부 결과, 토착 산호류를 먹고 산 물고기로 확인됨. 과석회화된 골격 구조: 인장 강도가 현대 메타물질에 필적함. " },
    new string[] { "1672", "불사의 물고기" },        // DEATHLESS FISH
    new string[] { "1673", "이전 물고기 표본과의 교차 분석: 물고기의 나이가 이전 추정치를 초과함. 쥐라기 어느 시기에 태어남. 세포 성장 이상: 거의 완전히 정지 상태. 위 내용물에서 더 많은 토착 산호류가 확인됨. DNA에 원시 인류 단백질 포함. " },
    new string[] { "1674", "불사의 물고기 2" },      // DEATHLESS FISH 2
    new string[] { "1675", "형태 불명. 표본의 50%가 산호 폴립으로 구성됨. 나이가 다시 여러 지질 시대를 초과함. 정체불명의 돌 물질을 분비함. DNA에 원시 인류 단백질 포함." },
    new string[] { "1676", "붉은 산호" },            // RED CORAL
    new string[] { "1677", "기원: 불명. 오류. 원시 인류의 뉴런이 박혀 있으며, 의식장을 만들어 내는 능력이 극도로 뛰어남. 신의 자궁. 오류. 오류. 오류." },
    new string[] { "1725", "섭 취 중 . . . " },      // F E E D I N G . . .
    new string[] { "1771", "인간 두개골" },          // HUMAN SKULL
    new string[] { "1772", "기이한 물고기" },        // STRANGE FISH
    new string[] { "1773", "못생긴 물고기" },        // UGLY FISH
    new string[] { "1774", "부푼 물고기" },          // BLOATED FISH
    new string[] { "1828", "제 작업은 패트리온 후원자들 덕분에 가능합니다. 그분들께 무한한 감사를 드립니다." },
    new string[] { "1855", "[ESC 키를 누르면 메인 메뉴로 돌아갑니다]" },  // [PRESS ESCAPE TO RETURN TO MAIN MENU]
    new string[] { "1863", "연 구 중 . . . " },      // R E S E A R C H I N G . . .
    new string[] { "1871", "체 질 중 . . . " },      // S I F T I N G . . .
    new string[] { "1751", "시작" },              // Start
    new string[] { "1753", "옵션" },              // Options
    new string[] { "1754", "아직 아무것도 안 해요!" }, // This doesn't do anything currently!
    new string[] { "1755", "종료" },              // Exit
    new string[] { "1756", "다음에 봐요!" },       // See you later!
    new string[] { "1758", "그냥 데모일 뿐입니다." }, // Just a demo.
    new string[] { "1885", " 워터 움브 월드" },    // " Water Womb World" (title)
    new string[] { "2030", "워터 움브 월드" },     // WATER WOMB WORLD
    new string[] { "2053", "워터 움브 월드" },     // Water Womb World
    // Identifiers (keep): 1752=rm_multimenu, 1757=game_end, 1759=h
};

int[] idxs = new int[patches.Length];
string[] kor = new string[patches.Length];

for (int i = 0; i < patches.Length; i++)
{
    idxs[i] = int.Parse(patches[i][0]);
    kor[i] = patches[i][1];
}

int count = Data.Strings.Count;
int patched = 0;

for (int i = 0; i < patches.Length; i++)
{
    int idx = idxs[i];
    if (idx < 0 || idx >= count) 
    {
        Console.WriteLine("SKIP: index " + idx + " out of range");
        continue;
    }
    
    string old = Data.Strings[idx].Content;
    string korean = kor[i];
    
    if (old != korean)
    {
        Data.Strings[idx].Content = korean;
        patched++;
        Console.WriteLine("PATCHED [" + idx + "]: '" + old + "' -> '" + korean + "'");
    }
    else
    {
        Console.WriteLine("SAME  [" + idx + "]: '" + old + "' (already Korean)");
    }
}
Console.WriteLine("Done: " + patched + " strings patched");
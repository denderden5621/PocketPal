#pragma once
#include <stdint.h>

// Oyunlar: 0 Zıpla, 1 Yakala, 2 Hafıza, 3 Tepki, 4 Düello (iki kişilik)
namespace games {

enum { ZIPLA = 0, YAKALA = 1, HAFIZA = 2, TEPKI = 3, DUELLO = 4, COUNT = 5 };

extern const char *const NAMES[COUNT];

// Oyunu oynat; oyuncu çıkınca ya da uzun süre dokunulmayınca döner.
// true = uyku zaman aşımıyla çıkıldı
bool play(int id);

} // namespace games

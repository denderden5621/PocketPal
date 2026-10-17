#pragma once

// Menü: iki düğmeyle gezinme (Sol = aşağı, Sağ = seç, uzun Sol = geri)
namespace menu {

enum Result { BACK, TIMEOUT };

Result run();          // ana menü
Result runGames();     // doğrudan oyun listesi

} // namespace menu

#include "store.h"
#include "nvs_flash.h"
#include "nvs.h"
#include <string.h>

namespace store {

static const uint8_t VERSION = 3;
Data d;
static Data saved;

static void defaults()
{
    memset(&d, 0, sizeof(d));
    d.version = VERSION;
    d.sound = 1;
    d.style = STYLE_CAT;
    d.rotate180 = 0;
    d.motion_wake = 1;
    d.tilt_rot = 0;
}

void begin()
{
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        err = nvs_flash_init();
    }
    defaults();
    if (err == ESP_OK) {
        nvs_handle_t h;
        if (nvs_open("pal", NVS_READONLY, &h) == ESP_OK) {
            Data tmp;
            size_t len = sizeof(tmp);
            if (nvs_get_blob(h, "data", &tmp, &len) == ESP_OK && len == sizeof(tmp) && tmp.version == VERSION)
                d = tmp;
            nvs_close(h);
        }
    }
    saved = d;
}

void save()
{
    if (memcmp(&d, &saved, sizeof(d)) == 0) return;
    nvs_handle_t h;
    if (nvs_open("pal", NVS_READWRITE, &h) != ESP_OK) return;
    if (nvs_set_blob(h, "data", &d, sizeof(d)) == ESP_OK && nvs_commit(h) == ESP_OK) saved = d;
    nvs_close(h);
}

void resetAll()
{
    defaults();
    save();
}

} // namespace store

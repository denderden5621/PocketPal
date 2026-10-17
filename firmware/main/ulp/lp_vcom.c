/*
 * LP çekirdek programı: Sharp bellek ekranının EXTCOMIN pinini (GPIO2 / D2)
 * her uyanışta tersine çevirir. LP zamanlayıcı 500 ms'de bir uyandırır -> 1 Hz kare dalga.
 * Ana işlemci derin uykudayken de çalışır; ekran görüntüyü korur ve DC yük birikmez.
 */
#include <stdint.h>
#include "ulp_lp_core_utils.h"
#include "ulp_lp_core_gpio.h"

#define VCOM_PIN LP_IO_NUM_2

volatile uint32_t vcom_enabled = 1;   /* ana işlemci 0 yazarsa darbe durur */
volatile uint32_t vcom_level = 0;
volatile uint32_t vcom_inited = 0;
volatile uint32_t vcom_ticks = 0;     /* teşhis için sayaç */

int main(void)
{
    if (!vcom_inited) {
        ulp_lp_core_gpio_init(VCOM_PIN);
        ulp_lp_core_gpio_output_enable(VCOM_PIN);
        vcom_inited = 1;
    }
    if (vcom_enabled) {
        vcom_level ^= 1;
        ulp_lp_core_gpio_set_level(VCOM_PIN, (uint8_t)vcom_level);
        vcom_ticks++;
    }
    return 0; /* LP çekirdek durur, LP zamanlayıcı tekrar başlatır */
}

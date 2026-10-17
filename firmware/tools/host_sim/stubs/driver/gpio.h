#pragma once
typedef enum { GPIO_NUM_0=0, GPIO_NUM_1, GPIO_NUM_2, GPIO_NUM_16=16, GPIO_NUM_17=17, GPIO_NUM_18=18, GPIO_NUM_19=19, GPIO_NUM_20=20, GPIO_NUM_21=21, GPIO_NUM_22=22, GPIO_NUM_23=23 } gpio_num_t;
typedef enum { GPIO_MODE_INPUT, GPIO_MODE_OUTPUT } gpio_mode_t;
static inline int gpio_reset_pin(gpio_num_t){return 0;}
static inline int gpio_set_direction(gpio_num_t, gpio_mode_t){return 0;}
static inline int gpio_set_level(gpio_num_t, int){return 0;}
static inline int gpio_hold_en(gpio_num_t){return 0;}
static inline int gpio_hold_dis(gpio_num_t){return 0;}
static inline int gpio_pullup_dis(gpio_num_t){return 0;}
static inline int gpio_pulldown_dis(gpio_num_t){return 0;}

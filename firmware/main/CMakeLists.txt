set(app_sources
    "main.cpp"
    "display.cpp"
    "lis3dh.cpp"
    "input.cpp"
    "sound.cpp"
    "face.cpp"
    "games.cpp"
    "menu.cpp"
    "power.cpp"
    "store.cpp")

idf_component_register(SRCS ${app_sources}
                       INCLUDE_DIRS "."
                       REQUIRES ulp esp_driver_gpio esp_driver_spi esp_driver_i2c esp_driver_ledc
                                esp_adc nvs_flash esp_timer esp_hw_support
                       WHOLE_ARCHIVE)

# LP çekirdek programı (ulp/lp_vcom.c) - ekranın EXTCOMIN pinini uykuda da çevirir
set(ulp_app_name ulp_main)
set(ulp_sources "ulp/lp_vcom.c")
set(ulp_exp_dep_srcs "power.cpp")
ulp_embed_binary(${ulp_app_name} "${ulp_sources}" "${ulp_exp_dep_srcs}")

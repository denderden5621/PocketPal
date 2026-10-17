#pragma once
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_ERR_NO_MEM 0x101
#define ESP_ERROR_CHECK(x) (void)(x)
typedef void* spi_device_handle_t;
typedef struct { int mosi_io_num, miso_io_num, sclk_io_num, quadwp_io_num, quadhd_io_num; size_t max_transfer_sz; } spi_bus_config_t;
typedef struct { int mode; int clock_speed_hz; int spics_io_num; unsigned flags; int cs_ena_pretrans, cs_ena_posttrans, queue_size; } spi_device_interface_config_t;
typedef struct { size_t length; const void* tx_buffer; } spi_transaction_t;
#define SPI2_HOST 1
#define SPI_DMA_CH_AUTO 3
#define SPI_DEVICE_POSITIVE_CS 1
#define SPI_DEVICE_TXBIT_LSBFIRST 2
static inline esp_err_t spi_bus_initialize(int, const spi_bus_config_t*, int){return 0;}
static inline esp_err_t spi_bus_add_device(int, const spi_device_interface_config_t*, spi_device_handle_t* d){*d=(void*)1;return 0;}
static inline esp_err_t spi_device_polling_transmit(spi_device_handle_t, spi_transaction_t*){return 0;}

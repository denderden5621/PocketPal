#pragma once
#include <stdlib.h>
#define MALLOC_CAP_DMA 0
static inline void* heap_caps_malloc(size_t n, int){return malloc(n);}

// PLE TinyLM inference on the ESP32-S3.
//
// The model lives in a flash 'model' partition (subtype 0x40), memory-mapped.
// Weights are staged int8 in PSRAM; scratch buffers are in SRAM.
// Based on slvDev/esp32-ai firmware/esp32_tinystories/esp32_tinystories.ino
// adapted for PlatformIO (Arduino framework, no display).

#include <Arduino.h>
#include "esp_partition.h"
#include "esp_spi_flash.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"

// int8 activations, required by the staged int8 kernel.
#define LLM_INT8_ACT 1
#define LLM_PROFILE 1
#define LLM_PROFILE_NOW() esp_timer_get_time()
#include "llm.h"
#include "generated/vocab.h"

// No display wired up.
#define USE_DISPLAY 0

static const int PROMPT_IDS[] = {9038, 2501, 263, 931}; // "Once upon a time"
static const int N_GENERATE = 200;

Model model;
Scratch s;

// ---- allocation ------------------------------------------------------------
static size_t psram_used = 0, sram_used = 0;

#define STATIC_SRAM_BYTES (2 * LLM_Q8_MAX_INPUT)

static void *ps(size_t n) {
  void *p = heap_caps_malloc(n, MALLOC_CAP_SPIRAM);
  if (p) psram_used += n;
  return p;
}
static void *ps_or_die(size_t n, const char *what) {
  void *p = ps(n);
  if (!p) {
    Serial.printf("FATAL: required PSRAM allocation failed: %s (%u bytes)\n",
                  what, (unsigned)n);
    while (1) delay(1000);
  }
  return p;
}
static void *sram_or_die(size_t n, const char *what) {
  void *p = heap_caps_malloc(n, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
  if (!p) {
    Serial.printf("FATAL: required SRAM allocation failed: %s (%u bytes)\n",
                  what, (unsigned)n);
    while (1) delay(1000);
  }
  sram_used += n;
  return p;
}

// ---- dual-core int8 matvec -------------------------------------------------
static TaskHandle_t worker_h, main_h;
static const QT *job_t;
static const int8_t *job_xq;
static float job_xs;
static float *job_y;
static int job_split;

static void worker_main(void *) {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    matvec_i8_range(job_t, job_xq, job_xs, job_y, 0, job_split);
    xTaskNotifyGive(main_h);
  }
}

static void matvec_par(const QT *t, const float *x, float *y) {
  static int8_t xq[LLM_Q8_MAX_INPUT];
  float xs;
  if (t->w8 == NULL || t->rows < 128) { MATVEC(t, x, y); return; }
  quantize_act(x, t->cols, xq, &xs);
  job_t = t; job_xq = xq; job_xs = xs; job_y = y; job_split = t->rows / 2;
  xTaskNotifyGive(worker_h);
  matvec_i8_range(t, xq, xs, y, job_split, t->rows);
  ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
}

// Copy RMSNorm weights from mapped flash to internal SRAM.
static void copy_norms_to_sram() {
  Cfg *c = &model.c;
  int D = c->dim, L = c->n_layers;
  const float **vecs[3 * 32 + 2];
  int sizes[3 * 32 + 2], n_vec = 0;
    for (int l = 0; l < L; l++) {
    vecs[n_vec] = &model.attn_norm[l]; sizes[n_vec++] = D;
    vecs[n_vec] = &model.ffn_norm[l];  sizes[n_vec++] = D;
      }
  vecs[n_vec] = &model.out_norm; sizes[n_vec++] = D;
  for (int i = 0; i < n_vec; i++) {
    size_t bytes = (size_t)sizes[i] * sizeof(float);
    void *dst = sram_or_die(bytes, "norm vector");
    memcpy(dst, *vecs[i], bytes);
    *vecs[i] = (const float *)dst;
  }
  Serial.printf("norms  -> SRAM   %d vectors\n", n_vec);
}

static void alloc_scratch() {
  Cfg *c = &model.c;
  int D = c->dim, L = c->n_layers, F = c->ffn, S = c->seq_len;
  // hot working set -> internal SRAM
  s.x     = (float *)sram_or_die(D * 4, "x");
  s.h     = (float *)sram_or_die((F > D ? F : D) * 4, "h");
  s.qkv   = (float *)sram_or_die(3 * D * 4, "qkv");
  s.att   = (float *)sram_or_die(D * 4, "att");
  s.g1    = (float *)sram_or_die(F * 4, "g1");
  s.g2    = (float *)sram_or_die(F * 4, "g2");
    s.tmpP  = (float *)sram_or_die(D * 4, "tmpP");
    s.scores = (float *)sram_or_die(S * 4, "scores");
  // logits: out_vocab floats (~99 KiB), read once per token -> PSRAM
  s.logits = (float *)ps_or_die((size_t)model.out_vocab * 4, "logits");
  // KV cache: ~1.1 MB, read once per position -> PSRAM
  s.kcache = (float *)ps_or_die((size_t)L * S * D * 4, "kcache");
  s.vcache = (float *)ps_or_die((size_t)L * S * D * 4, "vcache");
}

static void blink(uint8_t g) {
#ifdef RGB_BUILTIN
  neopixelWrite(RGB_BUILTIN, 0, g, g / 3);
#endif
}

// Emit one token to serial output.
static void emit(int tok) {
  if (tok >= VOCAB_N) return;
  const unsigned char *bytes = VOCAB_BLOB + VOCAB_OFF[tok];
  int len = VOCAB_OFF[tok + 1] - VOCAB_OFF[tok];
  if ((int)Serial.availableForWrite() >= len) Serial.write(bytes, len);
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n=== ESP32-S3 PLE TinyLM ===");

  // Memory-map the model partition (subtype 0x40, name "model").
  const esp_partition_t *part = esp_partition_find_first(
      ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)0x40, "model");
  if (!part) { Serial.println("model partition not found"); return; }
  const void *base;
  spi_flash_mmap_handle_t h;
  esp_err_t err = esp_partition_mmap(part, 0, part->size,
                                     SPI_FLASH_MMAP_DATA, &base, &h);
  if (err != ESP_OK) { Serial.printf("mmap failed: %d\n", err); return; }

  int llm_err = llm_load((const uint8_t *)base, &model);
  if (llm_err) {
    uint32_t m;
    memcpy(&m, base, 4);
    Serial.printf("bad model magic, err %d, read %x\n", llm_err, m);
    Serial.println("bad model magic");
    return;
  }
  Cfg *c = &model.c;
  Serial.printf("model: Vin=%d Vout=%d D=%d L=%d H=%d F=%d P=%d  (mapped %.1f MB)\\n",
                c->vocab, model.out_vocab, c->dim, c->n_layers, c->n_heads,
                c->ffn, c->group, part->size / 1e6);

  // Sanity-check vocab table vs model header.
  if (VOCAB_N != model.out_vocab) {
    Serial.printf("FATAL: tokenizer/model mismatch: vocab.h %d, model %d\n",
                  VOCAB_N, model.out_vocab);
    return;
  }

  alloc_scratch();
  copy_norms_to_sram();
  Serial.printf("hot set-> SRAM   %u B dynamic + %u B static = %u B managed\n",
                (unsigned)sram_used, (unsigned)STATIC_SRAM_BYTES,
                (unsigned)(sram_used + STATIC_SRAM_BYTES));

  // Stage every per-position tensor to int8 in PSRAM.
  int want = llm_core_stage_count(&model);
  int staged = 0; if (model.c.group == 0) { staged = llm_stage_core_int8_alloc(&model, ps); } else { Serial.println("Skipping PSRAM staging for INT4 model"); }
  if (model.c.group == 0 && staged != want) {
    Serial.printf("FATAL: staged %d/%d core tensors\n", staged, want);
    while (1) delay(1000);
  }
  // Stage the tied output head too (85% of dense MACs).
  {
    void *b = heap_caps_malloc(llm_stage_int8_bytes(&model.out_head), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (b) {
      llm_stage_int8(&model.out_head, b);
      ++staged;
    }
  }
  Serial.printf("weights-> PSRAM  %d tensors int8, %.2f MB allocated (out_head %d x %d)\\n",
                staged, psram_used / 1048576.0, model.out_head.rows, model.out_head.cols);

  main_h = xTaskGetCurrentTaskHandle();
  if (xTaskCreatePinnedToCore(worker_main, "mv", 4096, NULL, 2, &worker_h, 0) == pdPASS) {
    model.layer_matvec = matvec_par;
    model.head_matvec  = matvec_par;
  } else {
    Serial.println("dual-core worker failed; running single core");
  }

  // FNV-1a fingerprint of the model image.
  {
    const uint8_t *img = (const uint8_t *)base;
    uint32_t fp = 2166136261u;
    for (size_t i = 0; i < model.image_bytes; i++) { fp ^= img[i]; fp *= 16777619u; }
    Serial.printf("build: bytes=%u fp=%08x sram=%uB psram=%.2fMB\n",
                  (unsigned)model.image_bytes, fp,
                  (unsigned)(sram_used + STATIC_SRAM_BYTES),
                  psram_used / 1048576.0);
  }
  Serial.printf("free: sram %.0f KB | psram %.2f MB\n\n",
                heap_caps_get_free_size(MALLOC_CAP_INTERNAL) / 1024.0,
                heap_caps_get_free_size(MALLOC_CAP_SPIRAM) / 1048576.0);

  // ---- generate ----
  Serial.print(">>> ");
  int n_prompt = sizeof(PROMPT_IDS) / sizeof(int);
  int pos = 0, tok = 0;
  int64_t decode_us = 0;
  int decoded = 0;

  for (int i = 0; i < n_prompt; i++) {   // prime with the prompt
    tok = PROMPT_IDS[i];
    emit(tok); Serial.printf(" [%d] ", tok);
    llm_forward(&model, tok, pos++, &s);
  }

  Serial.println("\n[DEBUG] Priming finished"); llm_profile_reset(&s);

  Serial.printf("\n[DEBUG] seq_len=%d pos=%d N_GENERATE=%d\n", model.c.seq_len, pos, N_GENERATE); int64_t t_start = esp_timer_get_time();
  for (int step = 0; step < N_GENERATE && pos < model.c.seq_len; step++) {
    int best = 0; float bv = -1e30f;
    for (int v = 0; v < model.out_vocab; v++)
      if (s.logits[v] > bv) { bv = s.logits[v]; best = v; }
    tok = best;
    emit(tok);
    if (tok == 2) break;
    blink((step & 1) ? 40 : 8);

    int64_t d0 = esp_timer_get_time();
    llm_forward(&model, tok, pos++, &s);
    decode_us += esp_timer_get_time() - d0;
    decoded++;
    if ((step & 7) == 0) delay(0);  // feed the task WDT ~every 8 tokens
  }
  int64_t total_us = esp_timer_get_time() - t_start;

  Serial.printf("\n\n--- %d tokens in %.2f s ---\n", decoded, total_us / 1e6);
  Serial.printf("throughput: %.2f tok/s   (%.1f ms/token)\n",
                decoded * 1e6 / total_us, decode_us / 1000.0 / decoded);
  if (s.profile.calls) {
    float n = (float)s.profile.calls * 1000.f;
    Serial.printf("profile ms/token: input %.1f | attn %.1f | ffn %.1f | ple %.1f | head %.1f\n",
                  s.profile.input_us / n, s.profile.attn_us / n,
                  s.profile.ffn_us / n, s.profile.ple_us / n,
                  s.profile.head_us / n);
  }
  blink(0);
}

void loop() { delay(10000); }

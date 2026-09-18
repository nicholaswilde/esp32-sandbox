// ESP32-S3 Sourdough Baker Assistant - On-Device PLE INT4 Inference REPL
// Runs offline on ESP32-S3 (N16R8) with model memory-mapped at partition 0x110000.

#include <Arduino.h>
#include "esp_partition.h"
#include "esp_spi_flash.h"
#include "esp_heap_caps.h"
#include "esp_timer.h"

#define LLM_INT8_ACT 1
#define LLM_PROFILE 1
#define LLM_PROFILE_NOW() esp_timer_get_time()

#include "llm.h"
#include "bpe_tokenizer.h"
#include "generated/tokenizer_asset.h"
#include "generated/sourdough_words.h"
#include "generated/sourdough_out2in.h"

// ---- Globals & Buffers -----------------------------------------------------
static Model model;
static Scratch s;
static BpeTokenizer tokenizer;

static size_t psram_used = 0, sram_used = 0;
#define STATIC_SRAM_BYTES (2 * LLM_Q8_MAX_INPUT)

static void *ps_or_die(size_t n, const char *what) {
  void *p = heap_caps_malloc(n, MALLOC_CAP_SPIRAM);
  if (!p) {
    Serial.printf("FATAL: required PSRAM allocation failed: %s (%u bytes)\n", what, (unsigned)n);
    while (1) delay(1000);
  }
  psram_used += n;
  return p;
}

static void *sram_or_die(size_t n, const char *what) {
  void *p = heap_caps_malloc(n, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
  if (!p) {
    Serial.printf("FATAL: required SRAM allocation failed: %s (%u bytes)\n", what, (unsigned)n);
    while (1) delay(1000);
  }
  sram_used += n;
  return p;
}

// ---- Dual-Core Worker for Matvec -------------------------------------------
static TaskHandle_t worker_h, main_h;
static const QT *job_t;
static const int8_t *job_xq;
static float job_xs;
static float *job_y;
static int job_split;

static void worker_main(void *param) {
  (void)param;
  while (1) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    matvec_i8_range(job_t, job_xq, job_xs, job_y, 0, job_split);
    xTaskNotifyGive(main_h);
  }
}

static void matvec_par(const QT *t, const float *x, float *y) {
  static int8_t xq[LLM_Q8_MAX_INPUT];
  float xs;
  if (!t->w8 || t->rows < 64) {
    MATVEC(t, x, y);
    return;
  }
  quantize_act(x, t->cols, xq, &xs);
  job_t = t; job_xq = xq; job_xs = xs; job_y = y;
  job_split = t->rows / 2;
  xTaskNotifyGive(worker_h);
  matvec_i8_range(t, xq, xs, y, job_split, t->rows);
  ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
}

// Copy RMSNorm weights from mapped flash to internal SRAM for speed
static void copy_norms_to_sram() {
  Cfg *c = &model.c;
  int D = c->dim, L = c->n_layers, P = c->ple_dim;
  const float **vecs[4 * 32 + 2];
  int sizes[4 * 32 + 2], n_vec = 0;

  vecs[n_vec] = &model.ple_proj_norm; sizes[n_vec++] = P;
  for (int l = 0; l < L; l++) {
    vecs[n_vec] = &model.attn_norm[l]; sizes[n_vec++] = D;
    vecs[n_vec] = &model.ffn_norm[l];  sizes[n_vec++] = D;
    vecs[n_vec] = &model.ple_norm[l];  sizes[n_vec++] = D;
  }
  vecs[n_vec] = &model.out_norm; sizes[n_vec++] = D;

  for (int i = 0; i < n_vec; i++) {
    size_t bytes = (size_t)sizes[i] * sizeof(float);
    void *dst = sram_or_die(bytes, "norm vector");
    memcpy(dst, *vecs[i], bytes);
    *vecs[i] = (const float *)dst;
  }
  Serial.printf("[s3-sourdough] Copied %d RMSNorm vectors to SRAM\n", n_vec);
}

// ---- Allocation & SRAM Buffers ---------------------------------------------
static void alloc_scratch() {
  Cfg *c = &model.c;
  int D = c->dim, L = c->n_layers, F = c->ffn, P = c->ple_dim, S = c->seq_len;

  s.x      = (float *)sram_or_die(D * 4, "x");
  s.h      = (float *)sram_or_die((F > D ? F : D) * 4, "h");
  s.qkv    = (float *)sram_or_die(3 * D * 4, "qkv");
  s.att    = (float *)sram_or_die(D * 4, "att");
  s.g1     = (float *)sram_or_die(F * 4, "g1");
  s.g2     = (float *)sram_or_die(F * 4, "g2");
  s.ple    = (float *)sram_or_die(L * P * 4, "ple");
  s.tmpP   = (float *)sram_or_die(L * P * 4, "tmpP");
  s.trow   = (float *)sram_or_die(L * P * 4, "trow");
  s.scores = (float *)sram_or_die(S * 4, "scores");

  s.logits = (float *)ps_or_die((size_t)model.out_vocab * 4, "logits");
  s.kcache = (float *)ps_or_die((size_t)L * S * D * 4, "kcache");
  s.vcache = (float *)ps_or_die((size_t)L * S * D * 4, "vcache");
}

static void emit_word(int best, int &pieces_out) {
  if (best < 0 || best >= SOURDOUGH_WORD_COUNT) return;
  const char *w = SOURDOUGH_WORDS[best];
  bool punct = (w[1] == '\0' && strchr(".,:;?%", w[0]) != NULL);
  if (pieces_out && !punct) Serial.print(' ');
  Serial.print(w);
  Serial.flush();
  pieces_out++;
}

// ---- Sampling Helpers ------------------------------------------------------
typedef struct {
  float prob;
  int index;
} ProbIndex;

static ProbIndex *probindex = NULL;
static uint64_t rng_seed = 1337;

static unsigned int random_u32() {
  rng_seed ^= rng_seed >> 12;
  rng_seed ^= rng_seed << 25;
  rng_seed ^= rng_seed >> 27;
  return (rng_seed * 0x2545F4914F6CDD1Dull) >> 32;
}

static float random_f32() {
  return (random_u32() >> 8) / 16777216.0f;
}

static int compare_probindex(const void *a, const void *b) {
  ProbIndex *a_ = (ProbIndex *)a;
  ProbIndex *b_ = (ProbIndex *)b;
  if (a_->prob > b_->prob) return -1;
  if (a_->prob < b_->prob) return 1;
  return 0;
}

static int sample(float *logits, int n, float temperature, float topp, ProbIndex *pindex) {
  if (temperature <= 0.01f) {
    int best = 0; float best_val = -1e30f;
    for (int i = 0; i < n; i++) {
      if (logits[i] > best_val) { best_val = logits[i]; best = i; }
    }
    return best;
  }

  // Softmax
  float max_val = -1e30f;
  for (int i = 0; i < n; i++) {
    if (logits[i] > max_val) max_val = logits[i];
  }
  float sum = 0.0f;
  for (int i = 0; i < n; i++) {
    logits[i] = expf((logits[i] - max_val) / temperature);
    sum += logits[i];
  }
  for (int i = 0; i < n; i++) logits[i] /= sum;

  if (topp <= 0.0f || topp >= 1.0f) {
    float r = random_f32(), cdf = 0.0f;
    for (int i = 0; i < n; i++) {
      cdf += logits[i];
      if (r < cdf) return i;
    }
    return n - 1;
  }

  for (int i = 0; i < n; i++) {
    pindex[i].index = i;
    pindex[i].prob = logits[i];
  }
  qsort(pindex, n, sizeof(ProbIndex), compare_probindex);

  float cumsum = 0.0f;
  int last_idx = n - 1;
  for (int i = 0; i < n; i++) {
    cumsum += pindex[i].prob;
    if (cumsum >= topp) { last_idx = i; break; }
  }

  float r = random_f32() * cumsum, cdf = 0.0f;
  for (int i = 0; i <= last_idx; i++) {
    cdf += pindex[i].prob;
    if (r < cdf) return pindex[i].index;
  }
  return pindex[last_idx].index;
}


// ---- Setup & Inference REPL ------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n=======================================================");
  Serial.println("  🥖 ESP32-S3 Sourdough Baker Assistant (PLE INT4)    ");
  Serial.println("=======================================================");

  // 1. Initialize BPE Tokenizer
  int tok_rc = bpe_tokenizer_load(TOKENIZER_ASSET, TOKENIZER_ASSET_SIZE, &tokenizer);
  if (tok_rc != 0) {
    Serial.printf("FATAL: Failed to load BPE tokenizer asset (code %d)\n", tok_rc);
    while (1) delay(1000);
  }
  Serial.printf("[s3-sourdough] Tokenizer ready: vocab=%u, merges=%u\n",
                tokenizer.active_vocab, tokenizer.merge_count);

  // 2. Memory-map model partition from Flash (0x110000, subtype 0x40)
  const esp_partition_t *part = esp_partition_find_first(
      ESP_PARTITION_TYPE_DATA, (esp_partition_subtype_t)0x40, "model");
  if (!part) {
    Serial.println("FATAL: 'model' partition not found at 0x110000!");
    while (1) delay(1000);
  }

  const void *base = NULL;
  spi_flash_mmap_handle_t mmap_h;
  esp_err_t err = esp_partition_mmap(part, 0, part->size, SPI_FLASH_MMAP_DATA, &base, &mmap_h);
  if (err != ESP_OK) {
    Serial.printf("FATAL: esp_partition_mmap failed: %d\n", err);
    while (1) delay(1000);
  }

  // 3. Load PLE Model
  int llm_err = llm_load((const uint8_t *)base, &model);
  if (llm_err != 0) {
    uint32_t magic; memcpy(&magic, base, 4);
    Serial.printf("FATAL: llm_load error %d (magic: 0x%08x)\n", llm_err, magic);
    while (1) delay(1000);
  }

  Cfg *c = &model.c;
  Serial.printf("[s3-sourdough] Model loaded: vocab=%d, dim=%d, layers=%d, heads=%d, ffn=%d, ple_dim=%d\n",
                c->vocab, c->dim, c->n_layers, c->n_heads, c->ffn, c->ple_dim);

  if (model.out_vocab != SOURDOUGH_WORD_COUNT) {
    Serial.printf("FATAL: word table mismatch: model %d vs table %d\n",
                  model.out_vocab, SOURDOUGH_WORD_COUNT);
    while (1) delay(1000);
  }

  // 4. Allocate Scratch & Relocate Norms
  alloc_scratch();
  copy_norms_to_sram();

  // Stage core weights to int8 in PSRAM for fast matvec
  void *(*ps_alloc_fn)(size_t) = [](size_t n) -> void * {
    void *p = heap_caps_malloc(n, MALLOC_CAP_SPIRAM);
    if (p) psram_used += n;
    return p;
  };
  int want = llm_core_stage_count(&model);
  int staged = llm_stage_core_int8_alloc(&model, ps_alloc_fn);
  void *hb = ps_alloc_fn(llm_stage_int8_bytes(&model.out_head));
  if (hb) {
    llm_stage_int8(&model.out_head, hb);
    staged++;
  }
  Serial.printf("[s3-sourdough] Staged %d core + head tensors to int8 in PSRAM\n", staged);

  // 5. Setup dual-core acceleration
  main_h = xTaskGetCurrentTaskHandle();
  if (xTaskCreatePinnedToCore(worker_main, "matvec_worker", 4096, NULL, 2, &worker_h, 0) == pdPASS) {
    model.layer_matvec = matvec_par;
    if (model.out_head.w8) model.head_matvec = matvec_par;
    Serial.println("[s3-sourdough] Dual-core acceleration enabled (Core 0 + Core 1)");
  }

  probindex = (ProbIndex *)ps_or_die(model.out_vocab * sizeof(ProbIndex), "probindex");

  Serial.printf("[s3-sourdough] Free SRAM: %.1f KB | Free PSRAM: %.2f MB\n",
                heap_caps_get_free_size(MALLOC_CAP_INTERNAL) / 1024.0,
                heap_caps_get_free_size(MALLOC_CAP_SPIRAM) / 1048576.0);
  Serial.println("\nReady! Enter your sourdough question below:\n");
  Serial.print("User: ");
}

void loop() {
  if (!Serial.available()) {
    delay(20);
    return;
  }

  String prompt = Serial.readStringUntil('\n');
  prompt.trim();
  if (prompt.length() == 0) return;

  // Echo user question
  Serial.println(prompt);

  // 1. Encode prompt with on-device BPE tokenizer
  uint16_t prompt_tokens[128];
  int n_prompt = bpe_encode_ascii(&tokenizer, prompt.c_str(), prompt_tokens, 120);
  if (n_prompt < 0) {
    Serial.println("Assistant: Error: Prompt contains unsupported characters or is too long.\n");
    Serial.print("User: ");
    return;
  }

  Serial.print("Assistant: ");
  llm_profile_reset(&s);

  int pos = 0;
  // 2. Prime KV cache with prompt tokens
  for (int i = 0; i < n_prompt; i++) {
    llm_forward(&model, prompt_tokens[i], pos++, &s);
  }
  // 3. Feed BOS token
  llm_forward(&model, SOURDOUGH_OUT2IN[SOURDOUGH_BOS], pos++, &s);

  // 4. Autoregressive whole-word generation
  int64_t t0 = esp_timer_get_time();
  int pieces_out = 0;
  int max_pieces = 60;
  int recent[8] = {-1, -1, -1, -1, -1, -1, -1, -1};

  for (int step = 0; step < max_pieces && pos < model.c.seq_len; step++) {
    // Mild repetition penalty on recently emitted classes
    for (int r = 0; r < 8; r++) {
      int prev = recent[r];
      if (prev >= 0 && prev < SOURDOUGH_WORD_COUNT) {
        if (s.logits[prev] > 0) s.logits[prev] *= 0.85f;
        else s.logits[prev] *= 1.15f;
      }
    }

    // Greedy decoding over output classes
    int best = 0;
    for (int k = 1; k < SOURDOUGH_WORD_COUNT; k++) {
      if (s.logits[k] > s.logits[best]) best = k;
    }
    if (best == SOURDOUGH_EOS) break;
    recent[step % 8] = best;

    emit_word(best, pieces_out);
    llm_forward(&model, SOURDOUGH_OUT2IN[best], pos++, &s);
  }

  int64_t total_us = esp_timer_get_time() - t0;
  float tok_per_sec = (total_us > 0) ? (pieces_out * 1e6f / total_us) : 0.0f;

  Serial.printf("\n\n[%d words in %.2f s, %.1f words/s]\n", pieces_out, total_us / 1e6f, tok_per_sec);
  Serial.print("\nUser: ");
}

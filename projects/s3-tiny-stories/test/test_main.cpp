#include <unity.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "llm.h"
#include "generated/vocab.h"

void setUp(void) {}
void tearDown(void) {}

void test_vocab_constants(void) {
    TEST_ASSERT_EQUAL_INT(25353, VOCAB_N);
    // Token 433 is "Once"
    int tok_once = 433;
    const unsigned char *b_once = VOCAB_BLOB + VOCAB_OFF[tok_once];
    int len_once = VOCAB_OFF[tok_once + 1] - VOCAB_OFF[tok_once];
    char buf[16] = {0};
    memcpy(buf, b_once, len_once);
    TEST_ASSERT_EQUAL_STRING("Once", buf);

    // Prompt tokens: 433="Once", 447=" upon", 259=" a", 405=" time"
    const int prompt_ids[] = {433, 447, 259, 405};
    char prompt_buf[64] = {0};
    int offset = 0;
    for (int i = 0; i < 4; i++) {
        int id = prompt_ids[i];
        const unsigned char *b = VOCAB_BLOB + VOCAB_OFF[id];
        int len = VOCAB_OFF[id + 1] - VOCAB_OFF[id];
        memcpy(prompt_buf + offset, b, len);
        offset += len;
    }
    prompt_buf[offset] = '\0';
    TEST_ASSERT_EQUAL_STRING("Once upon a time", prompt_buf);
}

void test_llm_magic_and_config(void) {
    TEST_ASSERT_EQUAL_HEX32(0x00454C50u, LLM_MAGIC);
    TEST_ASSERT_EQUAL_UINT32(56u, LLM_HEADER_BYTES);
}

void test_model_bin_load(void) {
    FILE *f = fopen("pc_tools/model.bin", "rb");
    if (!f) {
        TEST_IGNORE_MESSAGE("pc_tools/model.bin not found on native path; skipping binary load test");
        return;
    }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    TEST_ASSERT_GREATER_THAN(10000000, sz);

    uint8_t *buf = (uint8_t *)malloc(sz);
    TEST_ASSERT_NOT_NULL(buf);
    size_t read_bytes = fread(buf, 1, sz, f);
    fclose(f);
    TEST_ASSERT_EQUAL_UINT32(sz, read_bytes);

    Model model;
    int rc = llm_load(buf, &model);
    TEST_ASSERT_EQUAL_INT(0, rc);
    TEST_ASSERT_EQUAL_INT(32768, model.c.vocab);
    TEST_ASSERT_EQUAL_INT(25353, model.out_vocab);
    TEST_ASSERT_GREATER_THAN(0, model.c.dim);
    TEST_ASSERT_GREATER_THAN(0, model.c.n_layers);
    TEST_ASSERT_GREATER_THAN(0, model.c.n_heads);
    TEST_ASSERT_GREATER_THAN(0, model.c.ffn);
    TEST_ASSERT_GREATER_THAN(0, model.c.ple_dim);
    TEST_ASSERT_GREATER_THAN(0, model.c.seq_len);

    free(buf);
}

int main(int argc, char **argv) {
    UNITY_BEGIN();
    RUN_TEST(test_vocab_constants);
    RUN_TEST(test_llm_magic_and_config);
    RUN_TEST(test_model_bin_load);
    return UNITY_END();
}

#include <unity.h>
#include "bpe_tokenizer.h"
#include "generated/tokenizer_asset.h"
#include "generated/vocab.h"

void test_bpe_encoder() {
    BpeTokenizer tok;
    int rc = bpe_tokenizer_load(TOKENIZER_ASSET, TOKENIZER_ASSET_SIZE, &tok);
    TEST_ASSERT_EQUAL_INT(0, rc);
    TEST_ASSERT_EQUAL_UINT32(2048, tok.active_vocab);
    TEST_ASSERT_EQUAL_UINT32(1791, tok.merge_count);

    uint16_t out[128];
    int n = bpe_encode_ascii(&tok, "Why is my bread gummy?", out, 128);
    TEST_ASSERT_EQUAL_INT(8, n);
    uint16_t expected[8] = {55, 72, 89, 333, 455, 458, 1237, 31};
    for (int i = 0; i < 8; i++) {
        TEST_ASSERT_EQUAL_UINT16(expected[i], out[i]);
    }
}

int main(int argc, char **argv) {
    UNITY_BEGIN();
    RUN_TEST(test_bpe_encoder);
    UNITY_END();
    return 0;
}

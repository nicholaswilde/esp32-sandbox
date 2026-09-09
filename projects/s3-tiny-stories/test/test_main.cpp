#include <unity.h>

void test_dummy() { TEST_ASSERT_EQUAL(1, 1); }

int main(int argc, char **argv) {
    UNITY_BEGIN();
    RUN_TEST(test_dummy);
    UNITY_END();
    return 0;
}

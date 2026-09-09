#include <stdint.h>
#include <stddef.h>

#include "voiage_v1.h"

_Static_assert(sizeof(VoiageAbiVersionV1) == 12, "version layout changed");
_Static_assert(sizeof(VoiageAbiCapabilitiesV1) == 16, "capability layout changed");
_Static_assert(sizeof(VoiageHandleV1) == 8, "handle width changed");

int main(void) {
    const double values[4] = {10.0, 1.0, 2.0, 8.0};
    double result = 0.0;
    int32_t status = 0;
    int32_t rows = 2;
    int32_t columns = 2;
    VoiageHandleV1 handle = VOIAGE_V1_NULL_HANDLE;

    (void)voiage_v1_abi_version();
    (void)voiage_v1_capabilities();
    (void)voiage_v1_evpi(values, 2, 2, &result);
    (void)voiage_v1_enbs(1.0, 0.5, &result);
    voiage_v1_enbs_r(&result, &result, &result, &status);
    (void)voiage_v1_evpi_i32(values, rows, columns, &result);
    voiage_v1_evpi_i32_r(values, &rows, &columns, &result, &status);
    (void)voiage_v1_handle_create(&handle);
    (void)voiage_v1_handle_free(handle);
    (void)voiage_v1_error_message(NULL, 0, NULL);
    return 0;
}

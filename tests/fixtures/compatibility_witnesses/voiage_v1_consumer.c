#include <stdint.h>
#include <stddef.h>

#include "voiage_v1.h"

_Static_assert(sizeof(VoiageAbiVersionV1) == 12, "version layout changed");
_Static_assert(sizeof(VoiageAbiCapabilitiesV1) == 16, "capability layout changed");
_Static_assert(sizeof(VoiageHandleV1) == 8, "handle width changed");

int main(void) {
    const double values[4] = {10.0, 1.0, 2.0, 8.0};
    double evsi_result = 1.0;
    double research_cost = 0.5;
    double result = 0.0;
    int32_t enbs_status = 0;
    int32_t evpi_status = 0;
    int32_t rows = 2;
    int32_t columns = 2;
    VoiageHandleV1 handle = VOIAGE_V1_NULL_HANDLE;
    VoiageAbiVersionV1 (*version_query)(void) = voiage_v1_abi_version;
    VoiageAbiCapabilitiesV1 (*capabilities_query)(void) = voiage_v1_capabilities;
    voiage_v1_status (*evpi_query)(const double *, uint64_t, uint64_t, double *) =
        voiage_v1_evpi;
    voiage_v1_status (*enbs_query)(double, double, double *) = voiage_v1_enbs;
    void (*enbs_r_query)(const double *, const double *, double *, int32_t *) =
        voiage_v1_enbs_r;
    voiage_v1_status (*evpi_i32_query)(const double *, int32_t, int32_t, double *) =
        voiage_v1_evpi_i32;
    void (*evpi_i32_r_query)(const double *, const int32_t *, const int32_t *, double *, int32_t *) =
        voiage_v1_evpi_i32_r;
    voiage_v1_status (*handle_create_query)(VoiageHandleV1 *) = voiage_v1_handle_create;
    voiage_v1_status (*handle_free_query)(VoiageHandleV1) = voiage_v1_handle_free;
    voiage_v1_status (*error_message_query)(char *, uint64_t, uint64_t *) =
        voiage_v1_error_message;

    (void)version_query();
    (void)capabilities_query();
    (void)evpi_query(values, 2, 2, &result);
    (void)enbs_query(evsi_result, research_cost, &result);
    enbs_r_query(&evsi_result, &research_cost, &result, &enbs_status);
    (void)evpi_i32_query(values, rows, columns, &result);
    evpi_i32_r_query(values, &rows, &columns, &result, &evpi_status);
    if (handle_create_query(&handle) == VOIAGE_V1_STATUS_OK) {
        (void)handle_free_query(handle);
    }
    (void)error_message_query(NULL, 0, NULL);
    return 0;
}

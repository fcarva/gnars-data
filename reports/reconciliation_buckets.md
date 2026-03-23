# Reconciliation Buckets

## Inputs
- funding_total_usd: 575,223.00
- onchain_inflow_usd: 346,977.49
- onchain_outflow_usd: 396,254.25
- onchain_net_usd: -49,276.76
- expected_balance_funding_model_usd: 178,969.00
- actual_balance_usd: 44,737.00

## Buckets
- inflow_missing_usd: 228,245.51
- outflow_explained_onchain_usd: 396,254.25
- initial_balance_adjustment_usd: 94,013.76
- signed_gap_actual_minus_expected_usd: -134,232.00
- signed_gap_identity_rhs_usd: -134,231.75
- identity_holds: True

## Identity
- actual - expected = initial_balance_adjustment - inflow_missing

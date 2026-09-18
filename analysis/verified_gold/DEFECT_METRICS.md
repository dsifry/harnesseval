# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators are computed from the registry (see _final in analysis/verified_gold/DEFECT_REGISTRY.json): verified = 42 goldens + every D-verified defect (105 after the 2026-09-18 withdrawal/dedup audit — 3 withdrawn, 2 merged; see WITHDRAWALS_AND_DEDUP_2026-09-18.md); reachable = 42 + only those D-verified defects that some run actually reported (1 verified defect is reported by no run and cap recall for everyone); full = 42 + all registry defects. The assignment map covers every finding (null = no clear match; see DEFECT_ASSIGN.md and DEFECT_ASSIGN_AUDIT.json). Nitpick counts from cells whose instruments include 'v1' are structurally unmeasured (the binary instrument has no important_non_bug category), not observed zeros. recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' | instruments |
|---|---|---|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.367 [0.269, 0.484] | 0.701 | 0.701 | 0.482 | 0.482 | 0.406 | 0.406 | v1 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.320 [0.277, 0.382] | 0.959 | 0.904 | 0.480 | 0.472 | 0.369 | 0.367 | rj3 |
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.347 [0.256, 0.473] | 0.708 | 0.708 | 0.466 | 0.466 | 0.386 | 0.386 | v1 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.333 [0.274, 0.411] | 0.860 | 0.754 | 0.480 | 0.462 | 0.380 | 0.375 | rj3/v2 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.463 [0.417, 0.537] | 0.673 | 0.450 | 0.548 | 0.456 | 0.493 | 0.460 | v2 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.517 [0.469, 0.594] | 0.916 | 0.400 | 0.661 | 0.451 | 0.566 | 0.488 | v2 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.463 [0.388, 0.568] | 0.907 | 0.439 | 0.613 | 0.450 | 0.513 | 0.458 | v2 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.481 [0.481, 0.481] | 0.867 | 0.419 | 0.619 | 0.448 | 0.528 | 0.468 | v2 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.490 [0.406, 0.607] | 0.809 | 0.404 | 0.610 | 0.443 | 0.532 | 0.470 | v2 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.531 [0.439, 0.663] | 0.929 | 0.377 | 0.675 | 0.441 | 0.580 | 0.491 | v2 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.519 [0.519, 0.519] | 0.700 | 0.378 | 0.596 | 0.438 | 0.547 | 0.483 | v2 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.361 [0.303, 0.450] | 0.736 | 0.552 | 0.484 | 0.436 | 0.402 | 0.387 | v2 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.544 [0.477, 0.691] | 0.792 | 0.362 | 0.645 | 0.435 | 0.581 | 0.494 | v2 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.361 [0.270, 0.496] | 0.716 | 0.546 | 0.480 | 0.434 | 0.400 | 0.387 | v2 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.320 [0.250, 0.436] | 0.959 | 0.671 | 0.480 | 0.433 | 0.369 | 0.357 | rj3 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.333 [0.259, 0.458] | 0.790 | 0.613 | 0.469 | 0.432 | 0.377 | 0.367 | v2 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.313 [0.245, 0.415] | 0.958 | 0.687 | 0.472 | 0.430 | 0.362 | 0.351 | rj3/v2 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.299 [0.208, 0.445] | 1.000 | 0.759 | 0.461 | 0.429 | 0.348 | 0.341 | v2 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.293 [0.266, 0.328] | 0.915 | 0.796 | 0.443 | 0.428 | 0.339 | 0.335 | rj3/v2 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.327 [0.256, 0.455] | 0.593 | 0.593 | 0.421 | 0.421 | 0.359 | 0.359 | v1 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.497 [0.397, 0.646] | 0.924 | 0.363 | 0.646 | 0.420 | 0.547 | 0.463 | v2 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.476 [0.392, 0.613] | 0.897 | 0.365 | 0.622 | 0.413 | 0.526 | 0.449 | v2 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.293 [0.219, 0.418] | 0.860 | 0.672 | 0.437 | 0.408 | 0.337 | 0.330 | v2 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.259 [0.193, 0.336] | 0.974 | 0.950 | 0.409 | 0.406 | 0.303 | 0.303 | v2 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.293 [0.207, 0.418] | 0.977 | 0.632 | 0.450 | 0.400 | 0.340 | 0.328 | v2 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.279 [0.226, 0.385] | 0.911 | 0.695 | 0.427 | 0.398 | 0.324 | 0.317 | rj3/v2 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.286 [0.235, 0.355] | 0.933 | 0.646 | 0.437 | 0.396 | 0.332 | 0.322 | rj3 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.320 [0.245, 0.421] | 0.734 | 0.505 | 0.445 | 0.392 | 0.360 | 0.345 | v2 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.503 [0.466, 0.571] | 0.592 | 0.318 | 0.544 | 0.389 | 0.519 | 0.451 | v2 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.299 [0.224, 0.400] | 0.863 | 0.550 | 0.444 | 0.388 | 0.344 | 0.329 | rj3 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.444 [0.444, 0.444] | 0.632 | 0.343 | 0.522 | 0.387 | 0.472 | 0.420 | v2 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.429 [0.372, 0.533] | 0.768 | 0.346 | 0.550 | 0.383 | 0.470 | 0.409 | v2 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.483 [0.391, 0.653] | 0.703 | 0.313 | 0.573 | 0.380 | 0.515 | 0.436 | v2 |
| gpt-6-astra · compound-realistic · low | 6 | 0.272 [0.218, 0.394] | 0.800 | 0.625 | 0.406 | 0.379 | 0.313 | 0.307 | rj3/v2 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.483 [0.401, 0.619] | 0.592 | 0.307 | 0.532 | 0.376 | 0.501 | 0.433 | v2 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.231 [0.163, 0.318] | 1.000 | 0.971 | 0.376 | 0.374 | 0.273 | 0.273 | v2 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.401 [0.336, 0.515] | 0.808 | 0.341 | 0.536 | 0.369 | 0.446 | 0.388 | v2 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.429 [0.350, 0.562] | 0.600 | 0.321 | 0.500 | 0.367 | 0.455 | 0.402 | v2 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.556 [0.556, 0.556] | 0.600 | 0.273 | 0.577 | 0.366 | 0.564 | 0.460 | v2 |
| gpt-6-astra · compound-realistic · high | 6 | 0.245 [0.197, 0.340] | 0.818 | 0.706 | 0.377 | 0.364 | 0.285 | 0.282 | rj3/v2 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.265 [0.195, 0.382] | 0.722 | 0.557 | 0.388 | 0.359 | 0.304 | 0.296 | v2 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.259 [0.198, 0.355] | 0.731 | 0.576 | 0.382 | 0.357 | 0.297 | 0.291 | v2 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.218 [0.151, 0.314] | 0.970 | 0.941 | 0.356 | 0.354 | 0.258 | 0.257 | v2 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.395 [0.286, 0.582] | 0.763 | 0.314 | 0.520 | 0.349 | 0.437 | 0.375 | v2 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.286 [0.214, 0.402] | 0.737 | 0.447 | 0.412 | 0.349 | 0.326 | 0.308 | v2 |
| claude-opus-5 · compound-realistic · low | 6 | 0.442 [0.365, 0.567] | 0.602 | 0.283 | 0.510 | 0.345 | 0.467 | 0.397 | v2 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.599 [0.506, 0.714] | 0.518 | 0.239 | 0.555 | 0.342 | 0.580 | 0.460 | v2 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.481 [0.481, 0.481] | 0.591 | 0.260 | 0.531 | 0.338 | 0.500 | 0.411 | v2 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.377 [0.340, 0.444] | 0.558 | 0.293 | 0.450 | 0.330 | 0.403 | 0.356 | v2 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.422 [0.319, 0.575] | 0.653 | 0.270 | 0.512 | 0.329 | 0.454 | 0.379 | v2 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.245 [0.190, 0.319] | 0.766 | 0.500 | 0.371 | 0.329 | 0.283 | 0.273 | v2 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.224 [0.165, 0.324] | 0.846 | 0.579 | 0.355 | 0.324 | 0.263 | 0.256 | v2 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.231 [0.179, 0.323] | 0.810 | 0.523 | 0.360 | 0.321 | 0.270 | 0.260 | v2 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.340 [0.242, 0.500] | 0.562 | 0.281 | 0.424 | 0.308 | 0.369 | 0.326 | v2 |
| claude-opus-5 · compound-realistic · high | 6 | 0.422 [0.341, 0.542] | 0.496 | 0.238 | 0.456 | 0.305 | 0.435 | 0.366 | v2 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.204 [0.163, 0.250] | 0.938 | 0.556 | 0.335 | 0.299 | 0.242 | 0.234 | v2 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.204 [0.124, 0.280] | 0.732 | 0.508 | 0.319 | 0.291 | 0.238 | 0.232 | v2 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.177 [0.117, 0.274] | 0.963 | 0.743 | 0.299 | 0.286 | 0.211 | 0.209 | rj3 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.184 [0.143, 0.248] | 0.659 | 0.574 | 0.287 | 0.278 | 0.215 | 0.213 | v2 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.156 [0.097, 0.245] | 1.000 | 1.000 | 0.271 | 0.271 | 0.188 | 0.188 | rj3 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.170 [0.099, 0.269] | 0.806 | 0.641 | 0.281 | 0.269 | 0.202 | 0.199 | rj3 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.150 [0.092, 0.234] | 0.957 | 0.957 | 0.259 | 0.259 | 0.180 | 0.180 | rj3 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.163 [0.091, 0.274] | 0.774 | 0.545 | 0.270 | 0.251 | 0.194 | 0.190 | rj3 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.143 [0.103, 0.202] | 1.000 | 1.000 | 0.250 | 0.250 | 0.172 | 0.172 | rj3/v2 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.245 [0.190, 0.333] | 0.480 | 0.237 | 0.324 | 0.241 | 0.271 | 0.243 | v2 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.136 [0.080, 0.215] | 1.000 | 1.000 | 0.240 | 0.240 | 0.164 | 0.164 | v2 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.136 [0.090, 0.208] | 1.000 | 1.000 | 0.240 | 0.240 | 0.164 | 0.164 | v2 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.129 [0.076, 0.198] | 0.950 | 0.950 | 0.228 | 0.228 | 0.156 | 0.156 | v2 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.245 [0.194, 0.330] | 0.387 | 0.198 | 0.300 | 0.219 | 0.264 | 0.234 | v2 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.143 [0.082, 0.193] | 0.875 | 0.344 | 0.246 | 0.202 | 0.172 | 0.162 | v2 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.109 [0.032, 0.215] | 0.696 | 0.364 | 0.188 | 0.168 | 0.131 | 0.127 | v2 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.102 [0.051, 0.166] | 0.750 | 0.357 | 0.180 | 0.159 | 0.123 | 0.119 | v2 |

MRV-vs-CE on ΔF1': 6/21 pairs resolve positive (CI lower bound > 0). On ΔF2' (our evaluator): 7/21. Point estimates: 17/21 positive on ΔF1', 17/21 on ΔF2'.

## variant: reachable

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' | instruments |
|---|---|---|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.370 [0.269, 0.495] | 0.701 | 0.701 | 0.484 | 0.484 | 0.408 | 0.408 | v1 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.322 [0.278, 0.387] | 0.959 | 0.904 | 0.482 | 0.475 | 0.371 | 0.369 | rj3 |
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.349 [0.259, 0.481] | 0.708 | 0.708 | 0.468 | 0.468 | 0.389 | 0.389 | v1 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.336 [0.281, 0.413] | 0.860 | 0.754 | 0.483 | 0.464 | 0.382 | 0.378 | rj3/v2 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.466 [0.419, 0.551] | 0.673 | 0.450 | 0.551 | 0.458 | 0.496 | 0.463 | v2 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.521 [0.471, 0.606] | 0.916 | 0.400 | 0.664 | 0.452 | 0.570 | 0.491 | v2 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.466 [0.388, 0.579] | 0.907 | 0.439 | 0.615 | 0.452 | 0.516 | 0.460 | v2 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.481 [0.481, 0.481] | 0.867 | 0.419 | 0.619 | 0.448 | 0.528 | 0.468 | v2 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.493 [0.408, 0.610] | 0.809 | 0.404 | 0.613 | 0.444 | 0.535 | 0.472 | v2 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.534 [0.441, 0.675] | 0.929 | 0.377 | 0.678 | 0.442 | 0.584 | 0.493 | v2 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.363 [0.305, 0.455] | 0.736 | 0.552 | 0.486 | 0.438 | 0.404 | 0.390 | v2 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.519 [0.519, 0.519] | 0.700 | 0.378 | 0.596 | 0.438 | 0.547 | 0.483 | v2 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.363 [0.272, 0.505] | 0.716 | 0.546 | 0.482 | 0.436 | 0.403 | 0.389 | v2 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.548 [0.477, 0.699] | 0.792 | 0.362 | 0.648 | 0.436 | 0.584 | 0.497 | v2 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.322 [0.249, 0.441] | 0.959 | 0.671 | 0.482 | 0.435 | 0.371 | 0.359 | rj3 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.336 [0.258, 0.467] | 0.790 | 0.613 | 0.471 | 0.434 | 0.379 | 0.369 | v2 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.315 [0.246, 0.419] | 0.958 | 0.687 | 0.474 | 0.432 | 0.364 | 0.353 | rj3/v2 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.301 [0.210, 0.453] | 1.000 | 0.759 | 0.463 | 0.431 | 0.350 | 0.343 | v2 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.295 [0.269, 0.331] | 0.915 | 0.796 | 0.446 | 0.430 | 0.341 | 0.337 | rj3/v2 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.329 [0.258, 0.455] | 0.593 | 0.593 | 0.423 | 0.423 | 0.361 | 0.361 | v1 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.500 [0.397, 0.650] | 0.924 | 0.363 | 0.649 | 0.421 | 0.551 | 0.465 | v2 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.479 [0.393, 0.629] | 0.897 | 0.365 | 0.625 | 0.414 | 0.529 | 0.451 | v2 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.295 [0.221, 0.419] | 0.860 | 0.672 | 0.439 | 0.410 | 0.339 | 0.332 | v2 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.260 [0.195, 0.341] | 0.974 | 0.950 | 0.411 | 0.409 | 0.305 | 0.304 | v2 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.295 [0.207, 0.420] | 0.977 | 0.632 | 0.453 | 0.402 | 0.342 | 0.330 | v2 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.281 [0.226, 0.394] | 0.911 | 0.695 | 0.429 | 0.400 | 0.326 | 0.319 | rj3/v2 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.288 [0.236, 0.363] | 0.933 | 0.646 | 0.440 | 0.398 | 0.334 | 0.324 | rj3 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.322 [0.248, 0.423] | 0.734 | 0.505 | 0.448 | 0.393 | 0.363 | 0.347 | v2 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.507 [0.467, 0.578] | 0.592 | 0.318 | 0.546 | 0.391 | 0.522 | 0.453 | v2 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.301 [0.224, 0.416] | 0.863 | 0.550 | 0.447 | 0.389 | 0.346 | 0.331 | rj3 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.444 [0.444, 0.444] | 0.632 | 0.343 | 0.522 | 0.387 | 0.472 | 0.420 | v2 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.432 [0.371, 0.546] | 0.768 | 0.346 | 0.553 | 0.384 | 0.473 | 0.411 | v2 |
| gpt-6-astra · compound-realistic · low | 6 | 0.274 [0.218, 0.400] | 0.800 | 0.625 | 0.408 | 0.381 | 0.315 | 0.309 | rj3/v2 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.486 [0.393, 0.660] | 0.703 | 0.313 | 0.575 | 0.381 | 0.518 | 0.438 | v2 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.486 [0.402, 0.625] | 0.592 | 0.307 | 0.534 | 0.377 | 0.504 | 0.436 | v2 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.233 [0.163, 0.323] | 1.000 | 0.971 | 0.378 | 0.376 | 0.275 | 0.275 | v2 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.404 [0.337, 0.526] | 0.808 | 0.341 | 0.539 | 0.370 | 0.449 | 0.390 | v2 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.432 [0.348, 0.560] | 0.600 | 0.321 | 0.502 | 0.368 | 0.457 | 0.404 | v2 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.556 [0.556, 0.556] | 0.600 | 0.273 | 0.577 | 0.366 | 0.564 | 0.460 | v2 |
| gpt-6-astra · compound-realistic · high | 6 | 0.247 [0.197, 0.347] | 0.818 | 0.706 | 0.379 | 0.365 | 0.287 | 0.283 | rj3/v2 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.267 [0.196, 0.396] | 0.722 | 0.557 | 0.390 | 0.361 | 0.306 | 0.298 | v2 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.260 [0.200, 0.366] | 0.731 | 0.576 | 0.384 | 0.358 | 0.299 | 0.292 | v2 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.219 [0.152, 0.318] | 0.970 | 0.941 | 0.358 | 0.356 | 0.259 | 0.259 | v2 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.397 [0.283, 0.588] | 0.763 | 0.314 | 0.523 | 0.350 | 0.439 | 0.377 | v2 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.288 [0.216, 0.407] | 0.737 | 0.447 | 0.414 | 0.350 | 0.328 | 0.310 | v2 |
| claude-opus-5 · compound-realistic · low | 6 | 0.445 [0.369, 0.577] | 0.602 | 0.283 | 0.512 | 0.346 | 0.470 | 0.399 | v2 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.603 [0.512, 0.719] | 0.518 | 0.239 | 0.557 | 0.342 | 0.584 | 0.462 | v2 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.481 [0.481, 0.481] | 0.591 | 0.260 | 0.531 | 0.338 | 0.500 | 0.411 | v2 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.247 [0.190, 0.323] | 0.766 | 0.500 | 0.373 | 0.330 | 0.285 | 0.274 | v2 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.425 [0.321, 0.584] | 0.653 | 0.270 | 0.515 | 0.330 | 0.457 | 0.381 | v2 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.377 [0.340, 0.444] | 0.558 | 0.293 | 0.450 | 0.330 | 0.403 | 0.356 | v2 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.226 [0.166, 0.330] | 0.846 | 0.579 | 0.357 | 0.325 | 0.265 | 0.257 | v2 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.233 [0.181, 0.333] | 0.810 | 0.523 | 0.362 | 0.322 | 0.272 | 0.262 | v2 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.342 [0.242, 0.511] | 0.562 | 0.281 | 0.426 | 0.309 | 0.371 | 0.328 | v2 |
| claude-opus-5 · compound-realistic · high | 6 | 0.425 [0.344, 0.548] | 0.496 | 0.238 | 0.458 | 0.305 | 0.437 | 0.367 | v2 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.205 [0.163, 0.250] | 0.938 | 0.556 | 0.337 | 0.300 | 0.244 | 0.235 | v2 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.205 [0.124, 0.283] | 0.732 | 0.508 | 0.321 | 0.293 | 0.240 | 0.233 | v2 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.178 [0.115, 0.276] | 0.963 | 0.743 | 0.301 | 0.287 | 0.213 | 0.210 | rj3 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.185 [0.143, 0.253] | 0.659 | 0.574 | 0.289 | 0.280 | 0.216 | 0.214 | v2 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.158 [0.097, 0.247] | 1.000 | 1.000 | 0.272 | 0.272 | 0.189 | 0.189 | rj3 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.171 [0.097, 0.271] | 0.806 | 0.641 | 0.282 | 0.270 | 0.203 | 0.201 | rj3 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.151 [0.093, 0.236] | 0.957 | 0.957 | 0.260 | 0.260 | 0.181 | 0.181 | rj3 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.164 [0.092, 0.276] | 0.774 | 0.545 | 0.271 | 0.253 | 0.195 | 0.191 | rj3 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.144 [0.104, 0.206] | 1.000 | 1.000 | 0.251 | 0.251 | 0.174 | 0.174 | rj3/v2 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.247 [0.191, 0.341] | 0.480 | 0.237 | 0.326 | 0.242 | 0.273 | 0.245 | v2 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.137 [0.080, 0.222] | 1.000 | 1.000 | 0.241 | 0.241 | 0.166 | 0.166 | v2 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.137 [0.091, 0.211] | 1.000 | 1.000 | 0.241 | 0.241 | 0.166 | 0.166 | v2 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.130 [0.076, 0.200] | 0.950 | 0.950 | 0.229 | 0.229 | 0.157 | 0.157 | v2 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.247 [0.192, 0.333] | 0.387 | 0.198 | 0.301 | 0.220 | 0.266 | 0.235 | v2 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.144 [0.083, 0.196] | 0.875 | 0.344 | 0.247 | 0.203 | 0.173 | 0.163 | v2 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.110 [0.032, 0.218] | 0.696 | 0.364 | 0.189 | 0.168 | 0.132 | 0.127 | v2 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.103 [0.052, 0.169] | 0.750 | 0.357 | 0.181 | 0.160 | 0.124 | 0.120 | v2 |

MRV-vs-CE on ΔF1': 6/21 pairs resolve positive (CI lower bound > 0). On ΔF2' (our evaluator): 7/21. Point estimates: 17/21 positive on ΔF1', 17/21 on ΔF2'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' | instruments |
|---|---|---|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.355 [0.259, 0.474] | 0.701 | 0.701 | 0.472 | 0.472 | 0.394 | 0.394 | v1 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.309 [0.269, 0.371] | 0.959 | 0.904 | 0.468 | 0.461 | 0.358 | 0.356 | rj3 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.467 [0.403, 0.567] | 0.910 | 0.449 | 0.617 | 0.458 | 0.517 | 0.463 | v2 |
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.336 [0.249, 0.458] | 0.708 | 0.708 | 0.455 | 0.455 | 0.375 | 0.375 | v1 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.454 [0.398, 0.532] | 0.676 | 0.454 | 0.543 | 0.454 | 0.486 | 0.454 | v2 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.513 [0.468, 0.594] | 0.918 | 0.406 | 0.658 | 0.453 | 0.563 | 0.488 | v2 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.322 [0.270, 0.400] | 0.860 | 0.754 | 0.469 | 0.452 | 0.368 | 0.364 | rj3/v2 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.481 [0.481, 0.481] | 0.867 | 0.419 | 0.619 | 0.448 | 0.528 | 0.468 | v2 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.526 [0.441, 0.663] | 0.930 | 0.383 | 0.672 | 0.443 | 0.576 | 0.490 | v2 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.480 [0.408, 0.592] | 0.811 | 0.408 | 0.603 | 0.441 | 0.523 | 0.464 | v2 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.519 [0.519, 0.519] | 0.700 | 0.378 | 0.596 | 0.438 | 0.547 | 0.483 | v2 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.533 [0.471, 0.670] | 0.794 | 0.365 | 0.638 | 0.433 | 0.570 | 0.488 | v2 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.349 [0.294, 0.442] | 0.736 | 0.552 | 0.473 | 0.427 | 0.390 | 0.376 | v2 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.309 [0.250, 0.407] | 0.959 | 0.691 | 0.468 | 0.427 | 0.358 | 0.348 | rj3/v2 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.296 [0.214, 0.434] | 1.000 | 0.763 | 0.457 | 0.427 | 0.345 | 0.337 | v2 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.349 [0.262, 0.496] | 0.716 | 0.546 | 0.469 | 0.426 | 0.389 | 0.376 | v2 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.309 [0.240, 0.419] | 0.959 | 0.671 | 0.468 | 0.423 | 0.358 | 0.347 | rj3 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.493 [0.395, 0.641] | 0.926 | 0.369 | 0.644 | 0.423 | 0.544 | 0.462 | v2 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.322 [0.249, 0.458] | 0.790 | 0.613 | 0.458 | 0.422 | 0.366 | 0.356 | v2 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.322 [0.250, 0.451] | 0.598 | 0.598 | 0.419 | 0.419 | 0.355 | 0.355 | v1 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.283 [0.259, 0.319] | 0.915 | 0.796 | 0.432 | 0.417 | 0.328 | 0.325 | rj3/v2 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.467 [0.394, 0.590] | 0.899 | 0.368 | 0.615 | 0.412 | 0.517 | 0.443 | v2 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.289 [0.206, 0.390] | 0.978 | 0.638 | 0.447 | 0.398 | 0.337 | 0.325 | v2 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.283 [0.212, 0.400] | 0.860 | 0.672 | 0.426 | 0.398 | 0.327 | 0.320 | v2 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.250 [0.187, 0.333] | 0.974 | 0.950 | 0.398 | 0.396 | 0.294 | 0.293 | v2 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.434 [0.386, 0.526] | 0.776 | 0.357 | 0.557 | 0.392 | 0.476 | 0.416 | v2 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.316 [0.252, 0.407] | 0.738 | 0.511 | 0.442 | 0.390 | 0.357 | 0.342 | v2 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.270 [0.215, 0.380] | 0.911 | 0.695 | 0.416 | 0.389 | 0.314 | 0.307 | rj3/v2 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.493 [0.456, 0.563] | 0.595 | 0.321 | 0.540 | 0.389 | 0.511 | 0.445 | v2 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.276 [0.226, 0.347] | 0.933 | 0.646 | 0.426 | 0.387 | 0.322 | 0.312 | rj3 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.444 [0.444, 0.444] | 0.632 | 0.343 | 0.522 | 0.387 | 0.472 | 0.420 | v2 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.480 [0.395, 0.642] | 0.709 | 0.319 | 0.573 | 0.383 | 0.513 | 0.436 | v2 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.289 [0.218, 0.388] | 0.863 | 0.550 | 0.433 | 0.379 | 0.334 | 0.320 | rj3 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.474 [0.400, 0.608] | 0.595 | 0.310 | 0.527 | 0.375 | 0.494 | 0.429 | v2 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.230 [0.170, 0.305] | 1.000 | 0.972 | 0.374 | 0.372 | 0.272 | 0.272 | v2 |
| gpt-6-astra · compound-realistic · low | 6 | 0.263 [0.207, 0.385] | 0.800 | 0.625 | 0.396 | 0.370 | 0.304 | 0.298 | rj3/v2 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.395 [0.336, 0.500] | 0.811 | 0.345 | 0.531 | 0.368 | 0.440 | 0.384 | v2 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.421 [0.346, 0.557] | 0.604 | 0.325 | 0.496 | 0.367 | 0.448 | 0.398 | v2 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.556 [0.556, 0.556] | 0.600 | 0.273 | 0.577 | 0.366 | 0.564 | 0.460 | v2 |
| gpt-6-astra · compound-realistic · high | 6 | 0.237 [0.189, 0.330] | 0.818 | 0.706 | 0.367 | 0.355 | 0.276 | 0.273 | rj3/v2 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.395 [0.292, 0.574] | 0.769 | 0.321 | 0.522 | 0.354 | 0.437 | 0.377 | v2 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.257 [0.189, 0.388] | 0.722 | 0.557 | 0.379 | 0.351 | 0.295 | 0.288 | v2 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.250 [0.193, 0.341] | 0.731 | 0.576 | 0.373 | 0.349 | 0.288 | 0.282 | v2 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.283 [0.218, 0.394] | 0.741 | 0.453 | 0.410 | 0.348 | 0.323 | 0.306 | v2 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.592 [0.512, 0.714] | 0.523 | 0.243 | 0.556 | 0.345 | 0.577 | 0.460 | v2 |
| claude-opus-5 · compound-realistic · low | 6 | 0.434 [0.365, 0.554] | 0.606 | 0.286 | 0.506 | 0.345 | 0.460 | 0.393 | v2 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.392 [0.365, 0.444] | 0.574 | 0.307 | 0.466 | 0.344 | 0.419 | 0.372 | v2 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.211 [0.147, 0.296] | 0.970 | 0.941 | 0.346 | 0.344 | 0.250 | 0.249 | v2 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.481 [0.481, 0.481] | 0.591 | 0.260 | 0.531 | 0.338 | 0.500 | 0.411 | v2 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.414 [0.321, 0.543] | 0.656 | 0.273 | 0.508 | 0.329 | 0.447 | 0.375 | v2 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.237 [0.184, 0.308] | 0.766 | 0.500 | 0.362 | 0.321 | 0.275 | 0.265 | v2 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.217 [0.160, 0.315] | 0.846 | 0.579 | 0.346 | 0.316 | 0.255 | 0.248 | v2 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.224 [0.176, 0.312] | 0.810 | 0.523 | 0.351 | 0.313 | 0.262 | 0.253 | v2 |
| claude-opus-5 · compound-realistic · high | 6 | 0.421 [0.350, 0.521] | 0.504 | 0.244 | 0.459 | 0.309 | 0.435 | 0.368 | v2 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.336 [0.245, 0.500] | 0.567 | 0.285 | 0.421 | 0.308 | 0.365 | 0.324 | v2 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.197 [0.157, 0.244] | 0.938 | 0.556 | 0.326 | 0.291 | 0.234 | 0.227 | v2 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.197 [0.123, 0.268] | 0.732 | 0.508 | 0.311 | 0.284 | 0.231 | 0.225 | v2 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.171 [0.112, 0.265] | 0.963 | 0.743 | 0.291 | 0.278 | 0.205 | 0.202 | rj3 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.178 [0.138, 0.238] | 0.659 | 0.574 | 0.280 | 0.271 | 0.208 | 0.206 | v2 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.151 [0.092, 0.238] | 1.000 | 1.000 | 0.263 | 0.263 | 0.182 | 0.182 | rj3 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.164 [0.094, 0.253] | 0.806 | 0.641 | 0.273 | 0.262 | 0.196 | 0.193 | rj3 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.145 [0.092, 0.227] | 0.957 | 0.957 | 0.251 | 0.251 | 0.174 | 0.174 | rj3 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.158 [0.089, 0.259] | 0.774 | 0.545 | 0.262 | 0.245 | 0.188 | 0.184 | rj3 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.138 [0.079, 0.218] | 1.000 | 1.000 | 0.243 | 0.243 | 0.167 | 0.167 | v2 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.138 [0.099, 0.198] | 1.000 | 1.000 | 0.243 | 0.243 | 0.167 | 0.167 | v2 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.138 [0.099, 0.195] | 1.000 | 1.000 | 0.243 | 0.243 | 0.167 | 0.167 | rj3/v2 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.243 [0.194, 0.320] | 0.487 | 0.242 | 0.325 | 0.243 | 0.270 | 0.243 | v2 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.125 [0.073, 0.192] | 0.950 | 0.950 | 0.221 | 0.221 | 0.151 | 0.151 | v2 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.237 [0.185, 0.323] | 0.387 | 0.198 | 0.294 | 0.216 | 0.257 | 0.228 | v2 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.145 [0.080, 0.199] | 0.880 | 0.355 | 0.249 | 0.206 | 0.174 | 0.164 | v2 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.112 [0.043, 0.202] | 0.708 | 0.378 | 0.193 | 0.173 | 0.134 | 0.130 | v2 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.099 [0.049, 0.164] | 0.750 | 0.357 | 0.174 | 0.155 | 0.119 | 0.115 | v2 |

MRV-vs-CE on ΔF1': 6/21 pairs resolve positive (CI lower bound > 0). On ΔF2' (our evaluator): 7/21. Point estimates: 17/21 positive on ΔF1', 17/21 on ΔF2'.


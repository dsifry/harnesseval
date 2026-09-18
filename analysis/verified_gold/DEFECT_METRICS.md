# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators: **verified** = 42 goldens + 91 D-verified defects (133 total); **full** = 42 + 145 (187 total). recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also charges nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.353 [0.268, 0.478] | 0.691 | 0.691 | 0.468 | 0.468 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.353 [0.250, 0.480] | 0.671 | 0.671 | 0.463 | 0.463 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.301 [0.217, 0.400] | 0.952 | 0.889 | 0.457 | 0.449 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.323 [0.254, 0.426] | 0.843 | 0.729 | 0.467 | 0.448 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.301 [0.254, 0.357] | 0.909 | 0.784 | 0.452 | 0.435 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.323 [0.235, 0.461] | 0.956 | 0.652 | 0.483 | 0.432 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.444 [0.385, 0.545] | 0.641 | 0.415 | 0.524 | 0.429 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.301 [0.209, 0.446] | 1.000 | 0.741 | 0.462 | 0.428 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.496 [0.437, 0.588] | 0.904 | 0.367 | 0.641 | 0.422 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.353 [0.291, 0.433] | 0.712 | 0.522 | 0.472 | 0.422 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.271 [0.198, 0.364] | 0.973 | 0.947 | 0.424 | 0.421 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.308 [0.235, 0.431] | 0.953 | 0.661 | 0.466 | 0.421 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.331 [0.256, 0.446] | 0.571 | 0.571 | 0.419 | 0.419 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.436 [0.310, 0.596] | 0.892 | 0.400 | 0.586 | 0.417 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.308 [0.250, 0.389] | 0.932 | 0.641 | 0.463 | 0.416 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.316 [0.207, 0.494] | 0.764 | 0.575 | 0.447 | 0.408 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.504 [0.380, 0.670] | 0.918 | 0.342 | 0.650 | 0.407 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.338 [0.205, 0.506] | 0.682 | 0.506 | 0.452 | 0.405 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.496 [0.398, 0.644] | 0.917 | 0.340 | 0.644 | 0.404 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.519 [0.417, 0.703] | 0.767 | 0.329 | 0.619 | 0.402 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.480 [0.480, 0.480] | 0.667 | 0.343 | 0.558 | 0.400 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.316 [0.246, 0.423] | 0.857 | 0.538 | 0.462 | 0.398 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.474 [0.366, 0.632] | 0.887 | 0.341 | 0.618 | 0.396 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.444 [0.360, 0.566] | 0.776 | 0.358 | 0.565 | 0.396 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.248 [0.172, 0.350] | 1.000 | 0.971 | 0.398 | 0.395 |
| gpt-6-astra · compound-realistic · low | 6 | 0.286 [0.232, 0.393] | 0.792 | 0.613 | 0.420 | 0.390 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.278 [0.173, 0.436] | 0.841 | 0.638 | 0.418 | 0.387 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.271 [0.190, 0.404] | 0.900 | 0.667 | 0.416 | 0.385 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.278 [0.194, 0.398] | 0.974 | 0.597 | 0.433 | 0.379 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.400 [0.400, 0.400] | 0.833 | 0.357 | 0.541 | 0.377 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.233 [0.167, 0.333] | 0.969 | 0.939 | 0.376 | 0.373 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.504 [0.435, 0.603] | 0.568 | 0.296 | 0.534 | 0.373 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.481 [0.382, 0.655] | 0.681 | 0.291 | 0.564 | 0.363 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.436 [0.355, 0.556] | 0.580 | 0.304 | 0.498 | 0.358 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.293 [0.175, 0.434] | 0.696 | 0.459 | 0.413 | 0.358 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.263 [0.170, 0.416] | 0.714 | 0.556 | 0.385 | 0.357 |
| gpt-6-astra · compound-realistic · high | 6 | 0.241 [0.161, 0.370] | 0.800 | 0.681 | 0.370 | 0.356 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.474 [0.383, 0.618] | 0.562 | 0.283 | 0.514 | 0.354 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.398 [0.321, 0.533] | 0.791 | 0.317 | 0.530 | 0.353 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.400 [0.400, 0.400] | 0.588 | 0.303 | 0.476 | 0.345 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.256 [0.158, 0.388] | 0.694 | 0.523 | 0.374 | 0.343 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.391 [0.323, 0.506] | 0.732 | 0.304 | 0.510 | 0.342 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.520 [0.520, 0.520] | 0.565 | 0.245 | 0.542 | 0.333 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.376 [0.262, 0.552] | 0.735 | 0.282 | 0.498 | 0.323 |
| claude-opus-5 · compound-realistic · low | 6 | 0.429 [0.322, 0.581] | 0.570 | 0.257 | 0.489 | 0.321 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.226 [0.167, 0.327] | 0.833 | 0.556 | 0.355 | 0.321 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.263 [0.152, 0.414] | 0.700 | 0.402 | 0.383 | 0.318 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.361 [0.233, 0.528] | 0.552 | 0.273 | 0.436 | 0.311 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.233 [0.174, 0.306] | 0.738 | 0.463 | 0.354 | 0.310 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.195 [0.116, 0.319] | 0.963 | 0.743 | 0.325 | 0.310 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.226 [0.152, 0.351] | 0.789 | 0.492 | 0.351 | 0.309 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.556 [0.459, 0.672] | 0.474 | 0.209 | 0.512 | 0.304 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.211 [0.162, 0.277] | 0.933 | 0.538 | 0.344 | 0.303 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.203 [0.148, 0.289] | 0.659 | 0.574 | 0.310 | 0.300 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.188 [0.107, 0.312] | 0.806 | 0.641 | 0.305 | 0.291 |
| claude-opus-5 · compound-realistic · high | 6 | 0.414 [0.331, 0.551] | 0.466 | 0.217 | 0.438 | 0.285 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.376 [0.306, 0.483] | 0.602 | 0.229 | 0.463 | 0.285 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.165 [0.088, 0.265] | 1.000 | 1.000 | 0.284 | 0.284 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.400 [0.400, 0.400] | 0.526 | 0.213 | 0.455 | 0.278 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.158 [0.117, 0.219] | 1.000 | 1.000 | 0.273 | 0.273 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.158 [0.105, 0.253] | 0.955 | 0.955 | 0.271 | 0.271 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.188 [0.114, 0.293] | 0.694 | 0.463 | 0.296 | 0.267 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.309 [0.256, 0.400] | 0.477 | 0.231 | 0.375 | 0.264 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.165 [0.099, 0.267] | 0.759 | 0.524 | 0.272 | 0.251 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.143 [0.086, 0.233] | 1.000 | 1.000 | 0.250 | 0.250 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.143 [0.102, 0.204] | 1.000 | 1.000 | 0.250 | 0.250 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.143 [0.086, 0.215] | 0.950 | 0.950 | 0.248 | 0.248 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.248 [0.187, 0.351] | 0.458 | 0.221 | 0.322 | 0.234 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.263 [0.186, 0.369] | 0.380 | 0.193 | 0.311 | 0.223 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.143 [0.088, 0.195] | 0.864 | 0.322 | 0.245 | 0.198 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.128 [0.050, 0.235] | 0.708 | 0.378 | 0.217 | 0.191 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.098 [0.053, 0.176] | 0.722 | 0.325 | 0.172 | 0.150 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| gpt-5.6-sol · compound-realistic · high | 6 | 0.390 [0.341, 0.485] | 0.676 | 0.454 | 0.495 | 0.419 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.424 [0.368, 0.546] | 0.915 | 0.397 | 0.579 | 0.410 |
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.288 [0.212, 0.420] | 0.708 | 0.708 | 0.410 | 0.410 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.384 [0.267, 0.546] | 0.907 | 0.439 | 0.540 | 0.410 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.435 [0.336, 0.624] | 0.928 | 0.376 | 0.592 | 0.403 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.424 [0.342, 0.568] | 0.904 | 0.381 | 0.577 | 0.401 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.282 [0.211, 0.408] | 0.685 | 0.685 | 0.400 | 0.400 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.271 [0.225, 0.375] | 0.857 | 0.750 | 0.412 | 0.398 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.429 [0.313, 0.636] | 0.927 | 0.371 | 0.587 | 0.398 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.305 [0.262, 0.396] | 0.740 | 0.557 | 0.432 | 0.394 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.254 [0.230, 0.296] | 0.918 | 0.804 | 0.398 | 0.386 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.379 [0.291, 0.530] | 0.798 | 0.387 | 0.513 | 0.383 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.243 [0.179, 0.340] | 0.956 | 0.896 | 0.387 | 0.382 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.424 [0.344, 0.600] | 0.781 | 0.347 | 0.549 | 0.382 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.254 [0.180, 0.389] | 1.000 | 0.763 | 0.405 | 0.381 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.414 [0.414, 0.414] | 0.667 | 0.343 | 0.511 | 0.375 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.266 [0.197, 0.417] | 0.783 | 0.603 | 0.397 | 0.369 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.249 [0.195, 0.352] | 0.957 | 0.677 | 0.395 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.418 [0.373, 0.512] | 0.592 | 0.318 | 0.490 | 0.361 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.249 [0.173, 0.372] | 0.957 | 0.657 | 0.395 | 0.361 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.260 [0.191, 0.383] | 0.582 | 0.582 | 0.359 | 0.359 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.412 [0.343, 0.560] | 0.598 | 0.313 | 0.488 | 0.356 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.407 [0.314, 0.617] | 0.706 | 0.316 | 0.516 | 0.356 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.345 [0.345, 0.345] | 0.833 | 0.357 | 0.488 | 0.351 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.266 [0.163, 0.440] | 0.691 | 0.516 | 0.384 | 0.351 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.215 [0.158, 0.314] | 0.974 | 0.950 | 0.352 | 0.350 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.254 [0.198, 0.355] | 0.865 | 0.556 | 0.393 | 0.349 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.237 [0.181, 0.347] | 0.933 | 0.646 | 0.378 | 0.347 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.367 [0.292, 0.518] | 0.607 | 0.328 | 0.458 | 0.347 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.237 [0.175, 0.313] | 0.977 | 0.627 | 0.382 | 0.344 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.345 [0.262, 0.490] | 0.762 | 0.339 | 0.475 | 0.342 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.226 [0.169, 0.365] | 0.909 | 0.690 | 0.362 | 0.340 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.333 [0.283, 0.460] | 0.808 | 0.341 | 0.472 | 0.337 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.254 [0.181, 0.351] | 0.726 | 0.495 | 0.377 | 0.336 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.345 [0.242, 0.512] | 0.772 | 0.324 | 0.477 | 0.334 |
| gpt-6-astra · compound-realistic · low | 6 | 0.226 [0.168, 0.370] | 0.800 | 0.625 | 0.352 | 0.332 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.220 [0.132, 0.356] | 0.848 | 0.650 | 0.350 | 0.329 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.345 [0.345, 0.345] | 0.588 | 0.303 | 0.435 | 0.323 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.192 [0.141, 0.262] | 1.000 | 0.971 | 0.322 | 0.321 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.448 [0.448, 0.448] | 0.565 | 0.245 | 0.500 | 0.317 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.215 [0.159, 0.313] | 0.731 | 0.576 | 0.332 | 0.313 |
| claude-opus-5 · compound-realistic · low | 6 | 0.356 [0.256, 0.526] | 0.594 | 0.276 | 0.445 | 0.311 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.237 [0.183, 0.345] | 0.737 | 0.447 | 0.359 | 0.310 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.305 [0.226, 0.470] | 0.581 | 0.297 | 0.400 | 0.301 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.452 [0.352, 0.610] | 0.494 | 0.222 | 0.472 | 0.298 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.175 [0.124, 0.239] | 0.969 | 0.939 | 0.297 | 0.295 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.203 [0.127, 0.345] | 0.706 | 0.537 | 0.316 | 0.295 |
| gpt-6-astra · compound-realistic · high | 6 | 0.186 [0.128, 0.310] | 0.805 | 0.688 | 0.303 | 0.293 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.333 [0.269, 0.450] | 0.641 | 0.260 | 0.439 | 0.292 |
| claude-opus-5 · compound-realistic · high | 6 | 0.350 [0.286, 0.478] | 0.496 | 0.238 | 0.411 | 0.284 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.198 [0.154, 0.273] | 0.761 | 0.493 | 0.314 | 0.282 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.192 [0.155, 0.253] | 0.810 | 0.523 | 0.311 | 0.281 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.286 [0.226, 0.414] | 0.531 | 0.271 | 0.371 | 0.278 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.181 [0.137, 0.267] | 0.842 | 0.571 | 0.298 | 0.275 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.345 [0.345, 0.345] | 0.526 | 0.213 | 0.417 | 0.263 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.153 [0.097, 0.239] | 0.964 | 0.750 | 0.263 | 0.254 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.158 [0.121, 0.220] | 0.667 | 0.583 | 0.256 | 0.249 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.158 [0.119, 0.206] | 0.933 | 0.538 | 0.271 | 0.245 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.147 [0.081, 0.223] | 0.812 | 0.650 | 0.249 | 0.240 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.153 [0.097, 0.221] | 0.711 | 0.482 | 0.251 | 0.232 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.130 [0.068, 0.213] | 1.000 | 1.000 | 0.230 | 0.230 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.215 [0.177, 0.284] | 0.494 | 0.247 | 0.299 | 0.230 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.119 [0.068, 0.200] | 1.000 | 1.000 | 0.212 | 0.212 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.119 [0.088, 0.165] | 1.000 | 1.000 | 0.212 | 0.212 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.119 [0.086, 0.173] | 1.000 | 1.000 | 0.212 | 0.212 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.119 [0.075, 0.200] | 0.955 | 0.955 | 0.211 | 0.211 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.215 [0.164, 0.304] | 0.400 | 0.207 | 0.279 | 0.211 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.113 [0.063, 0.183] | 0.952 | 0.952 | 0.202 | 0.202 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.124 [0.073, 0.200] | 0.759 | 0.524 | 0.214 | 0.201 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.107 [0.070, 0.150] | 0.864 | 0.322 | 0.191 | 0.161 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.096 [0.038, 0.166] | 0.708 | 0.378 | 0.169 | 0.153 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.073 [0.039, 0.137] | 0.722 | 0.325 | 0.133 | 0.120 |

MRV-vs-CE: 6/21 pairs resolve positive on ΔF1'.


# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators are computed from the registry (see _final in analysis/verified_gold/DEFECT_REGISTRY.json): verified = 42 goldens + every D-verified defect; full = 42 + all registry defects. recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.322 [0.244, 0.443] | 0.700 | 0.700 | 0.441 | 0.441 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.309 [0.217, 0.438] | 0.671 | 0.671 | 0.423 | 0.423 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.289 [0.243, 0.363] | 0.846 | 0.733 | 0.431 | 0.415 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.454 [0.398, 0.551] | 0.908 | 0.377 | 0.605 | 0.412 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.395 [0.349, 0.485] | 0.645 | 0.420 | 0.490 | 0.407 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.263 [0.197, 0.340] | 0.952 | 0.889 | 0.412 | 0.406 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.270 [0.244, 0.302] | 0.911 | 0.788 | 0.416 | 0.402 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.461 [0.369, 0.610] | 0.921 | 0.354 | 0.614 | 0.400 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.283 [0.202, 0.407] | 0.956 | 0.652 | 0.437 | 0.394 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.454 [0.328, 0.624] | 0.920 | 0.348 | 0.608 | 0.394 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.382 [0.257, 0.530] | 0.892 | 0.400 | 0.535 | 0.391 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.309 [0.244, 0.398] | 0.712 | 0.522 | 0.431 | 0.388 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.289 [0.221, 0.400] | 0.571 | 0.571 | 0.384 | 0.384 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.237 [0.171, 0.313] | 0.973 | 0.947 | 0.381 | 0.379 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.421 [0.318, 0.580] | 0.889 | 0.344 | 0.571 | 0.379 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.395 [0.304, 0.528] | 0.779 | 0.361 | 0.524 | 0.377 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.263 [0.207, 0.371] | 0.952 | 0.656 | 0.412 | 0.376 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.276 [0.176, 0.443] | 0.764 | 0.575 | 0.406 | 0.373 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.250 [0.186, 0.368] | 1.000 | 0.731 | 0.400 | 0.373 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.283 [0.228, 0.371] | 0.860 | 0.544 | 0.426 | 0.372 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.434 [0.338, 0.612] | 0.759 | 0.319 | 0.552 | 0.368 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.289 [0.174, 0.447] | 0.677 | 0.500 | 0.406 | 0.367 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.257 [0.206, 0.340] | 0.929 | 0.629 | 0.402 | 0.364 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.243 [0.173, 0.375] | 0.902 | 0.673 | 0.383 | 0.357 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.408 [0.333, 0.528] | 0.596 | 0.318 | 0.484 | 0.357 |
| gpt-6-astra · compound-realistic · low | 6 | 0.250 [0.203, 0.354] | 0.792 | 0.613 | 0.380 | 0.355 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.217 [0.162, 0.289] | 1.000 | 0.971 | 0.357 | 0.355 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.441 [0.369, 0.538] | 0.568 | 0.296 | 0.496 | 0.354 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.428 [0.335, 0.604] | 0.684 | 0.294 | 0.526 | 0.349 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.243 [0.179, 0.323] | 0.974 | 0.597 | 0.389 | 0.346 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.421 [0.322, 0.583] | 0.566 | 0.286 | 0.483 | 0.340 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.230 [0.146, 0.357] | 0.833 | 0.625 | 0.361 | 0.337 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.204 [0.143, 0.289] | 0.969 | 0.939 | 0.337 | 0.335 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.349 [0.267, 0.471] | 0.736 | 0.308 | 0.473 | 0.327 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.342 [0.283, 0.458] | 0.788 | 0.313 | 0.477 | 0.327 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.355 [0.257, 0.506] | 0.750 | 0.298 | 0.482 | 0.324 |
| gpt-6-astra · compound-realistic · high | 6 | 0.211 [0.149, 0.329] | 0.800 | 0.681 | 0.333 | 0.322 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.243 [0.147, 0.357] | 0.685 | 0.446 | 0.359 | 0.315 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.224 [0.146, 0.337] | 0.694 | 0.523 | 0.338 | 0.313 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.217 [0.146, 0.328] | 0.702 | 0.541 | 0.332 | 0.310 |
| claude-opus-5 · compound-realistic · low | 6 | 0.382 [0.276, 0.531] | 0.574 | 0.260 | 0.458 | 0.309 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.362 [0.282, 0.469] | 0.625 | 0.247 | 0.458 | 0.293 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.230 [0.154, 0.340] | 0.700 | 0.402 | 0.347 | 0.293 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.487 [0.376, 0.624] | 0.474 | 0.209 | 0.481 | 0.292 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.197 [0.145, 0.292] | 0.833 | 0.556 | 0.319 | 0.291 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.204 [0.149, 0.271] | 0.738 | 0.463 | 0.320 | 0.283 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.303 [0.200, 0.465] | 0.541 | 0.264 | 0.388 | 0.282 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.197 [0.145, 0.284] | 0.789 | 0.492 | 0.316 | 0.282 |
| claude-opus-5 · compound-realistic · high | 6 | 0.362 [0.284, 0.500] | 0.466 | 0.217 | 0.407 | 0.272 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.291 [0.212, 0.444] | 0.500 | 0.247 | 0.368 | 0.267 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.178 [0.138, 0.224] | 0.931 | 0.529 | 0.298 | 0.266 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.171 [0.126, 0.239] | 0.650 | 0.565 | 0.271 | 0.263 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.158 [0.098, 0.250] | 0.960 | 0.727 | 0.271 | 0.259 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.151 [0.094, 0.216] | 0.793 | 0.622 | 0.254 | 0.243 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.138 [0.099, 0.197] | 1.000 | 1.000 | 0.243 | 0.243 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.237 [0.187, 0.321] | 0.480 | 0.237 | 0.317 | 0.237 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.158 [0.100, 0.234] | 0.686 | 0.453 | 0.257 | 0.234 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.132 [0.074, 0.217] | 1.000 | 1.000 | 0.233 | 0.233 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.132 [0.096, 0.191] | 1.000 | 1.000 | 0.233 | 0.233 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.132 [0.073, 0.213] | 1.000 | 1.000 | 0.233 | 0.233 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.132 [0.086, 0.216] | 0.952 | 0.952 | 0.231 | 0.231 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.125 [0.073, 0.196] | 0.950 | 0.950 | 0.221 | 0.221 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.138 [0.084, 0.220] | 0.750 | 0.512 | 0.233 | 0.218 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.217 [0.157, 0.315] | 0.367 | 0.184 | 0.273 | 0.199 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.125 [0.081, 0.168] | 0.864 | 0.322 | 0.218 | 0.180 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.099 [0.031, 0.184] | 0.682 | 0.349 | 0.172 | 0.154 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.086 [0.047, 0.158] | 0.722 | 0.325 | 0.153 | 0.135 |

MRV-vs-CE: 8/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.322 [0.244, 0.443] | 0.700 | 0.700 | 0.441 | 0.441 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.309 [0.217, 0.438] | 0.671 | 0.671 | 0.423 | 0.423 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.289 [0.243, 0.363] | 0.846 | 0.733 | 0.431 | 0.415 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.454 [0.398, 0.552] | 0.908 | 0.377 | 0.605 | 0.412 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.395 [0.349, 0.484] | 0.645 | 0.420 | 0.490 | 0.407 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.263 [0.197, 0.339] | 0.952 | 0.889 | 0.412 | 0.406 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.270 [0.244, 0.302] | 0.911 | 0.788 | 0.416 | 0.402 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.461 [0.370, 0.607] | 0.921 | 0.354 | 0.614 | 0.400 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.283 [0.200, 0.404] | 0.956 | 0.652 | 0.437 | 0.394 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.454 [0.330, 0.624] | 0.920 | 0.348 | 0.608 | 0.394 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.382 [0.257, 0.530] | 0.892 | 0.400 | 0.535 | 0.391 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.309 [0.244, 0.398] | 0.712 | 0.522 | 0.431 | 0.388 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.289 [0.220, 0.400] | 0.571 | 0.571 | 0.384 | 0.384 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.237 [0.173, 0.313] | 0.973 | 0.947 | 0.381 | 0.379 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.421 [0.318, 0.581] | 0.889 | 0.344 | 0.571 | 0.379 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.395 [0.303, 0.528] | 0.779 | 0.361 | 0.524 | 0.377 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.263 [0.207, 0.371] | 0.952 | 0.656 | 0.412 | 0.376 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.276 [0.172, 0.443] | 0.764 | 0.575 | 0.406 | 0.373 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.250 [0.186, 0.369] | 1.000 | 0.731 | 0.400 | 0.373 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.283 [0.227, 0.375] | 0.860 | 0.544 | 0.426 | 0.372 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.434 [0.341, 0.610] | 0.759 | 0.319 | 0.552 | 0.368 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.289 [0.174, 0.444] | 0.677 | 0.500 | 0.406 | 0.367 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.257 [0.206, 0.337] | 0.929 | 0.629 | 0.402 | 0.364 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.243 [0.175, 0.375] | 0.902 | 0.673 | 0.383 | 0.357 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.408 [0.330, 0.528] | 0.596 | 0.318 | 0.484 | 0.357 |
| gpt-6-astra · compound-realistic · low | 6 | 0.250 [0.203, 0.354] | 0.792 | 0.613 | 0.380 | 0.355 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.217 [0.162, 0.290] | 1.000 | 0.971 | 0.357 | 0.355 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.441 [0.369, 0.538] | 0.568 | 0.296 | 0.496 | 0.354 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.428 [0.336, 0.604] | 0.684 | 0.294 | 0.526 | 0.349 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.243 [0.179, 0.323] | 0.974 | 0.597 | 0.389 | 0.346 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.421 [0.321, 0.583] | 0.566 | 0.286 | 0.483 | 0.340 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.230 [0.147, 0.350] | 0.833 | 0.625 | 0.361 | 0.337 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.204 [0.145, 0.288] | 0.969 | 0.939 | 0.337 | 0.335 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.349 [0.267, 0.471] | 0.736 | 0.308 | 0.473 | 0.327 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.342 [0.284, 0.458] | 0.788 | 0.313 | 0.477 | 0.327 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.355 [0.257, 0.505] | 0.750 | 0.298 | 0.482 | 0.324 |
| gpt-6-astra · compound-realistic · high | 6 | 0.211 [0.149, 0.330] | 0.800 | 0.681 | 0.333 | 0.322 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.243 [0.149, 0.357] | 0.685 | 0.446 | 0.359 | 0.315 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.224 [0.146, 0.347] | 0.694 | 0.523 | 0.338 | 0.313 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.217 [0.147, 0.340] | 0.702 | 0.541 | 0.332 | 0.310 |
| claude-opus-5 · compound-realistic · low | 6 | 0.382 [0.277, 0.531] | 0.574 | 0.260 | 0.458 | 0.309 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.362 [0.282, 0.470] | 0.625 | 0.247 | 0.458 | 0.293 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.230 [0.154, 0.340] | 0.700 | 0.402 | 0.347 | 0.293 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.487 [0.376, 0.622] | 0.474 | 0.209 | 0.481 | 0.292 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.197 [0.145, 0.293] | 0.833 | 0.556 | 0.319 | 0.291 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.204 [0.149, 0.273] | 0.738 | 0.463 | 0.320 | 0.283 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.303 [0.199, 0.469] | 0.541 | 0.264 | 0.388 | 0.282 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.197 [0.145, 0.284] | 0.789 | 0.492 | 0.316 | 0.282 |
| claude-opus-5 · compound-realistic · high | 6 | 0.362 [0.281, 0.500] | 0.466 | 0.217 | 0.407 | 0.272 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.291 [0.212, 0.444] | 0.500 | 0.247 | 0.368 | 0.267 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.178 [0.138, 0.224] | 0.931 | 0.529 | 0.298 | 0.266 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.171 [0.126, 0.239] | 0.650 | 0.565 | 0.271 | 0.263 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.158 [0.097, 0.250] | 0.960 | 0.727 | 0.271 | 0.259 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.151 [0.092, 0.216] | 0.793 | 0.622 | 0.254 | 0.243 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.138 [0.099, 0.197] | 1.000 | 1.000 | 0.243 | 0.243 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.237 [0.187, 0.323] | 0.480 | 0.237 | 0.317 | 0.237 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.158 [0.100, 0.236] | 0.686 | 0.453 | 0.257 | 0.234 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.132 [0.074, 0.218] | 1.000 | 1.000 | 0.233 | 0.233 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.132 [0.096, 0.191] | 1.000 | 1.000 | 0.233 | 0.233 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.132 [0.073, 0.212] | 1.000 | 1.000 | 0.233 | 0.233 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.132 [0.086, 0.215] | 0.952 | 0.952 | 0.231 | 0.231 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.125 [0.072, 0.194] | 0.950 | 0.950 | 0.221 | 0.221 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.138 [0.084, 0.220] | 0.750 | 0.512 | 0.233 | 0.218 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.217 [0.155, 0.313] | 0.367 | 0.184 | 0.273 | 0.199 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.125 [0.081, 0.168] | 0.864 | 0.322 | 0.218 | 0.180 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.099 [0.031, 0.184] | 0.682 | 0.349 | 0.172 | 0.154 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.086 [0.047, 0.155] | 0.722 | 0.325 | 0.153 | 0.135 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.


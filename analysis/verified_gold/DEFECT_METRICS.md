# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators are computed from the registry (see _final in analysis/verified_gold/DEFECT_REGISTRY.json): verified = 42 goldens + every D-verified defect; reachable = 42 + only those defects that some run actually reported (13 were audit-surfaced and no run ever reported them, so they cap recall for everyone); full = 42 + all registry defects. recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.322 [0.244, 0.443] | 0.700 | 0.700 | 0.441 | 0.441 | 0.361 | 0.361 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.309 [0.217, 0.438] | 0.671 | 0.671 | 0.423 | 0.423 | 0.347 | 0.347 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.289 [0.243, 0.363] | 0.846 | 0.733 | 0.431 | 0.415 | 0.333 | 0.329 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.454 [0.398, 0.551] | 0.908 | 0.377 | 0.605 | 0.412 | 0.504 | 0.436 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.395 [0.349, 0.485] | 0.645 | 0.420 | 0.490 | 0.407 | 0.428 | 0.399 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.263 [0.197, 0.340] | 0.952 | 0.889 | 0.412 | 0.406 | 0.308 | 0.306 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.270 [0.244, 0.302] | 0.911 | 0.788 | 0.416 | 0.402 | 0.314 | 0.311 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.461 [0.369, 0.610] | 0.921 | 0.354 | 0.614 | 0.400 | 0.512 | 0.434 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.283 [0.202, 0.407] | 0.956 | 0.652 | 0.437 | 0.394 | 0.329 | 0.319 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.454 [0.328, 0.624] | 0.920 | 0.348 | 0.608 | 0.394 | 0.505 | 0.428 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.382 [0.257, 0.530] | 0.892 | 0.400 | 0.535 | 0.391 | 0.431 | 0.385 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.309 [0.244, 0.398] | 0.712 | 0.522 | 0.431 | 0.388 | 0.349 | 0.337 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.289 [0.221, 0.400] | 0.571 | 0.571 | 0.384 | 0.384 | 0.321 | 0.321 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.237 [0.171, 0.313] | 0.973 | 0.947 | 0.381 | 0.379 | 0.279 | 0.279 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.421 [0.318, 0.580] | 0.889 | 0.344 | 0.571 | 0.379 | 0.471 | 0.403 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.395 [0.304, 0.528] | 0.779 | 0.361 | 0.524 | 0.377 | 0.438 | 0.388 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.263 [0.207, 0.371] | 0.952 | 0.656 | 0.412 | 0.376 | 0.308 | 0.299 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.276 [0.176, 0.443] | 0.764 | 0.575 | 0.406 | 0.373 | 0.317 | 0.308 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.250 [0.186, 0.368] | 1.000 | 0.731 | 0.400 | 0.373 | 0.294 | 0.288 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.283 [0.228, 0.371] | 0.860 | 0.544 | 0.426 | 0.372 | 0.327 | 0.313 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.434 [0.338, 0.612] | 0.759 | 0.319 | 0.552 | 0.368 | 0.475 | 0.405 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.289 [0.174, 0.447] | 0.677 | 0.500 | 0.406 | 0.367 | 0.327 | 0.316 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.257 [0.206, 0.340] | 0.929 | 0.629 | 0.402 | 0.364 | 0.300 | 0.291 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 | 0.417 | 0.368 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 | 0.440 | 0.387 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.243 [0.173, 0.375] | 0.902 | 0.673 | 0.383 | 0.357 | 0.285 | 0.279 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.408 [0.333, 0.528] | 0.596 | 0.318 | 0.484 | 0.357 | 0.435 | 0.386 |
| gpt-6-astra · compound-realistic · low | 6 | 0.250 [0.203, 0.354] | 0.792 | 0.613 | 0.380 | 0.355 | 0.290 | 0.284 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.217 [0.162, 0.289] | 1.000 | 0.971 | 0.357 | 0.355 | 0.257 | 0.257 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.441 [0.369, 0.538] | 0.568 | 0.296 | 0.496 | 0.354 | 0.461 | 0.402 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.428 [0.335, 0.604] | 0.684 | 0.294 | 0.526 | 0.349 | 0.462 | 0.392 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.243 [0.179, 0.323] | 0.974 | 0.597 | 0.389 | 0.346 | 0.286 | 0.276 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.421 [0.322, 0.583] | 0.566 | 0.286 | 0.483 | 0.340 | 0.444 | 0.385 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.230 [0.146, 0.357] | 0.833 | 0.625 | 0.361 | 0.337 | 0.269 | 0.264 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.204 [0.143, 0.289] | 0.969 | 0.939 | 0.337 | 0.335 | 0.242 | 0.242 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 | 0.400 | 0.355 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.349 [0.267, 0.471] | 0.736 | 0.308 | 0.473 | 0.327 | 0.390 | 0.340 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.342 [0.283, 0.458] | 0.788 | 0.313 | 0.477 | 0.327 | 0.386 | 0.336 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 | 0.496 | 0.404 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.355 [0.257, 0.506] | 0.750 | 0.298 | 0.482 | 0.324 | 0.397 | 0.342 |
| gpt-6-astra · compound-realistic · high | 6 | 0.211 [0.149, 0.329] | 0.800 | 0.681 | 0.333 | 0.322 | 0.247 | 0.244 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.243 [0.147, 0.357] | 0.685 | 0.446 | 0.359 | 0.315 | 0.279 | 0.268 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.224 [0.146, 0.337] | 0.694 | 0.523 | 0.338 | 0.313 | 0.259 | 0.253 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.217 [0.146, 0.328] | 0.702 | 0.541 | 0.332 | 0.310 | 0.252 | 0.247 |
| claude-opus-5 · compound-realistic · low | 6 | 0.382 [0.276, 0.531] | 0.574 | 0.260 | 0.458 | 0.309 | 0.409 | 0.349 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.362 [0.282, 0.469] | 0.625 | 0.247 | 0.458 | 0.293 | 0.395 | 0.331 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.230 [0.154, 0.340] | 0.700 | 0.402 | 0.347 | 0.293 | 0.266 | 0.252 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.487 [0.376, 0.624] | 0.474 | 0.209 | 0.481 | 0.292 | 0.484 | 0.385 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.197 [0.145, 0.292] | 0.833 | 0.556 | 0.319 | 0.291 | 0.233 | 0.227 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.204 [0.149, 0.271] | 0.738 | 0.463 | 0.320 | 0.283 | 0.238 | 0.230 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.303 [0.200, 0.465] | 0.541 | 0.264 | 0.388 | 0.282 | 0.332 | 0.294 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.197 [0.145, 0.284] | 0.789 | 0.492 | 0.316 | 0.282 | 0.232 | 0.224 |
| claude-opus-5 · compound-realistic · high | 6 | 0.362 [0.284, 0.500] | 0.466 | 0.217 | 0.407 | 0.272 | 0.379 | 0.319 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 | 0.394 | 0.323 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.291 [0.212, 0.444] | 0.500 | 0.247 | 0.368 | 0.267 | 0.318 | 0.281 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.178 [0.138, 0.224] | 0.931 | 0.529 | 0.298 | 0.266 | 0.212 | 0.205 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.171 [0.126, 0.239] | 0.650 | 0.565 | 0.271 | 0.263 | 0.201 | 0.199 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.158 [0.098, 0.250] | 0.960 | 0.727 | 0.271 | 0.259 | 0.190 | 0.187 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.151 [0.094, 0.216] | 0.793 | 0.622 | 0.254 | 0.243 | 0.181 | 0.178 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.138 [0.099, 0.197] | 1.000 | 1.000 | 0.243 | 0.243 | 0.167 | 0.167 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.237 [0.187, 0.321] | 0.480 | 0.237 | 0.317 | 0.237 | 0.264 | 0.237 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.158 [0.100, 0.234] | 0.686 | 0.453 | 0.257 | 0.234 | 0.187 | 0.182 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.132 [0.074, 0.217] | 1.000 | 1.000 | 0.233 | 0.233 | 0.159 | 0.159 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.132 [0.096, 0.191] | 1.000 | 1.000 | 0.233 | 0.233 | 0.159 | 0.159 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.132 [0.073, 0.213] | 1.000 | 1.000 | 0.233 | 0.233 | 0.159 | 0.159 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.132 [0.086, 0.216] | 0.952 | 0.952 | 0.231 | 0.231 | 0.159 | 0.159 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.125 [0.073, 0.196] | 0.950 | 0.950 | 0.221 | 0.221 | 0.151 | 0.151 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.138 [0.084, 0.220] | 0.750 | 0.512 | 0.233 | 0.218 | 0.165 | 0.162 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.217 [0.157, 0.315] | 0.367 | 0.184 | 0.273 | 0.199 | 0.236 | 0.210 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.125 [0.081, 0.168] | 0.864 | 0.322 | 0.218 | 0.180 | 0.151 | 0.142 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.099 [0.031, 0.184] | 0.682 | 0.349 | 0.172 | 0.154 | 0.119 | 0.115 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.086 [0.047, 0.158] | 0.722 | 0.325 | 0.153 | 0.135 | 0.104 | 0.100 |

MRV-vs-CE on ΔF1': 8/21 pairs resolve positive (CI lower bound > 0). On ΔF2' (our evaluator): 7/21. Point estimates: 19/21 positive on ΔF1', 18/21 on ΔF2'.

## variant: reachable

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.353 [0.276, 0.474] | 0.700 | 0.700 | 0.469 | 0.469 | 0.391 | 0.391 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.338 [0.244, 0.467] | 0.671 | 0.671 | 0.450 | 0.450 | 0.375 | 0.375 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.317 [0.262, 0.400] | 0.846 | 0.733 | 0.461 | 0.442 | 0.362 | 0.357 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.288 [0.221, 0.371] | 0.952 | 0.889 | 0.442 | 0.435 | 0.334 | 0.333 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.295 [0.272, 0.333] | 0.911 | 0.788 | 0.446 | 0.429 | 0.341 | 0.337 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.496 [0.451, 0.570] | 0.908 | 0.377 | 0.642 | 0.429 | 0.546 | 0.467 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.432 [0.394, 0.511] | 0.645 | 0.420 | 0.517 | 0.426 | 0.462 | 0.429 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.309 [0.222, 0.441] | 0.956 | 0.652 | 0.467 | 0.420 | 0.358 | 0.346 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.504 [0.417, 0.639] | 0.921 | 0.354 | 0.651 | 0.415 | 0.554 | 0.464 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.338 [0.274, 0.431] | 0.712 | 0.522 | 0.459 | 0.410 | 0.378 | 0.364 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.496 [0.375, 0.654] | 0.920 | 0.348 | 0.645 | 0.409 | 0.547 | 0.458 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.417 [0.287, 0.571] | 0.892 | 0.400 | 0.569 | 0.408 | 0.467 | 0.414 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.317 [0.245, 0.429] | 0.571 | 0.571 | 0.407 | 0.407 | 0.348 | 0.348 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.259 [0.194, 0.333] | 0.973 | 0.947 | 0.409 | 0.407 | 0.304 | 0.303 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.288 [0.230, 0.400] | 0.952 | 0.656 | 0.442 | 0.400 | 0.334 | 0.324 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.273 [0.208, 0.397] | 1.000 | 0.731 | 0.429 | 0.398 | 0.320 | 0.313 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.302 [0.194, 0.468] | 0.764 | 0.575 | 0.433 | 0.396 | 0.344 | 0.334 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.309 [0.255, 0.400] | 0.860 | 0.544 | 0.455 | 0.394 | 0.355 | 0.339 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.460 [0.357, 0.625] | 0.889 | 0.344 | 0.607 | 0.394 | 0.510 | 0.431 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.432 [0.344, 0.556] | 0.779 | 0.361 | 0.556 | 0.393 | 0.474 | 0.416 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.281 [0.233, 0.356] | 0.929 | 0.629 | 0.431 | 0.388 | 0.326 | 0.316 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.317 [0.197, 0.473] | 0.677 | 0.500 | 0.431 | 0.388 | 0.354 | 0.342 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.475 [0.377, 0.656] | 0.759 | 0.319 | 0.584 | 0.382 | 0.513 | 0.433 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.237 [0.179, 0.317] | 1.000 | 0.971 | 0.384 | 0.382 | 0.280 | 0.280 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.266 [0.198, 0.389] | 0.902 | 0.673 | 0.411 | 0.381 | 0.310 | 0.303 |
| gpt-6-astra · compound-realistic · low | 6 | 0.273 [0.227, 0.378] | 0.792 | 0.613 | 0.406 | 0.378 | 0.315 | 0.307 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.446 [0.376, 0.552] | 0.596 | 0.318 | 0.510 | 0.371 | 0.470 | 0.413 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.385 [0.385, 0.385] | 0.833 | 0.357 | 0.526 | 0.370 | 0.431 | 0.379 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.266 [0.200, 0.357] | 0.974 | 0.597 | 0.418 | 0.368 | 0.311 | 0.299 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.482 [0.420, 0.569] | 0.568 | 0.296 | 0.521 | 0.367 | 0.497 | 0.428 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.423 [0.423, 0.423] | 0.647 | 0.324 | 0.512 | 0.367 | 0.455 | 0.399 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.468 [0.380, 0.635] | 0.684 | 0.294 | 0.556 | 0.361 | 0.499 | 0.418 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.223 [0.161, 0.318] | 0.969 | 0.939 | 0.363 | 0.360 | 0.264 | 0.263 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.252 [0.164, 0.382] | 0.833 | 0.625 | 0.387 | 0.359 | 0.293 | 0.286 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.460 [0.356, 0.614] | 0.566 | 0.286 | 0.508 | 0.353 | 0.478 | 0.410 |
| gpt-6-astra · compound-realistic · high | 6 | 0.230 [0.167, 0.353] | 0.800 | 0.681 | 0.358 | 0.344 | 0.268 | 0.265 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.374 [0.319, 0.478] | 0.788 | 0.313 | 0.507 | 0.341 | 0.418 | 0.360 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.381 [0.301, 0.500] | 0.736 | 0.308 | 0.502 | 0.341 | 0.422 | 0.364 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.385 [0.385, 0.385] | 0.588 | 0.303 | 0.465 | 0.339 | 0.413 | 0.365 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.388 [0.287, 0.549] | 0.750 | 0.298 | 0.512 | 0.338 | 0.430 | 0.366 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.245 [0.164, 0.364] | 0.694 | 0.523 | 0.362 | 0.333 | 0.281 | 0.274 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.266 [0.164, 0.392] | 0.685 | 0.446 | 0.383 | 0.333 | 0.303 | 0.290 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.237 [0.161, 0.367] | 0.702 | 0.541 | 0.355 | 0.330 | 0.274 | 0.267 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.500 [0.500, 0.500] | 0.565 | 0.245 | 0.531 | 0.329 | 0.512 | 0.414 |
| claude-opus-5 · compound-realistic · low | 6 | 0.417 [0.312, 0.559] | 0.574 | 0.260 | 0.483 | 0.320 | 0.441 | 0.372 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.216 [0.159, 0.314] | 0.833 | 0.556 | 0.343 | 0.311 | 0.253 | 0.246 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.252 [0.172, 0.367] | 0.700 | 0.402 | 0.370 | 0.310 | 0.289 | 0.272 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.396 [0.317, 0.500] | 0.625 | 0.247 | 0.485 | 0.304 | 0.427 | 0.353 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.223 [0.167, 0.294] | 0.738 | 0.463 | 0.343 | 0.301 | 0.259 | 0.249 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.532 [0.427, 0.648] | 0.474 | 0.209 | 0.502 | 0.300 | 0.520 | 0.407 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.216 [0.156, 0.316] | 0.789 | 0.492 | 0.339 | 0.300 | 0.253 | 0.243 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.331 [0.227, 0.486] | 0.541 | 0.264 | 0.411 | 0.294 | 0.359 | 0.315 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.194 [0.154, 0.246] | 0.931 | 0.529 | 0.321 | 0.284 | 0.231 | 0.222 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.187 [0.140, 0.256] | 0.650 | 0.565 | 0.291 | 0.281 | 0.218 | 0.216 |
| claude-opus-5 · compound-realistic · high | 6 | 0.396 [0.310, 0.526] | 0.466 | 0.217 | 0.428 | 0.281 | 0.408 | 0.340 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.324 [0.244, 0.462] | 0.500 | 0.247 | 0.393 | 0.280 | 0.348 | 0.305 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.173 [0.109, 0.269] | 0.960 | 0.727 | 0.293 | 0.279 | 0.207 | 0.204 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.385 [0.385, 0.385] | 0.526 | 0.213 | 0.444 | 0.274 | 0.407 | 0.331 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.151 [0.108, 0.216] | 1.000 | 1.000 | 0.263 | 0.263 | 0.182 | 0.182 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.165 [0.104, 0.238] | 0.793 | 0.622 | 0.274 | 0.261 | 0.197 | 0.194 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.144 [0.082, 0.233] | 1.000 | 1.000 | 0.252 | 0.252 | 0.174 | 0.174 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.144 [0.107, 0.210] | 1.000 | 1.000 | 0.252 | 0.252 | 0.174 | 0.174 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.144 [0.082, 0.232] | 1.000 | 1.000 | 0.252 | 0.252 | 0.174 | 0.174 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.173 [0.108, 0.256] | 0.686 | 0.453 | 0.276 | 0.250 | 0.203 | 0.197 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.144 [0.097, 0.235] | 0.952 | 0.952 | 0.250 | 0.250 | 0.173 | 0.173 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.259 [0.204, 0.344] | 0.480 | 0.237 | 0.336 | 0.247 | 0.285 | 0.254 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.137 [0.082, 0.205] | 0.950 | 0.950 | 0.239 | 0.239 | 0.165 | 0.165 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.151 [0.093, 0.241] | 0.750 | 0.512 | 0.251 | 0.233 | 0.180 | 0.176 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.237 [0.172, 0.333] | 0.367 | 0.184 | 0.288 | 0.208 | 0.255 | 0.224 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.137 [0.083, 0.188] | 0.864 | 0.322 | 0.236 | 0.192 | 0.164 | 0.154 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.108 [0.034, 0.202] | 0.682 | 0.349 | 0.186 | 0.165 | 0.130 | 0.125 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.094 [0.052, 0.162] | 0.722 | 0.325 | 0.166 | 0.145 | 0.113 | 0.109 |

MRV-vs-CE on ΔF1': 7/21 pairs resolve positive (CI lower bound > 0). On ΔF2' (our evaluator): 7/21. Point estimates: 19/21 positive on ΔF1', 18/21 on ΔF2'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' | F2 | F2' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.322 [0.244, 0.443] | 0.700 | 0.700 | 0.441 | 0.441 | 0.361 | 0.361 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.309 [0.217, 0.440] | 0.671 | 0.671 | 0.423 | 0.423 | 0.347 | 0.347 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.289 [0.243, 0.363] | 0.846 | 0.733 | 0.431 | 0.415 | 0.333 | 0.329 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.454 [0.398, 0.548] | 0.908 | 0.377 | 0.605 | 0.412 | 0.504 | 0.436 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.395 [0.349, 0.484] | 0.645 | 0.420 | 0.490 | 0.407 | 0.428 | 0.399 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.263 [0.197, 0.340] | 0.952 | 0.889 | 0.412 | 0.406 | 0.308 | 0.306 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.270 [0.244, 0.302] | 0.911 | 0.788 | 0.416 | 0.402 | 0.314 | 0.311 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.461 [0.369, 0.607] | 0.921 | 0.354 | 0.614 | 0.400 | 0.512 | 0.434 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.283 [0.200, 0.405] | 0.956 | 0.652 | 0.437 | 0.394 | 0.329 | 0.319 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.454 [0.329, 0.625] | 0.920 | 0.348 | 0.608 | 0.394 | 0.505 | 0.428 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.382 [0.257, 0.530] | 0.892 | 0.400 | 0.535 | 0.391 | 0.431 | 0.385 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.309 [0.244, 0.398] | 0.712 | 0.522 | 0.431 | 0.388 | 0.349 | 0.337 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.289 [0.221, 0.398] | 0.571 | 0.571 | 0.384 | 0.384 | 0.321 | 0.321 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.237 [0.173, 0.313] | 0.973 | 0.947 | 0.381 | 0.379 | 0.279 | 0.279 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.421 [0.318, 0.577] | 0.889 | 0.344 | 0.571 | 0.379 | 0.471 | 0.403 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.395 [0.304, 0.528] | 0.779 | 0.361 | 0.524 | 0.377 | 0.438 | 0.388 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.263 [0.207, 0.371] | 0.952 | 0.656 | 0.412 | 0.376 | 0.308 | 0.299 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.276 [0.176, 0.446] | 0.764 | 0.575 | 0.406 | 0.373 | 0.317 | 0.308 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.250 [0.185, 0.369] | 1.000 | 0.731 | 0.400 | 0.373 | 0.294 | 0.288 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.283 [0.227, 0.375] | 0.860 | 0.544 | 0.426 | 0.372 | 0.327 | 0.313 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.434 [0.339, 0.610] | 0.759 | 0.319 | 0.552 | 0.368 | 0.475 | 0.405 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.289 [0.175, 0.448] | 0.677 | 0.500 | 0.406 | 0.367 | 0.327 | 0.316 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.257 [0.207, 0.337] | 0.929 | 0.629 | 0.402 | 0.364 | 0.300 | 0.291 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 | 0.417 | 0.368 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 | 0.440 | 0.387 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.243 [0.173, 0.368] | 0.902 | 0.673 | 0.383 | 0.357 | 0.285 | 0.279 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.408 [0.332, 0.529] | 0.596 | 0.318 | 0.484 | 0.357 | 0.435 | 0.386 |
| gpt-6-astra · compound-realistic · low | 6 | 0.250 [0.203, 0.354] | 0.792 | 0.613 | 0.380 | 0.355 | 0.290 | 0.284 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.217 [0.162, 0.289] | 1.000 | 0.971 | 0.357 | 0.355 | 0.257 | 0.257 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.441 [0.369, 0.538] | 0.568 | 0.296 | 0.496 | 0.354 | 0.461 | 0.402 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.428 [0.336, 0.602] | 0.684 | 0.294 | 0.526 | 0.349 | 0.462 | 0.392 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.243 [0.179, 0.323] | 0.974 | 0.597 | 0.389 | 0.346 | 0.286 | 0.276 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.421 [0.322, 0.583] | 0.566 | 0.286 | 0.483 | 0.340 | 0.444 | 0.385 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.230 [0.146, 0.348] | 0.833 | 0.625 | 0.361 | 0.337 | 0.269 | 0.264 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.204 [0.143, 0.289] | 0.969 | 0.939 | 0.337 | 0.335 | 0.242 | 0.242 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 | 0.400 | 0.355 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.349 [0.267, 0.474] | 0.736 | 0.308 | 0.473 | 0.327 | 0.390 | 0.340 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.342 [0.283, 0.457] | 0.788 | 0.313 | 0.477 | 0.327 | 0.386 | 0.336 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 | 0.496 | 0.404 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.355 [0.257, 0.506] | 0.750 | 0.298 | 0.482 | 0.324 | 0.397 | 0.342 |
| gpt-6-astra · compound-realistic · high | 6 | 0.211 [0.150, 0.323] | 0.800 | 0.681 | 0.333 | 0.322 | 0.247 | 0.244 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.243 [0.149, 0.359] | 0.685 | 0.446 | 0.359 | 0.315 | 0.279 | 0.268 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.224 [0.146, 0.348] | 0.694 | 0.523 | 0.338 | 0.313 | 0.259 | 0.253 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.217 [0.148, 0.329] | 0.702 | 0.541 | 0.332 | 0.310 | 0.252 | 0.247 |
| claude-opus-5 · compound-realistic · low | 6 | 0.382 [0.276, 0.531] | 0.574 | 0.260 | 0.458 | 0.309 | 0.409 | 0.349 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.362 [0.281, 0.467] | 0.625 | 0.247 | 0.458 | 0.293 | 0.395 | 0.331 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.230 [0.153, 0.340] | 0.700 | 0.402 | 0.347 | 0.293 | 0.266 | 0.252 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.487 [0.376, 0.624] | 0.474 | 0.209 | 0.481 | 0.292 | 0.484 | 0.385 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.197 [0.144, 0.292] | 0.833 | 0.556 | 0.319 | 0.291 | 0.233 | 0.227 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.204 [0.149, 0.271] | 0.738 | 0.463 | 0.320 | 0.283 | 0.238 | 0.230 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.303 [0.200, 0.465] | 0.541 | 0.264 | 0.388 | 0.282 | 0.332 | 0.294 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.197 [0.145, 0.289] | 0.789 | 0.492 | 0.316 | 0.282 | 0.232 | 0.224 |
| claude-opus-5 · compound-realistic · high | 6 | 0.362 [0.284, 0.496] | 0.466 | 0.217 | 0.407 | 0.272 | 0.379 | 0.319 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 | 0.394 | 0.323 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.291 [0.212, 0.444] | 0.500 | 0.247 | 0.368 | 0.267 | 0.318 | 0.281 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.178 [0.138, 0.224] | 0.931 | 0.529 | 0.298 | 0.266 | 0.212 | 0.205 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.171 [0.126, 0.238] | 0.650 | 0.565 | 0.271 | 0.263 | 0.201 | 0.199 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.158 [0.097, 0.250] | 0.960 | 0.727 | 0.271 | 0.259 | 0.190 | 0.187 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.151 [0.093, 0.216] | 0.793 | 0.622 | 0.254 | 0.243 | 0.181 | 0.178 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.138 [0.099, 0.198] | 1.000 | 1.000 | 0.243 | 0.243 | 0.167 | 0.167 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.237 [0.186, 0.320] | 0.480 | 0.237 | 0.317 | 0.237 | 0.264 | 0.237 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.158 [0.102, 0.236] | 0.686 | 0.453 | 0.257 | 0.234 | 0.187 | 0.182 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.132 [0.074, 0.216] | 1.000 | 1.000 | 0.233 | 0.233 | 0.159 | 0.159 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.132 [0.096, 0.188] | 1.000 | 1.000 | 0.233 | 0.233 | 0.159 | 0.159 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.132 [0.072, 0.214] | 1.000 | 1.000 | 0.233 | 0.233 | 0.159 | 0.159 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.132 [0.086, 0.216] | 0.952 | 0.952 | 0.231 | 0.231 | 0.159 | 0.159 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.125 [0.073, 0.192] | 0.950 | 0.950 | 0.221 | 0.221 | 0.151 | 0.151 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.138 [0.084, 0.220] | 0.750 | 0.512 | 0.233 | 0.218 | 0.165 | 0.162 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.217 [0.156, 0.315] | 0.367 | 0.184 | 0.273 | 0.199 | 0.236 | 0.210 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.125 [0.080, 0.168] | 0.864 | 0.322 | 0.218 | 0.180 | 0.151 | 0.142 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.099 [0.031, 0.184] | 0.682 | 0.349 | 0.172 | 0.154 | 0.119 | 0.115 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.086 [0.047, 0.155] | 0.722 | 0.325 | 0.153 | 0.135 | 0.104 | 0.100 |

MRV-vs-CE on ΔF1': 8/21 pairs resolve positive (CI lower bound > 0). On ΔF2' (our evaluator): 7/21. Point estimates: 19/21 positive on ΔF1', 18/21 on ΔF2'.


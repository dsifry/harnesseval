# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators: **verified** = 42 goldens + 91 D-verified defects (133 total); **full** = 42 + 145 (187 total). recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also charges nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.340 [0.259, 0.474] | 0.700 | 0.700 | 0.458 | 0.458 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.326 [0.229, 0.467] | 0.671 | 0.671 | 0.439 | 0.439 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.306 [0.253, 0.396] | 0.846 | 0.733 | 0.449 | 0.431 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.278 [0.207, 0.368] | 0.952 | 0.889 | 0.430 | 0.423 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.479 [0.424, 0.567] | 0.908 | 0.377 | 0.627 | 0.422 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.285 [0.255, 0.330] | 0.911 | 0.788 | 0.434 | 0.418 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.417 [0.370, 0.511] | 0.645 | 0.420 | 0.506 | 0.418 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.299 [0.212, 0.437] | 0.956 | 0.652 | 0.455 | 0.410 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.486 [0.393, 0.628] | 0.921 | 0.354 | 0.636 | 0.409 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.479 [0.349, 0.644] | 0.920 | 0.348 | 0.630 | 0.404 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.326 [0.258, 0.429] | 0.712 | 0.522 | 0.448 | 0.402 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.403 [0.270, 0.564] | 0.892 | 0.400 | 0.555 | 0.401 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.306 [0.231, 0.425] | 0.571 | 0.571 | 0.398 | 0.398 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.250 [0.182, 0.327] | 0.973 | 0.947 | 0.398 | 0.396 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.278 [0.218, 0.396] | 0.952 | 0.656 | 0.430 | 0.390 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.444 [0.336, 0.622] | 0.889 | 0.344 | 0.593 | 0.388 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.264 [0.195, 0.391] | 1.000 | 0.731 | 0.418 | 0.388 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.417 [0.324, 0.551] | 0.779 | 0.361 | 0.543 | 0.387 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.292 [0.186, 0.467] | 0.764 | 0.575 | 0.422 | 0.387 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.299 [0.240, 0.400] | 0.860 | 0.544 | 0.443 | 0.386 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.306 [0.183, 0.468] | 0.677 | 0.500 | 0.421 | 0.379 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.271 [0.218, 0.356] | 0.929 | 0.629 | 0.419 | 0.379 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.458 [0.354, 0.656] | 0.759 | 0.319 | 0.571 | 0.376 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.257 [0.186, 0.389] | 0.902 | 0.673 | 0.400 | 0.372 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.229 [0.169, 0.311] | 1.000 | 0.971 | 0.373 | 0.371 |
| gpt-6-astra · compound-realistic · low | 6 | 0.264 [0.217, 0.372] | 0.792 | 0.613 | 0.396 | 0.369 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.431 [0.356, 0.551] | 0.596 | 0.318 | 0.500 | 0.366 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.465 [0.394, 0.569] | 0.568 | 0.296 | 0.511 | 0.362 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.257 [0.189, 0.356] | 0.974 | 0.597 | 0.407 | 0.359 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.451 [0.358, 0.622] | 0.684 | 0.294 | 0.544 | 0.356 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.215 [0.150, 0.313] | 0.969 | 0.939 | 0.352 | 0.350 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.243 [0.156, 0.382] | 0.833 | 0.625 | 0.376 | 0.350 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.444 [0.338, 0.614] | 0.566 | 0.286 | 0.498 | 0.348 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.361 [0.303, 0.479] | 0.788 | 0.313 | 0.495 | 0.335 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.368 [0.283, 0.500] | 0.736 | 0.308 | 0.491 | 0.335 |
| gpt-6-astra · compound-realistic · high | 6 | 0.222 [0.157, 0.340] | 0.800 | 0.681 | 0.348 | 0.335 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.375 [0.269, 0.549] | 0.750 | 0.298 | 0.500 | 0.332 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.257 [0.156, 0.392] | 0.685 | 0.446 | 0.374 | 0.326 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.236 [0.153, 0.358] | 0.694 | 0.523 | 0.352 | 0.325 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.229 [0.153, 0.363] | 0.702 | 0.541 | 0.346 | 0.322 |
| claude-opus-5 · compound-realistic · low | 6 | 0.403 [0.292, 0.553] | 0.574 | 0.260 | 0.473 | 0.316 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.243 [0.163, 0.366] | 0.700 | 0.402 | 0.361 | 0.303 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.208 [0.151, 0.314] | 0.833 | 0.556 | 0.333 | 0.303 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.382 [0.297, 0.500] | 0.625 | 0.247 | 0.474 | 0.300 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.514 [0.397, 0.640] | 0.474 | 0.209 | 0.493 | 0.297 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.215 [0.156, 0.294] | 0.738 | 0.463 | 0.333 | 0.294 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.208 [0.149, 0.311] | 0.789 | 0.492 | 0.330 | 0.293 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.319 [0.214, 0.479] | 0.541 | 0.264 | 0.402 | 0.289 |
| claude-opus-5 · compound-realistic · high | 6 | 0.382 [0.298, 0.526] | 0.466 | 0.217 | 0.420 | 0.277 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.188 [0.146, 0.245] | 0.931 | 0.529 | 0.312 | 0.277 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.181 [0.132, 0.256] | 0.650 | 0.565 | 0.283 | 0.274 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.303 [0.224, 0.444] | 0.500 | 0.247 | 0.377 | 0.272 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.167 [0.103, 0.268] | 0.960 | 0.727 | 0.284 | 0.271 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.146 [0.103, 0.216] | 1.000 | 1.000 | 0.255 | 0.255 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.160 [0.099, 0.236] | 0.793 | 0.622 | 0.266 | 0.254 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.139 [0.077, 0.233] | 1.000 | 1.000 | 0.244 | 0.244 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.139 [0.101, 0.206] | 1.000 | 1.000 | 0.244 | 0.244 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.139 [0.077, 0.233] | 1.000 | 1.000 | 0.244 | 0.244 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.167 [0.103, 0.255] | 0.686 | 0.453 | 0.268 | 0.244 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.250 [0.191, 0.344] | 0.480 | 0.237 | 0.329 | 0.243 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.139 [0.091, 0.234] | 0.952 | 0.952 | 0.242 | 0.242 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.132 [0.077, 0.204] | 0.950 | 0.950 | 0.232 | 0.232 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.146 [0.089, 0.236] | 0.750 | 0.512 | 0.244 | 0.227 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.229 [0.168, 0.327] | 0.367 | 0.184 | 0.282 | 0.204 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.132 [0.082, 0.181] | 0.864 | 0.322 | 0.229 | 0.187 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.104 [0.032, 0.200] | 0.682 | 0.349 | 0.181 | 0.160 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.090 [0.051, 0.163] | 0.722 | 0.325 | 0.160 | 0.141 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.318 [0.240, 0.440] | 0.700 | 0.700 | 0.438 | 0.438 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.305 [0.214, 0.433] | 0.671 | 0.671 | 0.420 | 0.420 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.286 [0.239, 0.361] | 0.846 | 0.733 | 0.427 | 0.411 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.448 [0.390, 0.552] | 0.908 | 0.377 | 0.600 | 0.409 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.390 [0.343, 0.484] | 0.645 | 0.420 | 0.486 | 0.404 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.260 [0.194, 0.336] | 0.952 | 0.889 | 0.408 | 0.402 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.266 [0.241, 0.299] | 0.911 | 0.788 | 0.412 | 0.398 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.455 [0.363, 0.607] | 0.921 | 0.354 | 0.609 | 0.398 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.448 [0.324, 0.624] | 0.920 | 0.348 | 0.603 | 0.392 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.279 [0.198, 0.400] | 0.956 | 0.652 | 0.432 | 0.391 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.377 [0.252, 0.525] | 0.892 | 0.400 | 0.530 | 0.388 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.305 [0.242, 0.394] | 0.712 | 0.522 | 0.427 | 0.385 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.286 [0.217, 0.398] | 0.571 | 0.571 | 0.381 | 0.381 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.416 [0.312, 0.578] | 0.889 | 0.344 | 0.566 | 0.376 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.390 [0.299, 0.528] | 0.779 | 0.361 | 0.519 | 0.375 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.234 [0.171, 0.313] | 0.973 | 0.947 | 0.377 | 0.375 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.260 [0.205, 0.370] | 0.952 | 0.656 | 0.408 | 0.372 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.273 [0.168, 0.441] | 0.764 | 0.575 | 0.402 | 0.370 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.279 [0.224, 0.371] | 0.860 | 0.544 | 0.422 | 0.369 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.247 [0.183, 0.365] | 1.000 | 0.731 | 0.396 | 0.369 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.429 [0.335, 0.604] | 0.759 | 0.319 | 0.548 | 0.366 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.286 [0.171, 0.442] | 0.677 | 0.500 | 0.402 | 0.364 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.253 [0.203, 0.336] | 0.929 | 0.629 | 0.398 | 0.361 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.403 [0.324, 0.528] | 0.596 | 0.318 | 0.481 | 0.355 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.240 [0.172, 0.375] | 0.902 | 0.673 | 0.379 | 0.354 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.435 [0.362, 0.537] | 0.568 | 0.296 | 0.493 | 0.353 |
| gpt-6-astra · compound-realistic · low | 6 | 0.247 [0.199, 0.354] | 0.792 | 0.613 | 0.376 | 0.352 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.214 [0.159, 0.286] | 1.000 | 0.971 | 0.353 | 0.351 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.422 [0.330, 0.604] | 0.684 | 0.294 | 0.522 | 0.347 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.240 [0.177, 0.318] | 0.974 | 0.597 | 0.385 | 0.343 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.416 [0.318, 0.582] | 0.566 | 0.286 | 0.479 | 0.339 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.227 [0.145, 0.347] | 0.833 | 0.625 | 0.357 | 0.333 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.201 [0.143, 0.282] | 0.969 | 0.939 | 0.333 | 0.332 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.344 [0.263, 0.469] | 0.736 | 0.308 | 0.469 | 0.325 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.338 [0.279, 0.458] | 0.788 | 0.313 | 0.473 | 0.325 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.351 [0.253, 0.495] | 0.750 | 0.298 | 0.478 | 0.322 |
| gpt-6-astra · compound-realistic · high | 6 | 0.208 [0.147, 0.327] | 0.800 | 0.681 | 0.330 | 0.318 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.240 [0.146, 0.351] | 0.685 | 0.446 | 0.356 | 0.312 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.221 [0.144, 0.346] | 0.694 | 0.523 | 0.335 | 0.311 |
| claude-opus-5 · compound-realistic · low | 6 | 0.377 [0.272, 0.529] | 0.574 | 0.260 | 0.455 | 0.308 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.214 [0.145, 0.333] | 0.702 | 0.541 | 0.328 | 0.307 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.357 [0.278, 0.464] | 0.625 | 0.247 | 0.455 | 0.292 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.481 [0.371, 0.622] | 0.474 | 0.209 | 0.477 | 0.291 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.227 [0.151, 0.339] | 0.700 | 0.402 | 0.343 | 0.290 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.195 [0.142, 0.289] | 0.833 | 0.556 | 0.316 | 0.288 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.201 [0.146, 0.269] | 0.738 | 0.463 | 0.316 | 0.281 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.299 [0.195, 0.469] | 0.541 | 0.264 | 0.385 | 0.280 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.195 [0.143, 0.280] | 0.789 | 0.492 | 0.312 | 0.279 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| claude-opus-5 · compound-realistic · high | 6 | 0.357 [0.276, 0.495] | 0.466 | 0.217 | 0.404 | 0.270 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.287 [0.208, 0.444] | 0.500 | 0.247 | 0.365 | 0.266 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.175 [0.136, 0.222] | 0.931 | 0.529 | 0.295 | 0.263 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.169 [0.124, 0.237] | 0.650 | 0.565 | 0.268 | 0.260 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.156 [0.095, 0.247] | 0.960 | 0.727 | 0.268 | 0.257 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.149 [0.091, 0.212] | 0.793 | 0.622 | 0.251 | 0.241 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.136 [0.098, 0.194] | 1.000 | 1.000 | 0.240 | 0.240 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.234 [0.185, 0.320] | 0.480 | 0.237 | 0.314 | 0.235 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.156 [0.100, 0.232] | 0.686 | 0.453 | 0.254 | 0.232 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.130 [0.073, 0.216] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.130 [0.095, 0.188] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.130 [0.072, 0.208] | 1.000 | 1.000 | 0.230 | 0.230 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.130 [0.084, 0.212] | 0.952 | 0.952 | 0.229 | 0.229 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.123 [0.071, 0.192] | 0.950 | 0.950 | 0.218 | 0.218 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.136 [0.083, 0.216] | 0.750 | 0.512 | 0.231 | 0.215 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.214 [0.153, 0.310] | 0.367 | 0.184 | 0.270 | 0.198 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.123 [0.081, 0.166] | 0.864 | 0.322 | 0.216 | 0.178 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.097 [0.030, 0.180] | 0.682 | 0.349 | 0.170 | 0.152 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.084 [0.046, 0.153] | 0.722 | 0.325 | 0.151 | 0.134 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.


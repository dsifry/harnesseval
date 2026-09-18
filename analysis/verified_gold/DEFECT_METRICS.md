# §10d — defect-level metrics (per-run matching at the individual-bug unit)

Denominators: **verified** = 42 goldens + 91 D-verified defects (133 total); **full** = 42 + 145 (187 total). recall = (golden TP + distinct defects hit) / denominator; adjP charges hallucinations, adjP' also charges nitpicks.

## variant: verified

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.345 [0.267, 0.474] | 0.700 | 0.700 | 0.462 | 0.462 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.331 [0.237, 0.467] | 0.671 | 0.671 | 0.443 | 0.443 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.310 [0.254, 0.396] | 0.846 | 0.733 | 0.454 | 0.436 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.282 [0.213, 0.368] | 0.952 | 0.889 | 0.435 | 0.428 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.486 [0.436, 0.567] | 0.908 | 0.377 | 0.633 | 0.425 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.289 [0.263, 0.330] | 0.911 | 0.788 | 0.439 | 0.423 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.423 [0.381, 0.511] | 0.645 | 0.420 | 0.511 | 0.421 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.303 [0.218, 0.437] | 0.956 | 0.652 | 0.460 | 0.413 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.493 [0.404, 0.628] | 0.921 | 0.354 | 0.642 | 0.412 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.486 [0.360, 0.644] | 0.920 | 0.348 | 0.636 | 0.406 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.331 [0.266, 0.429] | 0.712 | 0.522 | 0.452 | 0.405 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.408 [0.278, 0.564] | 0.892 | 0.400 | 0.560 | 0.404 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.310 [0.237, 0.425] | 0.571 | 0.571 | 0.402 | 0.402 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.254 [0.188, 0.327] | 0.973 | 0.947 | 0.402 | 0.400 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.282 [0.223, 0.396] | 0.952 | 0.656 | 0.435 | 0.394 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.268 [0.200, 0.391] | 1.000 | 0.731 | 0.422 | 0.392 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.296 [0.192, 0.467] | 0.764 | 0.575 | 0.426 | 0.391 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.451 [0.346, 0.622] | 0.889 | 0.344 | 0.598 | 0.390 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.423 [0.333, 0.551] | 0.779 | 0.361 | 0.548 | 0.390 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.303 [0.247, 0.400] | 0.860 | 0.544 | 0.448 | 0.389 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.310 [0.188, 0.468] | 0.677 | 0.500 | 0.425 | 0.383 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.275 [0.224, 0.356] | 0.929 | 0.629 | 0.424 | 0.382 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.465 [0.363, 0.656] | 0.759 | 0.319 | 0.576 | 0.378 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.261 [0.192, 0.389] | 0.902 | 0.673 | 0.404 | 0.376 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.232 [0.173, 0.311] | 1.000 | 0.971 | 0.377 | 0.375 |
| gpt-6-astra · compound-realistic · low | 6 | 0.268 [0.221, 0.372] | 0.792 | 0.613 | 0.400 | 0.373 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.437 [0.366, 0.551] | 0.596 | 0.318 | 0.504 | 0.368 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.472 [0.406, 0.569] | 0.568 | 0.296 | 0.515 | 0.364 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.261 [0.195, 0.356] | 0.974 | 0.597 | 0.411 | 0.363 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.458 [0.369, 0.622] | 0.684 | 0.294 | 0.549 | 0.358 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.218 [0.155, 0.313] | 0.969 | 0.939 | 0.356 | 0.354 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.246 [0.160, 0.382] | 0.833 | 0.625 | 0.380 | 0.354 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.451 [0.348, 0.614] | 0.566 | 0.286 | 0.502 | 0.350 |
| gpt-6-astra · compound-realistic · high | 6 | 0.225 [0.162, 0.340] | 0.800 | 0.681 | 0.352 | 0.339 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.366 [0.311, 0.479] | 0.788 | 0.313 | 0.500 | 0.338 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.373 [0.291, 0.500] | 0.736 | 0.308 | 0.495 | 0.338 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.380 [0.277, 0.549] | 0.750 | 0.298 | 0.505 | 0.334 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.261 [0.160, 0.392] | 0.685 | 0.446 | 0.378 | 0.329 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.239 [0.158, 0.358] | 0.694 | 0.523 | 0.356 | 0.329 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.232 [0.157, 0.363] | 0.702 | 0.541 | 0.349 | 0.325 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| claude-opus-5 · compound-realistic · low | 6 | 0.408 [0.301, 0.553] | 0.574 | 0.260 | 0.477 | 0.318 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.211 [0.154, 0.314] | 0.833 | 0.556 | 0.337 | 0.306 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.246 [0.167, 0.366] | 0.700 | 0.402 | 0.365 | 0.306 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.387 [0.306, 0.500] | 0.625 | 0.247 | 0.478 | 0.301 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.521 [0.409, 0.640] | 0.474 | 0.209 | 0.497 | 0.298 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.218 [0.161, 0.294] | 0.738 | 0.463 | 0.337 | 0.297 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.211 [0.153, 0.311] | 0.789 | 0.492 | 0.333 | 0.296 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.324 [0.220, 0.479] | 0.541 | 0.264 | 0.405 | 0.291 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.190 [0.150, 0.245] | 0.931 | 0.529 | 0.316 | 0.280 |
| claude-opus-5 · compound-realistic · high | 6 | 0.387 [0.306, 0.526] | 0.466 | 0.217 | 0.423 | 0.278 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.183 [0.136, 0.256] | 0.650 | 0.565 | 0.286 | 0.277 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.311 [0.234, 0.444] | 0.500 | 0.247 | 0.383 | 0.275 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.169 [0.106, 0.268] | 0.960 | 0.727 | 0.287 | 0.274 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.148 [0.105, 0.216] | 1.000 | 1.000 | 0.258 | 0.258 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.162 [0.102, 0.236] | 0.793 | 0.622 | 0.269 | 0.257 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.141 [0.079, 0.233] | 1.000 | 1.000 | 0.247 | 0.247 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.141 [0.104, 0.206] | 1.000 | 1.000 | 0.247 | 0.247 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.141 [0.079, 0.233] | 1.000 | 1.000 | 0.247 | 0.247 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.169 [0.106, 0.255] | 0.686 | 0.453 | 0.271 | 0.246 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.141 [0.093, 0.234] | 0.952 | 0.952 | 0.245 | 0.245 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.254 [0.197, 0.344] | 0.480 | 0.237 | 0.332 | 0.245 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.134 [0.079, 0.204] | 0.950 | 0.950 | 0.235 | 0.235 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.148 [0.091, 0.236] | 0.750 | 0.512 | 0.247 | 0.230 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.232 [0.172, 0.327] | 0.367 | 0.184 | 0.284 | 0.206 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.134 [0.082, 0.183] | 0.864 | 0.322 | 0.232 | 0.189 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.106 [0.033, 0.200] | 0.682 | 0.349 | 0.183 | 0.162 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.092 [0.051, 0.163] | 0.722 | 0.325 | 0.163 | 0.143 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

## variant: full

| cell | n PRs | recall [CI] | adjP | adjP' | F1 | F1' |
|---|---|---|---|---|---|---|
| claude-fable-5-1 · vanilla-engineered · high | 6 | 0.343 [0.266, 0.468] | 0.700 | 0.700 | 0.460 | 0.460 |
| claude-fable-5-1 · vanilla-engineered · medium | 6 | 0.329 [0.235, 0.462] | 0.671 | 0.671 | 0.441 | 0.441 |
| gpt-6-astra · metareview-realistic · high | 6 | 0.308 [0.252, 0.396] | 0.846 | 0.733 | 0.451 | 0.433 |
| gpt-6-astra · metareview-realistic · low | 6 | 0.280 [0.212, 0.368] | 0.952 | 0.889 | 0.432 | 0.426 |
| glm-5.3-vision-background · metareview-realistic · high | 6 | 0.483 [0.436, 0.560] | 0.908 | 0.377 | 0.630 | 0.423 |
| gpt-6-astra · metareview-realistic · medium | 6 | 0.287 [0.261, 0.330] | 0.911 | 0.788 | 0.436 | 0.421 |
| gpt-5.6-sol · compound-realistic · high | 6 | 0.420 [0.379, 0.505] | 0.645 | 0.420 | 0.508 | 0.420 |
| claude-opus-5 · vanilla-engineered · high | 6 | 0.301 [0.214, 0.436] | 0.956 | 0.652 | 0.457 | 0.411 |
| glm-5.3-flash-background · metareview-realistic · high | 6 | 0.490 [0.402, 0.627] | 0.921 | 0.354 | 0.639 | 0.411 |
| glm-5.3-vision-background · metareview-realistic · medium | 6 | 0.483 [0.360, 0.640] | 0.920 | 0.348 | 0.633 | 0.405 |
| gpt-5.6-sol · metareview-realistic · high | 6 | 0.329 [0.265, 0.427] | 0.712 | 0.522 | 0.450 | 0.403 |
| glm-5.3-flash-background · compound-realistic · high | 6 | 0.406 [0.276, 0.566] | 0.892 | 0.400 | 0.558 | 0.403 |
| claude-opus-5 · vanilla-engineered · medium | 6 | 0.308 [0.235, 0.425] | 0.571 | 0.571 | 0.400 | 0.400 |
| gpt-5.6-sol · vanilla-engineered · high | 6 | 0.252 [0.188, 0.327] | 0.973 | 0.947 | 0.400 | 0.398 |
| glm-5.3-flash-background · vanilla-engineered · high | 6 | 0.280 [0.222, 0.393] | 0.952 | 0.656 | 0.432 | 0.392 |
| glm-5.3-vision-background · vanilla-engineered · medium | 6 | 0.266 [0.200, 0.391] | 1.000 | 0.731 | 0.420 | 0.390 |
| glm-5.3-vision-background · compound-realistic · high | 6 | 0.448 [0.345, 0.620] | 0.889 | 0.344 | 0.595 | 0.389 |
| gpt-5.6-sol · metareview-realistic · low | 6 | 0.294 [0.187, 0.457] | 0.764 | 0.575 | 0.424 | 0.389 |
| claude-opus-5 · vanilla-engineered · low | 6 | 0.280 [0.228, 0.358] | 0.930 | 0.635 | 0.430 | 0.388 |
| glm-5.3-vision-background · metareview-realistic · low | 6 | 0.420 [0.332, 0.543] | 0.779 | 0.361 | 0.545 | 0.388 |
| claude-fable-5-1 · vanilla-engineered · low | 6 | 0.301 [0.245, 0.396] | 0.860 | 0.544 | 0.446 | 0.387 |
| gpt-5.6-sol · metareview-realistic · medium | 6 | 0.308 [0.190, 0.468] | 0.677 | 0.500 | 0.423 | 0.381 |
| glm-5.3-vision-background · compound-realistic · medium | 6 | 0.462 [0.363, 0.649] | 0.759 | 0.319 | 0.574 | 0.377 |
| gpt-6-astra · compound-realistic · medium | 6 | 0.259 [0.192, 0.380] | 0.902 | 0.673 | 0.402 | 0.374 |
| gpt-5.6-sol · vanilla-engineered · low | 6 | 0.231 [0.171, 0.311] | 1.000 | 0.971 | 0.375 | 0.373 |
| gpt-6-astra · compound-realistic · low | 6 | 0.266 [0.220, 0.370] | 0.792 | 0.613 | 0.398 | 0.371 |
| claude-opus-5 · metareview-realistic · medium | 6 | 0.434 [0.362, 0.543] | 0.596 | 0.318 | 0.502 | 0.367 |
| claude-fable-5-1 · metareview-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.833 | 0.357 | 0.513 | 0.364 |
| claude-opus-5 · metareview-realistic · low | 6 | 0.469 [0.404, 0.560] | 0.568 | 0.296 | 0.513 | 0.363 |
| glm-5.3-vision-background · vanilla-engineered · high | 6 | 0.259 [0.195, 0.352] | 0.974 | 0.597 | 0.409 | 0.361 |
| claude-fable-5-1 · metareview-realistic · medium | 1 | 0.407 [0.407, 0.407] | 0.647 | 0.324 | 0.500 | 0.361 |
| glm-5.3-flash-background · metareview-realistic · low | 6 | 0.455 [0.368, 0.622] | 0.684 | 0.294 | 0.546 | 0.357 |
| gpt-5.6-sol · vanilla-engineered · medium | 6 | 0.217 [0.155, 0.313] | 0.969 | 0.939 | 0.354 | 0.352 |
| glm-5.3-flash-background · vanilla-engineered · medium | 6 | 0.245 [0.158, 0.378] | 0.833 | 0.625 | 0.378 | 0.352 |
| claude-opus-5 · metareview-realistic · high | 6 | 0.448 [0.344, 0.603] | 0.566 | 0.286 | 0.500 | 0.349 |
| gpt-6-astra · compound-realistic · high | 6 | 0.224 [0.160, 0.347] | 0.800 | 0.681 | 0.350 | 0.337 |
| glm-5.3-flash-background · metareview-realistic · medium | 6 | 0.364 [0.307, 0.469] | 0.788 | 0.313 | 0.498 | 0.337 |
| glm-5.3-flash-background · compound-realistic · low | 6 | 0.371 [0.289, 0.495] | 0.736 | 0.308 | 0.493 | 0.337 |
| glm-5.3-flash-background · compound-realistic · medium | 6 | 0.378 [0.276, 0.544] | 0.750 | 0.298 | 0.502 | 0.333 |
| claude-fable-5-1 · metareview-realistic · low | 1 | 0.370 [0.370, 0.370] | 0.588 | 0.303 | 0.455 | 0.333 |
| gpt-5.6-sol · compound-realistic · medium | 6 | 0.259 [0.159, 0.388] | 0.685 | 0.446 | 0.376 | 0.327 |
| gpt-5.6-terra · metareview-realistic · high | 6 | 0.238 [0.158, 0.358] | 0.694 | 0.523 | 0.354 | 0.327 |
| claude-fable-5-1 · compound-realistic · medium | 1 | 0.481 [0.481, 0.481] | 0.565 | 0.245 | 0.520 | 0.325 |
| gpt-5.6-terra · metareview-realistic · medium | 6 | 0.231 [0.156, 0.363] | 0.702 | 0.541 | 0.347 | 0.324 |
| claude-opus-5 · compound-realistic · low | 6 | 0.406 [0.303, 0.553] | 0.574 | 0.260 | 0.475 | 0.317 |
| gpt-5.6-terra · compound-realistic · low | 6 | 0.210 [0.153, 0.311] | 0.833 | 0.556 | 0.335 | 0.305 |
| gpt-5.6-sol · compound-realistic · low | 6 | 0.245 [0.166, 0.363] | 0.700 | 0.402 | 0.363 | 0.304 |
| glm-5.3-vision-background · compound-realistic · low | 6 | 0.385 [0.305, 0.495] | 0.625 | 0.247 | 0.476 | 0.301 |
| claude-opus-5 · compound-realistic · medium | 6 | 0.517 [0.410, 0.633] | 0.474 | 0.209 | 0.495 | 0.298 |
| gpt-5.6-terra · compound-realistic · medium | 6 | 0.217 [0.160, 0.291] | 0.738 | 0.463 | 0.335 | 0.295 |
| glm-5.3-vision-background · vanilla-engineered · low | 6 | 0.210 [0.150, 0.313] | 0.789 | 0.492 | 0.331 | 0.294 |
| claude-sonnet-5 · metareview-realistic · high | 6 | 0.322 [0.219, 0.479] | 0.541 | 0.264 | 0.404 | 0.290 |
| glm-5.3-flash-background · vanilla-engineered · low | 6 | 0.189 [0.148, 0.245] | 0.931 | 0.529 | 0.314 | 0.278 |
| claude-opus-5 · compound-realistic · high | 6 | 0.385 [0.297, 0.517] | 0.466 | 0.217 | 0.421 | 0.278 |
| claude-fable-5-1 · compound-realistic · low | 2 | 0.311 [0.234, 0.444] | 0.500 | 0.247 | 0.383 | 0.275 |
| gpt-5.6-terra · metareview-realistic · low | 6 | 0.182 [0.134, 0.253] | 0.650 | 0.565 | 0.284 | 0.275 |
| claude-sonnet-5 · vanilla-engineered · high | 6 | 0.168 [0.105, 0.268] | 0.960 | 0.727 | 0.286 | 0.273 |
| claude-fable-5-1 · compound-realistic · high | 1 | 0.370 [0.370, 0.370] | 0.526 | 0.213 | 0.435 | 0.270 |
| gpt-5.6-terra · vanilla-engineered · high | 6 | 0.147 [0.105, 0.214] | 1.000 | 1.000 | 0.256 | 0.256 |
| claude-sonnet-5 · vanilla-engineered · medium | 6 | 0.161 [0.100, 0.236] | 0.793 | 0.622 | 0.267 | 0.256 |
| gpt-5.6-terra · vanilla-engineered · medium | 6 | 0.140 [0.079, 0.231] | 1.000 | 1.000 | 0.245 | 0.245 |
| gpt-6-astra · vanilla-engineered · low | 6 | 0.140 [0.103, 0.207] | 1.000 | 1.000 | 0.245 | 0.245 |
| gpt-6-astra · vanilla-engineered · high | 6 | 0.140 [0.079, 0.231] | 1.000 | 1.000 | 0.245 | 0.245 |
| gpt-5.6-terra · compound-realistic · high | 6 | 0.168 [0.104, 0.252] | 0.686 | 0.453 | 0.270 | 0.245 |
| claude-sonnet-5 · metareview-realistic · medium | 6 | 0.252 [0.196, 0.341] | 0.480 | 0.237 | 0.330 | 0.244 |
| gpt-6-astra · vanilla-engineered · medium | 6 | 0.140 [0.093, 0.232] | 0.952 | 0.952 | 0.244 | 0.244 |
| gpt-5.6-terra · vanilla-engineered · low | 6 | 0.133 [0.079, 0.202] | 0.950 | 0.950 | 0.233 | 0.233 |
| claude-sonnet-5 · vanilla-engineered · low | 6 | 0.147 [0.090, 0.236] | 0.750 | 0.512 | 0.246 | 0.228 |
| claude-sonnet-5 · metareview-realistic · low | 6 | 0.231 [0.167, 0.327] | 0.367 | 0.184 | 0.283 | 0.205 |
| claude-sonnet-5 · compound-realistic · medium | 6 | 0.133 [0.081, 0.184] | 0.864 | 0.322 | 0.230 | 0.188 |
| claude-sonnet-5 · compound-realistic · high | 6 | 0.105 [0.033, 0.198] | 0.682 | 0.349 | 0.182 | 0.161 |
| claude-sonnet-5 · compound-realistic · low | 6 | 0.091 [0.051, 0.160] | 0.722 | 0.325 | 0.161 | 0.142 |

MRV-vs-CE: 7/21 pairs resolve positive on ΔF1'.

